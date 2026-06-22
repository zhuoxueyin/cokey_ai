import type { DramaAgentRef } from '@/types/dramaAgent'
import type { AssetItem } from '@/types'
import type { CanvasNode } from '@/types/canvas'
import { isCdnUrl, pickCdnUrl } from '@/utils/cdnUrl'
import { pickOutputImageUrl } from '@/utils/canvasNodeSize'

/** 从资源库条目解析引用 URL（须为 CDN） */
export function assetToAgentRef(asset: AssetItem): DramaAgentRef | null {
  try {
    return {
      type: 'asset',
      id: asset.id,
      name: asset.file_name,
      url: pickCdnUrl(asset),
    }
  } catch {
    return null
  }
}

/** 从画布节点收集可引用图片 */
export function collectCanvasAgentRefs(nodes: CanvasNode[] = []): DramaAgentRef[] {
  const out: DramaAgentRef[] = []
  const seen = new Set<string>()

  for (const node of nodes) {
    let url: string | undefined
    if (node.node_type === 'resource') {
      if ((node.config?.resource_type || 'image') === 'video') continue
      url = node.config?.resource_url
    } else if (node.node_type === 'image') {
      const images = node.result?.images
      if (Array.isArray(images) && images.length) {
        const idx = node.config?.output_image_index ?? 0
        url = pickOutputImageUrl(node.result, idx) || undefined
      }
    }
    if (!url || !isCdnUrl(url) || seen.has(url)) continue
    seen.add(url)
    out.push({
      type: 'canvas',
      id: node.node_id,
      name: node.title || node.node_type,
      url,
    })
  }
  return out
}

export function mergeAgentRefs(existing: DramaAgentRef[], incoming: DramaAgentRef[]): DramaAgentRef[] {
  const seen = new Set(existing.map((r) => r.id || r.url).filter(Boolean))
  const next = [...existing]
  for (const ref of incoming) {
    const key = ref.id || ref.url
    if (!key || !ref.url || seen.has(key)) continue
    seen.add(key)
    next.push(ref)
  }
  return next
}
