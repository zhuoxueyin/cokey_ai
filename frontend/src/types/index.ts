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
  created_at: string
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
