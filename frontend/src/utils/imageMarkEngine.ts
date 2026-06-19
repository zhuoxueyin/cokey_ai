import type { ImageMarkLayer } from '@/types/imageMark'

export interface ImageLayout {
  width: number
  height: number
  offsetX: number
  offsetY: number
  naturalW: number
  naturalH: number
}

export function clamp01(v: number): number {
  return Math.min(1, Math.max(0, v))
}

export function computeImageLayout(
  containerW: number,
  containerH: number,
  naturalW: number,
  naturalH: number,
): ImageLayout {
  if (!naturalW || !naturalH || !containerW || !containerH) {
    return { width: 0, height: 0, offsetX: 0, offsetY: 0, naturalW, naturalH }
  }
  const scale = Math.min(containerW / naturalW, containerH / naturalH)
  const width = naturalW * scale
  const height = naturalH * scale
  return {
    width,
    height,
    offsetX: (containerW - width) / 2,
    offsetY: (containerH - height) / 2,
    naturalW,
    naturalH,
  }
}

export function clientToNorm(
  clientX: number,
  clientY: number,
  containerRect: DOMRect,
  layout: ImageLayout,
): { x: number; y: number } | null {
  if (!layout.width || !layout.height) return null
  const x = (clientX - containerRect.left - layout.offsetX) / layout.width
  const y = (clientY - containerRect.top - layout.offsetY) / layout.height
  if (x < 0 || y < 0 || x > 1 || y > 1) return null
  return { x: clamp01(x), y: clamp01(y) }
}

/** 将屏幕坐标映射到 canvas 归一化坐标（自动匹配 CSS 缩放，避免笔迹错位） */
export function pointerToNormOnCanvas(
  clientX: number,
  clientY: number,
  canvas: HTMLCanvasElement,
  clamp = true,
): { x: number; y: number } | null {
  const rect = canvas.getBoundingClientRect()
  if (!rect.width || !rect.height) return null
  const x = (clientX - rect.left) / rect.width
  const y = (clientY - rect.top) / rect.height
  if (!clamp && (x < 0 || y < 0 || x > 1 || y > 1)) return null
  return { x: clamp01(x), y: clamp01(y) }
}

function drawPath(
  ctx: CanvasRenderingContext2D,
  layer: ImageMarkLayer,
  width: number,
  height: number,
  composite?: GlobalCompositeOperation,
) {
  if (!layer.points || layer.points.length < 2) return
  ctx.save()
  if (composite) ctx.globalCompositeOperation = composite
  ctx.strokeStyle = composite ? 'rgba(0,0,0,1)' : layer.color
  ctx.lineWidth = layer.strokeWidth * (width / 800)
  ctx.lineCap = 'round'
  ctx.lineJoin = 'round'
  ctx.beginPath()
  layer.points.forEach((p, i) => {
    const px = p.x * width
    const py = p.y * height
    if (i === 0) ctx.moveTo(px, py)
    else ctx.lineTo(px, py)
  })
  ctx.stroke()
  ctx.restore()
}

export function renderMarkLayers(
  ctx: CanvasRenderingContext2D,
  layers: ImageMarkLayer[],
  width: number,
  height: number,
) {
  const scale = width / 800
  for (const layer of layers) {
    if (layer.type === 'eraser') {
      drawPath(ctx, layer, width, height, 'destination-out')
      continue
    }
    ctx.save()
    ctx.strokeStyle = layer.color
    ctx.fillStyle = layer.color
    ctx.lineWidth = layer.strokeWidth * scale
    ctx.lineCap = 'round'
    ctx.lineJoin = 'round'

    switch (layer.type) {
      case 'path':
        drawPath(ctx, layer, width, height)
        break
      case 'ellipse':
        if (layer.cx != null && layer.cy != null && layer.rx != null && layer.ry != null) {
          ctx.beginPath()
          ctx.ellipse(
            layer.cx * width,
            layer.cy * height,
            Math.abs(layer.rx * width),
            Math.abs(layer.ry * height),
            0,
            0,
            Math.PI * 2,
          )
          ctx.stroke()
        }
        break
      case 'rect':
        if (layer.x != null && layer.y != null && layer.w != null && layer.h != null) {
          ctx.strokeRect(layer.x * width, layer.y * height, layer.w * width, layer.h * height)
        }
        break
      case 'text':
        if (layer.text && layer.x != null && layer.y != null) {
          const fs = (layer.fontSize || 18) * scale
          ctx.font = `600 ${fs}px sans-serif`
          ctx.fillText(layer.text, layer.x * width, layer.y * height)
        }
        break
      default:
        break
    }
    ctx.restore()
  }
}

export async function loadImageElement(url: string): Promise<HTMLImageElement> {
  const load = (crossOrigin: boolean) =>
    new Promise<HTMLImageElement>((resolve, reject) => {
      const img = new Image()
      if (crossOrigin) img.crossOrigin = 'anonymous'
      img.onload = () => resolve(img)
      img.onerror = () => reject(new Error('图片加载失败'))
      img.src = url
    })
  try {
    return await load(true)
  } catch {
    return load(false)
  }
}

export async function exportMergedMarkImage(
  imageUrl: string,
  layers: ImageMarkLayer[],
): Promise<Blob> {
  const img = await loadImageElement(imageUrl)
  const w = img.naturalWidth
  const h = img.naturalHeight

  // 标记单独一层：擦除只影响标注，不会 destination-out 掉底图
  const markCanvas = document.createElement('canvas')
  markCanvas.width = w
  markCanvas.height = h
  const markCtx = markCanvas.getContext('2d')
  if (!markCtx) throw new Error('无法创建画布')
  renderMarkLayers(markCtx, layers, w, h)

  const canvas = document.createElement('canvas')
  canvas.width = w
  canvas.height = h
  const ctx = canvas.getContext('2d')
  if (!ctx) throw new Error('无法创建画布')
  ctx.drawImage(img, 0, 0)
  ctx.drawImage(markCanvas, 0, 0)

  return new Promise((resolve, reject) => {
    canvas.toBlob((blob) => {
      if (blob) resolve(blob)
      else reject(new Error('导出失败，请检查图片是否允许跨域访问'))
    }, 'image/png')
  })
}

export function createLayerId(): string {
  return `mark_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
}
