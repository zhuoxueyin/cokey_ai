import { useCallback, useEffect, useRef, useState } from 'react'
import { Button, Input, Slider, Tooltip, message } from 'antd'
import {
  HighlightOutlined,
  BorderOutlined,
  RadiusSettingOutlined,
  ClearOutlined,
  FontSizeOutlined,
  UndoOutlined,
  RedoOutlined,
  DeleteOutlined,
  SaveOutlined,
  CloseOutlined,
} from '@ant-design/icons'
import type { ImageMarkLayer, ImageMarkTool } from '@/types/imageMark'
import { DEFAULT_MARK_COLOR, DEFAULT_MARK_STROKE, MARK_COLOR_PRESETS } from '@/types/imageMark'
import {
  computeImageLayout,
  createLayerId,
  exportMergedMarkImage,
  loadImageElement,
  pointerToNormOnCanvas,
  renderMarkLayers,
  type ImageLayout,
} from '@/utils/imageMarkEngine'

interface ResourceImageMarkEditorProps {
  imageUrl: string
  initialLayers?: ImageMarkLayer[]
  initialTool?: ImageMarkTool
  onCancel: () => void
  onSave: (layers: ImageMarkLayer[], blob: Blob) => Promise<void>
}

const TOOL_ITEMS: { key: ImageMarkTool; label: string; icon: React.ReactNode }[] = [
  { key: 'brush', label: '画笔', icon: <HighlightOutlined /> },
  { key: 'ellipse', label: '椭圆', icon: <RadiusSettingOutlined /> },
  { key: 'rect', label: '方形', icon: <BorderOutlined /> },
  { key: 'eraser', label: '擦除', icon: <ClearOutlined /> },
  { key: 'text', label: '文字', icon: <FontSizeOutlined /> },
]

function cloneLayers(layers: ImageMarkLayer[]): ImageMarkLayer[] {
  return layers.map((l) => ({ ...l, points: l.points ? l.points.map((p) => ({ ...p })) : undefined }))
}

