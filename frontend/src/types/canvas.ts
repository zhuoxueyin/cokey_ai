import type { TaskResult } from './index'
import type { CanvasUpstreamPreview } from '@/utils/canvasUpstream'
import type { ImageMarkLayer } from './imageMark'

export type CanvasNodeType = 'resource' | 'text' | 'image' | 'video' | 'group' | 'title'
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
  is_workspace_default?: boolean
  agent_thread_id?: string
  source_agent_thread_id?: string
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
  /** 标题节点：H1-H5 级别（兼容旧数据，优先用 title_font_size） */
  heading_level?: 1 | 2 | 3 | 4 | 5
  /** 标题节点：字号 px（14–40） */
  title_font_size?: number
  /** 标题节点：文字颜色 */
  color?: string
  /** 标题节点：字体族 */
  font_family?: 'system' | 'sans' | 'serif' | 'mono'
  /** 节点宽度 */
  width?: number
  /** 节点高度（可选，文本节点自适应） */
  height?: number
  /** 用户手动调整过尺寸后为 true，不再自动按图片缩放 */
  user_resized?: boolean
  /** 多图结果时作为下游引用的图片索引，默认 0 */
  output_image_index?: number
  /** 绑定的视觉风格（风格广场 style_id） */
  style_preset_id?: string
  /** 风格名称缓存，便于节点展示 */
  style_preset_name?: string
  /** 图片标记图层（归一化坐标，可重新编辑） */
  mark_layers?: ImageMarkLayer[]
  /** 首次标记前的原图 URL */
  mark_source_url?: string
}

export interface CanvasNode {
  id: string
  node_id: string
  project_id: string
  node_type: CanvasNodeType
  title: string
  position: { x: number; y: number }
  /** 所属分组节点 ID */
  parent_id?: string | null
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

/** 画布项目运行记录（列表项） */
export interface CanvasRunRecord {
  task_id: string
  /** 链路日志 ID（trace_id / Log ID） */
  trace_id?: string
  project_id?: string
  canvas_project_id?: string
  node_id?: string
  canvas_node_id?: string
  node_title?: string
  node_type?: CanvasNodeType | string
  canvas_node_type?: string
  model_code?: string
  channel_code?: string
  /** 渠道侧任务 ID（如火山视频） */
  external_task_id?: string
  category?: string
  status: string
  params_summary?: string
  error_message?: string
  duration_ms?: number
  created_at: string
  updated_at?: string
}

/** 画布运行记录详情 */
export interface CanvasRunDetail extends CanvasRunRecord {
  result?: TaskResult
  params?: Record<string, unknown>
  channel_request?: Record<string, unknown>
  channel_response?: Record<string, unknown>
}

export interface CanvasNodeData {
  canvasNode: CanvasNode
  onRun?: (nodeId: string) => void
  onAckStale?: (nodeId: string) => void
  onResizeEnd?: (width: number, height: number) => void
  onResizeStart?: () => void
  onAutoSize?: (width: number, height: number) => void
  onEditText?: (text: string) => void
  onCopyText?: (text: string) => void
  onTitleChange?: (title: string) => void
  onEditTitleContent?: (content: string) => void
  /** 标题节点：单击后进入编辑（非选中即编辑） */
  titleEditing?: boolean
  onTitleEditEnd?: () => void
  onOpenPanel?: () => void
  onDuplicate?: () => void
  onUpdateConfig?: (patch: Partial<CanvasNodeConfig>) => void | Promise<void>
  /** 多图节点当前主图索引（仅主图可被下游引用） */
  primaryImageIndex?: number
  onSelectPrimaryImage?: (index: number) => void
  onSelectOutputImage?: (index: number) => void
  selected?: boolean
  upstream?: CanvasUpstreamPreview
  /** 当前正在本地发起运行的节点 ID */
  activeRunNodeId?: string | null
}
