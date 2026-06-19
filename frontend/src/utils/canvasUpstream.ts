import type { CanvasNode } from '@/types/canvas'
import type { Edge } from '@xyflow/react'

export interface CanvasUpstreamPreview {
  texts: string[]
  images: string[]
}

function imageUrlAt(
  result: CanvasNode['result'],
  index: number,
): string | null {
  const imgs = result?.images
  if (!imgs?.length) return null
  const idx = Math.max(0, Math.min(index, imgs.length - 1))
  const img = imgs[idx]
  if (!img) return null
  return typeof img === 'string' ? img : img?.url || null
}

/** 从图片节点结果中按 output_image_index 取下游引用 URL */
export function pickOutputImageUrl(
  result: CanvasNode['result'],
  outputImageIndex?: number,
): string | null {
  return imageUrlAt(result, outputImageIndex ?? 0)
}

/** 从连线收集上游文本（→提示词）与图片（→参考图） */
export function collectUpstreamPreview(
  nodeId: string,
  edges: Edge[],
  nodeMap: Map<string, CanvasNode>,
): CanvasUpstreamPreview {
  const texts: string[] = []
  const images: string[] = []

  for (const edge of edges) {
    if (edge.target !== nodeId) continue
    const source = nodeMap.get(edge.source)
    if (!source) continue

    const result = source.result
    const cfg = source.config || {}

    if (source.node_type === 'resource') {
      const url = cfg.resource_url
      if (url && (cfg.resource_type || 'image') !== 'video') {
        images.push(url)
      }
    } else if (source.node_type === 'text') {
      const text = result?.text ?? cfg.content
      if (text) texts.push(String(text))
    } else if (source.node_type === 'image') {
      const url = pickOutputImageUrl(result, cfg.output_image_index)
      if (url) images.push(url)
    }
  }

  return { texts, images }
}
