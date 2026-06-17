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
  status: 'draft' | 'published'  // 状态：未发布/已发布
  created_at: string
  updated_at: string
}

export interface PromptVersion {
  _id: string
  prompt_id: string
  version: number
  content: string
  comment: string
  created_at: string
}

export interface PromptListResponse {
  code: string
  message: string
  data: {
    data: PromptItem[]
    total: number
    page: number
    page_size: number
    total_pages: number
  }
}

export interface PromptResponse {
  code: string
  message: string
  data: PromptItem
}

export interface PromptVersionResponse {
  code: string
  message: string
  data: PromptVersion[]
}