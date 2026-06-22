import type { CanvasNode, CanvasNodeStatus } from '@/types/canvas'
import type { TaskResult } from '@/types'

export function nodeHasOutput(result?: TaskResult): boolean {
  if (!result) return false
  if (result.text) return true
  if (result.images?.length) return true
  if (result.videos?.length) return true
  return false
}

/** 服务端节点相对本地是否有可同步的状态/结果变化（用于 running 轮询） */
export function shouldSyncCanvasNodeFromServer(local: CanvasNode, server: CanvasNode): boolean {
  if (local.node_id !== server.node_id) return false
  if (local.status === 'running' && server.status !== 'running') return true
  if (local.result_version !== server.result_version) return true
  if (server.status === 'success' && nodeHasOutput(server.result) && !nodeHasOutput(local.result)) {
    return true
  }
  if (server.status === 'failed' && local.status === 'running') return true
  if (local.task_id !== server.task_id && server.task_id) return true
  return false
}

export function listRunningCanvasNodeIds(nodes: Iterable<CanvasNode>): string[] {
  return [...nodes].filter((n) => n.status === 'running').map((n) => n.node_id)
}

/** 节点展示态：运行中优先；已成功但结果未同步时仍显示运行中 */
export function resolveNodeDisplayStatus(
  node: CanvasNode,
  activeRunNodeId?: string | null,
): CanvasNodeStatus {
  const isActiveRun = activeRunNodeId === node.node_id
  if (node.status === 'running' || isActiveRun) {
    if (nodeHasOutput(node.result)) return 'success'
    return 'running'
  }
  if (node.status === 'success' && !nodeHasOutput(node.result) && node.task_id) {
    return 'running'
  }
  return node.status
}
