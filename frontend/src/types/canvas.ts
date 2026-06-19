import type { TaskResult } from './index'
import type { CanvasUpstreamPreview } from '@/utils/canvasUpstream'

export type CanvasNodeType = 'resource' | 'text' | 'image' | 'video'
export type CanvasNodeStatus = 'idle' | 'running' | 'success' | 'failed'

export interface CanvasViewport {
  x: number
  y: number
  zoom: number
}

export interface CanvasProject {
  id: string
  project_id: string
  user_id?: string
  title: string
  viewport: CanvasViewport
  created_at: string
  updated_at: string
  nodes?: CanvasNode[]
  edges?: CanvasEdge[]
}

export interface CanvasNodeConfig {
  prompt?: string
  model_code?: string
  params?: Record<string, any>
  resource_url?: string
  resource_type?: 'image' | 'video'
  resource_name?: string
  /** 文本节点：manual=自己编写，generate=模型生成 */
  text_mode?: 'manual' | 'generate'
  /** 文本节点手动编写内容 */
  content?: string
  /** 节点宽度 */
  width?: number
  /** 节点高度（可选，文本节点自适应） */
  height?: number
  /** 用户手动调整过尺寸后为 true，不再自动按图片缩放 */
  user_resized?: boolean
  /** 多图结果时作为下游引用的图片索引，默认 0 */
  output_image_index?: number
}

export interface CanvasNode {
  id: string
  node_id: string
  project_id: string
  node_type: CanvasNodeType
  title: string
  position: { x: number; y: number }
  config: CanvasNodeConfig
  result?: TaskResult
  result_version: number
  task_id?: string
  status: CanvasNodeStatus
  error_message?: string
  input_stale: boolean
  upstream_snapshot: Record<string, { result_version: number; node_type: string }>
  created_at: string
  updated_at: string
}

export interface CanvasEdge {
  id: string
  edge_id: string
  project_id: string
  source_node_id: string
  target_node_id: string
  source_handle: string
  target_handle: string
  created_at: string
}

export interface CanvasNodeData {
  canvasNode: CanvasNode
  onRun?: (nodeId: string) => void
  onUpdateConfig?: (nodeId: string, config: Partial<CanvasNodeConfig>) => void
  onAckStale?: (nodeId: string) => void
  onResizeEnd?: (width: number, height: number) => void
  onResizeStart?: () => void
  onAutoSize?: (width: number, height: number) => void
  onEditText?: (text: string) => void
  onCopyText?: (text: string) => void
  onOpenPanel?: () => void
  onDuplicate?: () => void
  /** 多图节点当前主图索引（仅主图可被下游引用） */
  primaryImageIndex?: number
  onSelectPrimaryImage?: (index: number) => void
  onSelectOutputImage?: (index: number) => void
  selected?: boolean
  upstream?: CanvasUpstreamPreview
}
