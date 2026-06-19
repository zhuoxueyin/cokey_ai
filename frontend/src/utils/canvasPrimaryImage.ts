import type { CanvasNode } from '@/types/canvas'

/** 将主图索引限制在有效范围内 */
export function clampPrimaryImageIndex(index: number, imageCount: number): number {
  if (imageCount <= 0) return 0
  return Math.max(0, Math.min(index, imageCount - 1))
}

/** 从节点 config 或运行时 map 解析主图索引（map 优先，防止 config 被覆盖后回退） */
export function resolvePrimaryImageIndex(
  nodeId: string,
  node: CanvasNode | undefined,
  primaryByNode: Record<string, number>,
): number {
  if (primaryByNode[nodeId] !== undefined) {
    return primaryByNode[nodeId]
  }
  return node?.config.output_image_index ?? 0
}

export function upstreamPreviewKey(images: string[], texts: string[]): string {
  return `${images.join('\u0001')}|${texts.join('\u0001')}`
}

/** 把主图索引写回节点 config（供上游收集与持久化） */
export function withPrimaryImageConfig(
  node: CanvasNode,
  primaryByNode: Record<string, number>,
): CanvasNode {
  const imageCount = node.result?.images?.length ?? 0
  const raw = resolvePrimaryImageIndex(node.node_id, node, primaryByNode)
  const index = clampPrimaryImageIndex(raw, imageCount)
  return {
    ...node,
    config: { ...node.config, output_image_index: index },
  }
}

/** 从项目节点列表初始化主图 map */
export function buildPrimaryImageMap(nodes: CanvasNode[] = []): Record<string, number> {
  const map: Record<string, number> = {}
  for (const node of nodes) {
    if (node.node_type !== 'image') continue
    const count = node.result?.images?.length ?? 0
    map[node.node_id] = clampPrimaryImageIndex(node.config.output_image_index ?? 0, count)
  }
  return map
}
