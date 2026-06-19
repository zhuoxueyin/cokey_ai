import type { CanvasNode, CanvasNodeStatus } from '@/types/canvas'
import type { TaskResult } from '@/types'

export function nodeHasOutput(result?: TaskResult): boolean {
  if (!result) return false
  if (result.text) return true
  if (result.images?.length) return true
  if (result.videos?.length) return true
  return false
}

/** 节点展示态：避免任务已成功但 status 仍为 running 时一直红/加载中 */
export function resolveNodeDisplayStatus(
  node: CanvasNode,
  activeRunNodeId?: string | null,
): CanvasNodeStatus {
  if (node.status !== 'running') return node.status
  if (activeRunNodeId === node.node_id) return 'running'
  if (nodeHasOutput(node.result)) return 'success'
  return 'running'
}
