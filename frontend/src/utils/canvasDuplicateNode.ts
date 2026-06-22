import type { CanvasNode } from '@/types/canvas'
import { IMAGE_NODE_DEFAULT } from '@/utils/canvasNodeSize'

/** 图片节点粘贴副本：只保留生图参数，清空结果与运行态（兼容旧后端仍返回 result 的情况） */
export function sanitizeDuplicatedImageNode(node: CanvasNode): CanvasNode {
  if (node.node_type !== 'image') return node

  const config = { ...node.config, output_image_index: 0 }
  if (!node.config.user_resized) {
    config.width = IMAGE_NODE_DEFAULT.width
    config.height = IMAGE_NODE_DEFAULT.height
  }

  return {
    ...node,
    status: 'idle',
    result: undefined,
    result_version: 0,
    task_id: undefined,
    error_message: undefined,
    input_stale: false,
    upstream_snapshot: {},
    config,
  }
}

export function imageDuplicateNeedsServerRepair(serverNode: CanvasNode): boolean {
  return (
    serverNode.node_type === 'image' &&
    (Boolean(serverNode.result) ||
      serverNode.status !== 'idle' ||
      Boolean(serverNode.task_id) ||
      (serverNode.result_version ?? 0) > 0)
  )
}
