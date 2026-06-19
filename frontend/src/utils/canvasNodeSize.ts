/** 图片节点默认最大外框（完整呈现图片，但不过大） */
export const IMAGE_NODE_MAX = { width: 360, height: 320 }

export const IMAGE_NODE_DEFAULT = { width: 280, height: 280 }

/** 按图片比例计算节点尺寸，保证完整显示且不超过上限 */
export function computeImageNodeSize(
  naturalWidth: number,
  naturalHeight: number,
  maxWidth = IMAGE_NODE_MAX.width,
  maxHeight = IMAGE_NODE_MAX.height,
): { width: number; height: number } {
  if (!naturalWidth || !naturalHeight) {
    return { ...IMAGE_NODE_DEFAULT }
  }
  const ratio = naturalWidth / naturalHeight
  let width = maxWidth
  let height = Math.round(width / ratio)
  if (height > maxHeight) {
    height = maxHeight
    width = Math.round(height * ratio)
  }
  // 节点含标题栏，给内容区留出约 40px
  height += 40
  return {
    width: Math.max(200, Math.round(width)),
    height: Math.max(180, Math.round(height)),
  }
}

export function loadImageDimensions(url: string): Promise<{ width: number; height: number }> {
  return new Promise((resolve) => {
    const img = new Image()
    img.onload = () => resolve({ width: img.naturalWidth, height: img.naturalHeight })
    img.onerror = () => resolve({ width: 0, height: 0 })
    img.src = url
  })
}

export function pickFirstImageUrl(result?: { images?: Array<string | { url?: string }> }): string | null {
  return pickOutputImageUrl(result, 0)
}

export function pickOutputImageUrl(
  result?: { images?: Array<string | { url?: string }> },
  outputImageIndex = 0,
): string | null {
  const imgs = result?.images
  if (!imgs?.length) return null
  const idx = Math.max(0, Math.min(outputImageIndex, imgs.length - 1))
  const img = imgs[idx]
  if (!img) return null
  return typeof img === 'string' ? img : img.url || null
}
