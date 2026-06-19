import type { CanvasNode } from '@/types/canvas'
import type { Edge } from '@xyflow/react'

export interface CanvasUpstreamPreview {
  texts: string[]
  images: string[]
  videos: string[]
  refs: CanvasUpstreamRef[]
}

export interface CanvasUpstreamRef {
  nodeId: string
  title: string
  kind: 'text' | 'image'
  /** @ 展示标签（不含 @ 前缀） */
  mentionLabel: string
  /** 图片缩略图 URL */
  previewUrl?: string
  /** 文本预览（用于文本节点缩略） */
  previewText?: string
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

/** 从连线收集上游文本（→提示词）与图片（→参考图）及 @ 引用元数据 */
export function collectUpstreamPreview(
  nodeId: string,
  edges: Edge[],
  nodeMap: Map<string, CanvasNode>,
): CanvasUpstreamPreview {
  const texts: string[] = []
  const images: string[] = []
  const videos: string[] = []
  const refs = collectUpstreamRefs(nodeId, edges, nodeMap)

  for (const edge of edges) {
    if (edge.target !== nodeId) continue
    const source = nodeMap.get(edge.source)
    if (!source) continue
    const result = source.result
    const cfg = source.config || {}

    if (source.node_type === 'resource') {
      const url = cfg.resource_url
      const rtype = cfg.resource_type || 'image'
      if (url) {
        if (rtype === 'video') videos.push(url)
        else images.push(url)
      }
    } else if (source.node_type === 'video') {
      for (const vid of result?.videos || []) {
        const url = typeof vid === 'string' ? vid : vid?.url
        if (url) videos.push(url)
      }
    } else if (source.node_type === 'image') {
      const url = pickOutputImageUrl(result, cfg.output_image_index)
      if (url) images.push(url)
    } else if (source.node_type === 'text') {
      const text = result?.text ?? cfg.content
      if (text) texts.push(String(text))
    }
  }

  for (const ref of refs) {
    const source = nodeMap.get(ref.nodeId)
    if (!source) continue
    if (ref.kind === 'text') {
      const text = source.result?.text ?? source.config?.content
      if (text && !texts.includes(String(text))) texts.push(String(text))
    } else {
      const url =
        source.node_type === 'resource'
          ? source.config?.resource_url
          : pickOutputImageUrl(source.result, source.config?.output_image_index)
      if (url && !images.includes(url)) images.push(url)
    }
  }

  return { texts, images, videos, refs }
}

function assignMentionLabels(
  raw: Array<Omit<CanvasUpstreamRef, 'mentionLabel'>>,
): CanvasUpstreamRef[] {
  const used = new Map<string, number>()
  let textIdx = 0
  let imageIdx = 0
  return raw.map((item) => {
    let base = item.title.trim().slice(0, 12)
    if (!base) {
      base = item.kind === 'text' ? `文本 ${++textIdx}` : `图片 ${++imageIdx}`
    }
    const count = used.get(base) ?? 0
    used.set(base, count + 1)
    const mentionLabel = count === 0 ? base : `${base}${count + 1}`
    return { ...item, mentionLabel }
  })
}

/** 当前节点可 @ 的上游资源（按连线顺序） */
export function collectUpstreamRefs(
  nodeId: string,
  edges: Edge[],
  nodeMap: Map<string, CanvasNode>,
): CanvasUpstreamRef[] {
  const raw: Array<Omit<CanvasUpstreamRef, 'mentionLabel'>> = []

  for (const edge of edges) {
    if (edge.target !== nodeId) continue
    const source = nodeMap.get(edge.source)
    if (!source) continue

    const result = source.result
    const cfg = source.config || {}
    const title = source.title || source.node_type

    if (source.node_type === 'resource') {
      const url = cfg.resource_url
      if (url && (cfg.resource_type || 'image') !== 'video') {
        raw.push({ nodeId: source.node_id, title, kind: 'image', previewUrl: url })
      }
    } else if (source.node_type === 'text') {
      const text = result?.text ?? cfg.content
      if (text) {
        raw.push({
          nodeId: source.node_id,
          title,
          kind: 'text',
          previewText: String(text).replace(/\s+/g, ' ').trim().slice(0, 80),
        })
      }
    } else if (source.node_type === 'image') {
      const url = pickOutputImageUrl(result, cfg.output_image_index)
      if (url) raw.push({ nodeId: source.node_id, title, kind: 'image', previewUrl: url })
    }
  }

  return assignMentionLabels(raw)
}
