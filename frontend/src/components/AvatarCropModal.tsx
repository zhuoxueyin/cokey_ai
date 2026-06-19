import { useCallback, useEffect, useRef, useState } from 'react'
import { Modal, Slider, Button } from 'antd'

const OUTPUT_SIZE = 256
const VIEWPORT = 240

interface AvatarCropModalProps {
  open: boolean
  imageSrc: string | null
  onCancel: () => void
  onConfirm: (file: File) => void
}

export default function AvatarCropModal({ open, imageSrc, onCancel, onConfirm }: AvatarCropModalProps) {
  const [scale, setScale] = useState(1)
  const [offset, setOffset] = useState({ x: 0, y: 0 })
  const [imgSize, setImgSize] = useState({ w: 0, h: 0 })
  const [dragging, setDragging] = useState(false)
  const dragStart = useRef({ x: 0, y: 0, ox: 0, oy: 0 })
  const viewportRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open || !imageSrc) return
    setScale(1)
    setOffset({ x: 0, y: 0 })
    const img = new Image()
    img.crossOrigin = 'anonymous'
    img.onload = () => {
      setImgSize({ w: img.naturalWidth, h: img.naturalHeight })
      const cover = Math.max(VIEWPORT / img.naturalWidth, VIEWPORT / img.naturalHeight)
      setScale(cover)
    }
    img.src = imageSrc
  }, [open, imageSrc])

  const clampOffset = useCallback(
    (ox: number, oy: number, s: number) => {
      if (!imgSize.w || !imgSize.h) return { x: ox, y: oy }
      const dw = imgSize.w * s
      const dh = imgSize.h * s
      const maxX = Math.max(0, (dw - VIEWPORT) / 2)
      const maxY = Math.max(0, (dh - VIEWPORT) / 2)
      return {
        x: Math.min(maxX, Math.max(-maxX, ox)),
        y: Math.min(maxY, Math.max(-maxY, oy)),
      }
    },
    [imgSize],
  )

  const handlePointerDown = (e: React.PointerEvent) => {
    setDragging(true)
    dragStart.current = { x: e.clientX, y: e.clientY, ox: offset.x, oy: offset.y }
    ;(e.target as HTMLElement).setPointerCapture?.(e.pointerId)
  }

  const handlePointerMove = (e: React.PointerEvent) => {
    if (!dragging) return
    const dx = e.clientX - dragStart.current.x
    const dy = e.clientY - dragStart.current.y
    setOffset(clampOffset(dragStart.current.ox + dx, dragStart.current.oy + dy, scale))
  }

  const handlePointerUp = () => setDragging(false)

  const handleScaleChange = (v: number) => {
    setScale(v)
    setOffset((prev) => clampOffset(prev.x, prev.y, v))
  }

  const handleConfirm = async () => {
    if (!imageSrc || !imgSize.w) return
    const img = new Image()
    img.crossOrigin = 'anonymous'
    await new Promise<void>((resolve, reject) => {
      img.onload = () => resolve()
      img.onerror = reject
      img.src = imageSrc
    })

    const canvas = document.createElement('canvas')
    canvas.width = OUTPUT_SIZE
    canvas.height = OUTPUT_SIZE
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const dw = imgSize.w * scale
    const dh = imgSize.h * scale
    const sx = VIEWPORT / 2 + offset.x - dw / 2
    const sy = VIEWPORT / 2 + offset.y - dh / 2
    const ratio = OUTPUT_SIZE / VIEWPORT

    ctx.fillStyle = '#fff'
    ctx.fillRect(0, 0, OUTPUT_SIZE, OUTPUT_SIZE)
    ctx.drawImage(img, sx * ratio, sy * ratio, dw * ratio, dh * ratio)

    try {
      canvas.toBlob(
        (blob) => {
          if (!blob) return
          onConfirm(new File([blob], 'avatar.png', { type: 'image/png' }))
        },
        'image/png',
        0.92,
      )
    } catch {
      // CDN 图片可能因跨域无法导出，提示重新选择本地图片
      onCancel()
    }
  }

  const dw = imgSize.w * scale
  const dh = imgSize.h * scale
  const left = VIEWPORT / 2 + offset.x - dw / 2
  const top = VIEWPORT / 2 + offset.y - dh / 2

  return (
    <Modal
      title="调整头像可见区域"
      open={open}
      onCancel={onCancel}
      footer={[
        <Button key="cancel" onClick={onCancel}>
          取消
        </Button>,
        <Button key="ok" type="primary" onClick={handleConfirm}>
          确认
        </Button>,
      ]}
      width={360}
      destroyOnClose
    >
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16 }}>
        <div
          ref={viewportRef}
          style={{
            width: VIEWPORT,
            height: VIEWPORT,
            borderRadius: '50%',
            overflow: 'hidden',
            position: 'relative',
            background: '#f0f0f0',
            border: '2px solid #e8e8e8',
            cursor: dragging ? 'grabbing' : 'grab',
            touchAction: 'none',
          }}
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onPointerLeave={handlePointerUp}
        >
          {imageSrc && imgSize.w > 0 && (
            <img
              src={imageSrc}
              alt="crop"
              draggable={false}
              style={{
                position: 'absolute',
                left,
                top,
                width: dw,
                height: dh,
                maxWidth: 'none',
                userSelect: 'none',
                pointerEvents: 'none',
              }}
            />
          )}
        </div>
        <div style={{ width: '100%' }}>
          <div style={{ fontSize: 12, color: '#666', marginBottom: 4 }}>缩放</div>
          <Slider
            min={
              imgSize.w && imgSize.h
                ? Math.max(0.1, Math.min(VIEWPORT / imgSize.w, VIEWPORT / imgSize.h))
                : 0.1
            }
            max={
              imgSize.w && imgSize.h
                ? Math.max(2, Math.max(VIEWPORT / imgSize.w, VIEWPORT / imgSize.h) * 3)
                : 3
            }
            step={0.01}
            value={scale}
            onChange={handleScaleChange}
            disabled={!imgSize.w}
          />
        </div>
        <div style={{ fontSize: 11, color: '#999' }}>拖动图片调整位置，滚轮区域可缩放</div>
      </div>
    </Modal>
  )
}
