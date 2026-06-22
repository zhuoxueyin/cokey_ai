import { useEffect, useRef, useState } from 'react'
import { Slider } from 'antd'
import { useReactFlow, useStore, type Node } from '@xyflow/react'
import type { CanvasNode, CanvasNodeConfig } from '@/types/canvas'
import {
  clampToTwoLines,
  FONT_OPTIONS,
  resolveTitleContent,
  resolveTitleFontSize,
  TITLE_FONT_SIZE_MAX,
  TITLE_FONT_SIZE_MIN,
  titleTextStyle,
} from '@/utils/titleNodeStyles'

interface TitleNodeEditPanelProps {
  nodeId: string | null
  visible: boolean
  node: CanvasNode | null
  onUpdateConfig: (nodeId: string, patch: Partial<CanvasNodeConfig>) => void | Promise<void>
  onEditContent: (nodeId: string, content: string, options?: { immediate?: boolean }) => void
}

const PANEL_GAP = 8
const PANEL_MIN = 280
const PANEL_MAX = 520

type PanelLayout = { x: number; y: number; w: number }

function measureAbovePanel(
  nodeId: string,
  getNode?: (id: string) => Node | undefined,
  flowToScreenPosition?: (pos: { x: number; y: number }) => { x: number; y: number },
): PanelLayout | null {
  const nodeEl = document.querySelector(`.react-flow__node[data-id="${nodeId}"]`) as HTMLElement | null
  const workspace = nodeEl?.closest('.canvas-workspace') as HTMLElement | null

  if (nodeEl && workspace) {
    const nodeRect = nodeEl.getBoundingClientRect()
    const wsRect = workspace.getBoundingClientRect()
    const panelW = Math.min(PANEL_MAX, Math.max(PANEL_MIN, nodeRect.width))
    return {
      x: nodeRect.left + nodeRect.width / 2 - wsRect.left,
      y: nodeRect.top - wsRect.top - PANEL_GAP,
      w: panelW,
    }
  }

  if (!getNode || !flowToScreenPosition) return null
  const node = getNode(nodeId)
  if (!node) return null
  const nodeWidth = Number(node.width ?? node.measured?.width ?? 360)
  const panelW = Math.min(PANEL_MAX, Math.max(PANEL_MIN, nodeWidth))
  const p = flowToScreenPosition({ x: node.position.x + nodeWidth / 2, y: node.position.y })
  return { x: p.x, y: p.y - PANEL_GAP, w: panelW }
}

export default function TitleNodeEditPanel({
  nodeId,
  visible,
  node,
  onUpdateConfig,
  onEditContent,
}: TitleNodeEditPanelProps) {
  const { flowToScreenPosition, getNode } = useReactFlow()
  const transform = useStore((s) => s.transform)
  const [layout, setLayout] = useState<PanelLayout | null>(null)

  const config = node?.config ?? {}
  const fontFamily = config.font_family || 'sans'
  const color = config.color || '#ffffff'
  const fontSize = resolveTitleFontSize(config)
  const remoteContent = resolveTitleContent(config)
  const [content, setContent] = useState(remoteContent)
  const contentRef = useRef(content)
  contentRef.current = content

  useEffect(() => {
    setContent(remoteContent)
  }, [nodeId, remoteContent])

  useEffect(() => {
    if (!visible || !nodeId) {
      setLayout(null)
      return
    }

    const update = () => {
      const next = measureAbovePanel(nodeId, getNode, flowToScreenPosition)
      if (next) setLayout(next)
    }

    update()
    const raf = requestAnimationFrame(update)
    window.addEventListener('resize', update)
    return () => {
      cancelAnimationFrame(raf)
      window.removeEventListener('resize', update)
    }
  }, [visible, nodeId, getNode, flowToScreenPosition, transform])

  useEffect(() => {
    if (!visible || !nodeId) return
    return () => {
      onEditContent(nodeId, contentRef.current, { immediate: true })
    }
  }, [visible, nodeId, onEditContent])

  if (!visible || !nodeId || !node || !layout) return null

  const patchConfig = (patch: Partial<CanvasNodeConfig>) => {
    void onUpdateConfig(nodeId, patch)
  }

  const handleContentChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const next = clampToTwoLines(e.target.value)
    setContent(next)
    onEditContent(nodeId, next)
  }

  const handleContentBlur = () => {
    onEditContent(nodeId, content, { immediate: true })
  }

  const handleContentKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && content.split('\n').length >= 2) {
      e.preventDefault()
    }
  }

  const previewStyle = titleTextStyle({ ...config, content })

  return (
    <div
      className="canvas-title-node-edit-panel nodrag nopan"
      style={{ left: layout.x, top: layout.y, width: layout.w }}
      onMouseDown={(e) => e.stopPropagation()}
      onPointerDown={(e) => e.stopPropagation()}
      onClick={(e) => e.stopPropagation()}
      onDoubleClick={(e) => e.stopPropagation()}
    >
      <div className="canvas-title-node__toolbar">
        <div className="canvas-title-node__size-row">
          <span className="canvas-title-node__size-label">小</span>
          <Slider
            className="canvas-title-node__size-slider"
            min={TITLE_FONT_SIZE_MIN}
            max={TITLE_FONT_SIZE_MAX}
            step={1}
            value={fontSize}
            tooltip={{ formatter: (v) => `${v}px` }}
            onChange={(value) => patchConfig({ title_font_size: value })}
          />
          <span className="canvas-title-node__size-label">大</span>
          <span className="canvas-title-node__size-value">{fontSize}px</span>
        </div>
        <div className="canvas-title-node__style-row">
          <select
            className="canvas-title-node__font-select"
            value={fontFamily}
            onChange={(e) =>
              patchConfig({ font_family: e.target.value as CanvasNodeConfig['font_family'] })
            }
          >
            {FONT_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
          <label className="canvas-title-node__color-wrap">
            <input
              type="color"
              className="canvas-title-node__color-input"
              value={color}
              onChange={(e) => patchConfig({ color: e.target.value })}
            />
            <span className="canvas-title-node__color-label">颜色</span>
          </label>
        </div>
      </div>
      <textarea
        className="canvas-title-node__editor"
        value={content}
        onChange={handleContentChange}
        onBlur={handleContentBlur}
        onKeyDown={handleContentKeyDown}
        placeholder="输入标题（最多 2 行）"
        rows={2}
        style={previewStyle}
      />
      <div className="canvas-title-node-edit-panel__hint">点击空白取消选中时会自动保存</div>
    </div>
  )
}