export default function ResourceImageMarkEditor({
  imageUrl,
  initialLayers = [],
  initialTool = 'brush',
  onCancel,
  onSave,
}: ResourceImageMarkEditorProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const imageRef = useRef<HTMLImageElement>(null)

  const [tool, setTool] = useState<ImageMarkTool>(initialTool)
  const [color, setColor] = useState(DEFAULT_MARK_COLOR)
  const [strokeWidth, setStrokeWidth] = useState(DEFAULT_MARK_STROKE)
  const [layers, setLayers] = useState<ImageMarkLayer[]>(() => cloneLayers(initialLayers))
  const [history, setHistory] = useState<ImageMarkLayer[][]>(() => [cloneLayers(initialLayers)])
  const [historyIndex, setHistoryIndex] = useState(0)
  const [layout, setLayout] = useState<ImageLayout>({
    width: 0,
    height: 0,
    offsetX: 0,
    offsetY: 0,
    naturalW: 0,
    naturalH: 0,
  })
  const [draft, setDraft] = useState<ImageMarkLayer | null>(null)
  const [textInput, setTextInput] = useState<{ x: number; y: number; value: string } | null>(null)
  const [saving, setSaving] = useState(false)
  const drawingRef = useRef(false)
  const startNormRef = useRef<{ x: number; y: number } | null>(null)
  const historyIndexRef = useRef(0)

  const pushHistory = useCallback((next: ImageMarkLayer[]) => {
    setHistory((prev) => {
      const idx = historyIndexRef.current
      const trimmed = prev.slice(0, idx + 1)
      const merged = [...trimmed, cloneLayers(next)]
      historyIndexRef.current = merged.length - 1
      setHistoryIndex(merged.length - 1)
      return merged
    })
    setLayers(cloneLayers(next))
  }, [])

  const syncLayout = useCallback(() => {
    const container = containerRef.current
    const img = imageRef.current
    if (!container || !img?.naturalWidth) return
    setLayout(
      computeImageLayout(container.clientWidth, container.clientHeight, img.naturalWidth, img.naturalHeight),
    )
  }, [])

  useEffect(() => {
    syncLayout()
    const ro = new ResizeObserver(syncLayout)
    if (containerRef.current) ro.observe(containerRef.current)
    return () => ro.disconnect()
  }, [syncLayout])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas || !layout.naturalW) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    const all = draft ? [...layers, draft] : layers
    renderMarkLayers(ctx, all, canvas.width, canvas.height)
  }, [layers, draft, layout])

  const getNormPoint = (clientX: number, clientY: number, clamp = true) => {
    const canvas = canvasRef.current
    if (!canvas) return null
    return pointerToNormOnCanvas(clientX, clientY, canvas, clamp)
  }

  const handlePointerDown = (e: React.PointerEvent) => {
    e.stopPropagation()
    e.preventDefault()
    const point = getNormPoint(e.clientX, e.clientY, true)
    if (!point) return

    if (tool === 'text') {
      setTextInput({ x: point.x, y: point.y, value: '' })
      return
    }

    drawingRef.current = true
    startNormRef.current = point
    ;(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId)

    if (tool === 'brush' || tool === 'eraser') {
      setDraft({
        id: createLayerId(),
        type: tool === 'eraser' ? 'eraser' : 'path',
        color: tool === 'eraser' ? '#000' : color,
        strokeWidth: tool === 'eraser' ? Math.max(strokeWidth, 8) : strokeWidth,
        points: [point],
      })
    } else if (tool === 'ellipse') {
      setDraft({
        id: createLayerId(),
        type: 'ellipse',
        color,
        strokeWidth,
        cx: point.x,
        cy: point.y,
        rx: 0,
        ry: 0,
      })
    } else if (tool === 'rect') {
      setDraft({
        id: createLayerId(),
        type: 'rect',
        color,
        strokeWidth,
        x: point.x,
        y: point.y,
        w: 0,
        h: 0,
      })
    }
  }

  const handlePointerMove = (e: React.PointerEvent) => {
    if (!drawingRef.current || !draft) return
    e.stopPropagation()
    const point = getNormPoint(e.clientX, e.clientY, true)
    if (!point) return

    if (draft.type === 'path' || draft.type === 'eraser') {
      setDraft((d) => {
        if (!d?.points) return d
        const last = d.points[d.points.length - 1]
        if (Math.hypot(last.x - point.x, last.y - point.y) < 0.002) return d
        return { ...d, points: [...d.points, point] }
      })
    } else if (draft.type === 'ellipse' && startNormRef.current) {
      const sx = startNormRef.current.x
      const sy = startNormRef.current.y
      setDraft((d) =>
        d
          ? {
              ...d,
              cx: (sx + point.x) / 2,
              cy: (sy + point.y) / 2,
              rx: Math.abs(point.x - sx) / 2,
              ry: Math.abs(point.y - sy) / 2,
            }
          : d,
      )
    } else if (draft.type === 'rect' && startNormRef.current) {
      const sx = startNormRef.current.x
      const sy = startNormRef.current.y
      setDraft((d) =>
        d
          ? {
              ...d,
              x: Math.min(sx, point.x),
              y: Math.min(sy, point.y),
              w: Math.abs(point.x - sx),
              h: Math.abs(point.y - sy),
            }
          : d,
      )
    }
  }

  const finishDrawing = () => {
    if (!drawingRef.current || !draft) return
    drawingRef.current = false
    startNormRef.current = null
    const valid =
      (draft.type === 'path' && (draft.points?.length || 0) > 1) ||
      (draft.type === 'eraser' && (draft.points?.length || 0) > 1) ||
      (draft.type === 'ellipse' && (draft.rx || 0) > 0.005 && (draft.ry || 0) > 0.005) ||
      (draft.type === 'rect' && (draft.w || 0) > 0.005 && (draft.h || 0) > 0.005)
    if (valid) pushHistory([...layers, draft])
    setDraft(null)
  }

  const handlePointerUp = (e: React.PointerEvent) => {
    e.stopPropagation()
    finishDrawing()
  }

  const handleUndo = () => {
    if (historyIndex <= 0) return
    const nextIndex = historyIndex - 1
    historyIndexRef.current = nextIndex
    setHistoryIndex(nextIndex)
    setLayers(cloneLayers(history[nextIndex]))
    setDraft(null)
  }

  const handleRedo = () => {
    if (historyIndex >= history.length - 1) return
    const nextIndex = historyIndex + 1
    historyIndexRef.current = nextIndex
    setHistoryIndex(nextIndex)
    setLayers(cloneLayers(history[nextIndex]))
    setDraft(null)
  }

  const handleClear = () => {
    if (layers.length === 0) return
    pushHistory([])
  }

  const confirmText = () => {
    if (!textInput?.value.trim()) {
      setTextInput(null)
      return
    }
    pushHistory([
      ...layers,
      {
        id: createLayerId(),
        type: 'text',
        color,
        strokeWidth,
        x: textInput.x,
        y: textInput.y,
        text: textInput.value.trim(),
        fontSize: 18 + strokeWidth * 2,
      },
    ])
    setTextInput(null)
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      const blob = await exportMergedMarkImage(imageUrl, layers)
      await onSave(layers, blob)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '保存失败'
      message.error(msg)
    } finally {
      setSaving(false)
    }
  }

  useEffect(() => {
    loadImageElement(imageUrl).catch(() => message.warning('图片加载可能受限，保存时若失败请更换 CDN 资源'))
  }, [imageUrl])

  return (
    <div className="canvas-resource-mark nodrag nopan canvas-resource-mark-editor" onMouseDown={(e) => e.stopPropagation()}>
      <div className="canvas-resource-mark__toolbar">
        <div className="canvas-resource-mark__tools">
          {TOOL_ITEMS.map((item) => (
            <Tooltip key={item.key} title={item.label}>
              <button
                type="button"
                className={`canvas-resource-mark__tool${tool === item.key ? ' canvas-resource-mark__tool--active' : ''}`}
                onClick={() => {
                  setTool(item.key)
                  setTextInput(null)
                }}
              >
                {item.icon}
              </button>
            </Tooltip>
          ))}
        </div>
        <div className="canvas-resource-mark__divider" />
        <div className="canvas-resource-mark__colors">
          {MARK_COLOR_PRESETS.map((c) => (
            <button
              key={c}
              type="button"
              className={`canvas-resource-mark__color${color === c ? ' canvas-resource-mark__color--active' : ''}`}
              style={{ background: c, borderColor: c === '#ffffff' ? '#666' : c }}
              onClick={() => setColor(c)}
              aria-label={`颜色 ${c}`}
            />
          ))}
        </div>
        <div className="canvas-resource-mark__stroke">
          <Slider min={1} max={16} value={strokeWidth} onChange={setStrokeWidth} style={{ width: 72 }} />
        </div>
        <div className="canvas-resource-mark__divider" />
        <Tooltip title="撤销">
          <button type="button" className="canvas-resource-mark__tool" disabled={historyIndex <= 0} onClick={handleUndo}>
            <UndoOutlined />
          </button>
        </Tooltip>
        <Tooltip title="重做">
          <button
            type="button"
            className="canvas-resource-mark__tool"
            disabled={historyIndex >= history.length - 1}
            onClick={handleRedo}
          >
            <RedoOutlined />
          </button>
        </Tooltip>
        <Tooltip title="清空标记">
          <button type="button" className="canvas-resource-mark__tool" disabled={layers.length === 0} onClick={handleClear}>
            <DeleteOutlined />
          </button>
        </Tooltip>
        <div className="canvas-resource-mark__actions">
          <Button size="small" icon={<CloseOutlined />} onClick={onCancel}>
            取消
          </Button>
          <Button size="small" type="primary" icon={<SaveOutlined />} loading={saving} onClick={() => void handleSave()}>
            保存
          </Button>
        </div>
      </div>

      <div ref={containerRef} className="canvas-resource-mark__stage">
        <img
          ref={imageRef}
          src={imageUrl}
          alt=""
          className="canvas-resource-mark__image"
          crossOrigin="anonymous"
          onLoad={syncLayout}
          draggable={false}
        />
        {layout.width > 0 && (
          <canvas
            ref={canvasRef}
            className="canvas-resource-mark__canvas"
            width={layout.naturalW}
            height={layout.naturalH}
            style={{
              left: layout.offsetX,
              top: layout.offsetY,
              width: layout.width,
              height: layout.height,
            }}
            onPointerDown={handlePointerDown}
            onPointerMove={handlePointerMove}
            onPointerUp={handlePointerUp}
            onPointerLeave={handlePointerUp}
          />
        )}
        {textInput && layout.width > 0 && (
          <div
            className="canvas-resource-mark__text-input nodrag nopan"
            style={{
              left: layout.offsetX + textInput.x * layout.width,
              top: layout.offsetY + textInput.y * layout.height,
            }}
            onMouseDown={(e) => e.stopPropagation()}
          >
            <Input
              autoFocus
              size="small"
              value={textInput.value}
              placeholder="输入文字"
              onChange={(e) => setTextInput({ ...textInput, value: e.target.value })}
              onPressEnter={confirmText}
              onBlur={confirmText}
            />
          </div>
        )}
      </div>
    </div>
  )
}
