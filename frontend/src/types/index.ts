export interface ApiResponse<T = any> {
  code: string
  message: string
  data?: T
}

export interface PaginatedResponse<T = any> extends ApiResponse<T[]> {
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface ModelItem {
  id: string
  model_code: string
  model_name: string
  category: 'text' | 'image' | 'video'
  cover?: string
  description?: string
  tags: string[]
  is_default: boolean
  param_schema?: ParamSchema
  channel_bindings?: ChannelBinding[]
  status?: 'online' | 'offline' | 'maintenance'
  sort_order?: number
  created_at?: string
  updated_at?: string
  supported_inputs?: {
    image?: boolean
    video?: boolean
    audio?: boolean
  }
}

export interface ParamSchema {
  fields: ParamField[]
}

export interface ParamField {
  name: string
  label: string
  field_type: 'text' | 'textarea' | 'number' | 'slider' | 'select' | 'switch' | 'image_upload'
  required?: boolean
  default?: any
  placeholder?: string
  options?: { label: string; value: any }[]
  min?: number
  max?: number
  step?: number
  help_text?: string
  show_when?: Record<string, any>
}

export interface ChannelBinding {
  channel_code: string
  channel_model_id: string
  priority: number
  status: string
}

export interface TaskItem {
  id: string
  task_id: string
  session_id?: string
  model_code: string
  channel_code?: string
  category: 'text' | 'image' | 'video'
  status: 'pending' | 'processing' | 'success' | 'failed'
  params: Record<string, any>
  params_summary: string
  result?: TaskResult
  error_message?: string
  duration_ms?: number
  trace_id?: string
  channel_request?: Record<string, any>    // 渠道请求参数
  channel_response?: Record<string, any>   // 渠道响应（视频类型包含create和query）
  created_at: string
  updated_at?: string
}

export interface TaskResult {
  type: 'text' | 'image' | 'video'
  text?: string
  images?: { url: string; revised_prompt?: string }[]
  videos?: { url: string; revised_prompt?: string }[]
  choices?: any[]
}

export interface GenerateRequest {
  model_code: string
  category: 'text' | 'image' | 'video'
  session_id?: string
  params: Record<string, any>
}

export interface ParamMapping {
  source: string
  target: string
  default?: any
  transform?: 'first_image' | 'image_list' | 'int' | 'float' | 'str' | 'json' | 'cdn_url'
}

export interface ResponseMapping {
  source: string
  target?: string
  content_type: 'text' | 'image' | 'video' | 'audio'
}

/**
 * Body 入参定义（新格式，推荐使用）
 *
 * value_type:
 *   - 'fixed': 固定值，由配置者填写
 *   - 'dynamic': 动态参数，由前端/业务层传入。value 填写业务层字段名
 *   - 'image': 图片类型，从业务传入的 images 中获取，自动 CDN 化
 */
export interface BodyParam {
  key: string
  value_type: 'fixed' | 'dynamic' | 'image'
  value: string
  description?: string
}

export interface EndpointConfig {
  type: string
  endpoint: string
  method: string
  description?: string

  // —— 新配置方式（推荐）——
  content_type?: string           // Content-Type，默认 application/json
  headers?: Record<string, string> // 自定义 headers，Authorization 由系统自动处理
  body_params?: BodyParam[]       // Body 入参表（优先于 params_template）

  // —— 旧配置方式（保持兼容）——
  params_template?: Record<string, any>
  param_mappings?: ParamMapping[]
  required_params?: string[]
  default_params?: Record<string, any>

  // 响应配置（系统自动识别，无需手动配置）
  response_mappings?: ResponseMapping[]
  response_extract_path?: string
}

export interface ChannelItem {
  id: string
  channel_code: string
  channel_name: string
  channel_type: 'aggregator' | 'direct'
  channel_provider?: 'weelinking' | 'apiyi' | 'volcengine' | null
  base_url: string
  auth_config: ChannelAuthConfig
  api_config: ChannelApiConfig
  endpoints?: EndpointConfig[]
  retry_config: ChannelRetryConfig
  rate_limit_config: ChannelRateLimitConfig
  status: 'active' | 'inactive'
  description?: string
  created_at?: string
  updated_at?: string
}

export interface ChannelAuthConfig {
  api_key?: string
}

export interface ChannelApiConfig {
  text_path?: string
  image_path?: string
  image_edits_path?: string
  video_path?: string
  video_image_path?: string
  audio_path?: string
  text_stream?: boolean
}

export interface ChannelRetryConfig {
  timeout?: number
  max_retries?: number
  retry_delay?: number
}

export interface ChannelRateLimitConfig {
  requests_per_minute?: number
  requests_per_hour?: number
  requests_per_day?: number
}

export interface TaskStats {
  total_tasks: number
  success_count: number
  failed_count: number
  pending_count: number
  processing_count: number
  success_rate: number
  avg_duration_ms: number
  category_breakdown: {
    text: number
    image: number
    video: number
  }
}

export interface AssetItem {
  id: string
  file_name: string
  file_path: string
  url: string
  cdn_urls: string[]
  resolved_cdn_url?: string
  cdn_ready?: boolean
  file_size: number
  content_type: string
  category: 'image' | 'file' | 'video'
  source_type: 'upload' | 'generated'
  created_at: string
  updated_at: string
}

export interface AssetListResponse {
  items: AssetItem[]
  total: number
  page: number
  page_size: number
}

// 提示词类型
export interface PromptItem {
  _id: string
  name: string
  content: string
  category: 'text' | 'image' | 'video'
  tags: string[]
  description: string
  is_active: boolean
  version: number
  published_version: number | null
  created_at: string
  updated_at: string
}
