import request, { longRunningService } from './request'
import type { ApiResponse, PaginatedResponse, ModelItem, TaskItem, TaskResult, ChannelItem, TaskStats, AssetItem, AssetListResponse } from '@/types'

export interface PaginatedParams {
  page?: number
  page_size?: number
  category?: string
  status?: string
  session_id?: string
  model_code?: string
  sort_by?: string
  sort_order?: number
  time_range?: string  // 时间范围：1h, 6h, 24h, 7d, 30d, all
}

export const getModels = (category?: string): Promise<ApiResponse<ModelItem[]>> => {
  return request.get('/models', { params: { category } })
}

export const getDefaultModel = (category: string): Promise<ApiResponse<ModelItem>> => {
  return request.get('/models/default', { params: { category } })
}

export const getModelDetail = (model_code: string): Promise<ApiResponse<ModelItem>> => {
  return request.get(`/models/${model_code}`)
}

export const getSessionTasks = (session_id: string, category?: string, time_range?: number): Promise<ApiResponse<TaskItem[]>> => {
  const params: Record<string, any> = {}
  if (category && category !== 'all') params.category = category
  if (time_range !== undefined) params.time_range = time_range
  return request.get(`/tasks/session/${session_id}`, { params })
}

export const generate = (params: {
  model_code: string
  category: string
  session_id?: string
  user_id?: string
  params: Record<string, any>
}): Promise<ApiResponse<TaskResult & { task_id: string; status: string; duration_ms?: number; created_at: string }>> => {
  // 使用长时间任务请求实例（30分钟超时）
  return longRunningService.post('/tasks/generate', params)
}

export const createTask = (params: {
  model_code: string
  category: string
  session_id?: string
  user_id?: string
  params: Record<string, any>
}): Promise<ApiResponse<{ task_id: string; status: string }>> => {
  return request.post('/tasks', params)
}

export const executeTask = (task_id: string): Promise<ApiResponse<any>> => {
  return request.post(`/tasks/${task_id}/execute`)
}

export const getTaskStatus = (task_id: string): Promise<ApiResponse<TaskResult & {
  task_id: string
  status: string
  error_message?: string
  duration_ms?: number
  created_at: string
}>> => {
  return request.get(`/tasks/${task_id}`)
}

export const listTasks = (params?: {
  page?: number
  page_size?: number
  session_id?: string
  user_id?: string
  category?: string
  status?: string
  time_range?: string  // 时间范围：1h, 6h, 24h, 7d, 30d, all（默认6h）
}): Promise<PaginatedResponse<TaskItem>> => {
  return request.get('/tasks', { params })
}

// ==================== 会话管理 ====================
export const createSession = (params: {
  category: string
  user_id?: string
}): Promise<ApiResponse<{ session_id: string }>> => {
  return request.post('/sessions', params)
}

export const getSession = (session_id: string): Promise<ApiResponse<any>> => {
  return request.get(`/sessions/${session_id}`)
}

export const updateSessionContext = (session_id: string, context: Record<string, any>): Promise<ApiResponse<any>> => {
  return request.put(`/sessions/${session_id}/context`, { context })
}

export const listUserSessions = (user_id?: string): Promise<ApiResponse<any[]>> => {
  return request.get('/sessions', { params: { user_id } })
}

export const uploadImage = (file: File): Promise<ApiResponse<{ url: string; file_size: number; content_type: string }>> => {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/upload/image', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export const uploadFile = (file: File): Promise<ApiResponse<{ url: string; file_size: number; content_type: string }>> => {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/upload/file', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export const listModelsAdmin = (params?: PaginatedParams): Promise<PaginatedResponse<ModelItem>> => {
  return request.get('/admin/models', { params })
}

export const getModelAdmin = (model_id: string): Promise<ApiResponse<ModelItem>> => {
  return request.get(`/admin/models/${model_id}`)
}

export const createModelAdmin = (data: Partial<ModelItem> & { model_code: string; model_name: string; category: string }): Promise<ApiResponse<ModelItem>> => {
  return request.post('/admin/models', data)
}

export const updateModelAdmin = (model_id: string, data: Partial<ModelItem>): Promise<ApiResponse<ModelItem>> => {
  return request.put(`/admin/models/${model_id}`, data)
}

export const deleteModelAdmin = (model_id: string): Promise<ApiResponse<{ deleted: boolean }>> => {
  return request.delete(`/admin/models/${model_id}`)
}

export const setModelStatus = (model_id: string, status: 'online' | 'offline' | 'maintenance'): Promise<ApiResponse<{ status: string }>> => {
  return request.post(`/admin/models/${model_id}/status`, { status })
}

export const batchImportModels = (channel_code: string, models: any[]): Promise<ApiResponse<any>> => {
  return request.post('/admin/models/batch-import', { channel_code, models })
}

export const listChannelsAdmin = (params?: PaginatedParams): Promise<PaginatedResponse<ChannelItem>> => {
  return request.get('/admin/channels', { params })
}

export const getChannelAdmin = (channel_id: string): Promise<ApiResponse<ChannelItem>> => {
  return request.get(`/admin/channels/${channel_id}`)
}

export const createChannelAdmin = (data: Partial<ChannelItem> & { channel_code: string; channel_name: string; channel_type: string; base_url: string; auth_config: any }): Promise<ApiResponse<ChannelItem>> => {
  return request.post('/admin/channels', data)
}

export const updateChannelAdmin = (channel_id: string, data: Partial<ChannelItem>): Promise<ApiResponse<ChannelItem>> => {
  return request.put(`/admin/channels/${channel_id}`, data)
}

export const deleteChannelAdmin = (channel_id: string): Promise<ApiResponse<{ deleted: boolean }>> => {
  return request.delete(`/admin/channels/${channel_id}`)
}

export const setChannelStatus = (channel_id: string, status: 'active' | 'inactive'): Promise<ApiResponse<{ status: string }>> => {
  return request.post(`/admin/channels/${channel_id}/status`, { status })
}

export const listTasksAdmin = (params?: PaginatedParams): Promise<PaginatedResponse<TaskItem>> => {
  return request.get('/admin/tasks', { params })
}

export const getTaskAdmin = (task_id: string): Promise<ApiResponse<TaskItem>> => {
  return request.get(`/admin/tasks/${task_id}`)
}

export const getTaskStatsAdmin = (params?: { start_time?: string; end_time?: string; category?: string }): Promise<ApiResponse<TaskStats>> => {
  return request.get('/admin/tasks/stats/overview', { params })
}

// ==================== 用户认证 ====================

export interface UserInfo {
  userId: string
  username: string
  nickname: string
  avatar_url?: string
  status: number
}

export const register = (username: string, password: string, nickname?: string): Promise<ApiResponse<{ userId: string; username: string; nickname: string }>> => {
  return request.post('/auth/register', { username, password, nickname })
}

export const login = (username: string, password: string): Promise<ApiResponse<{ token: string; user: UserInfo }>> => {
  return request.post('/auth/login', { username, password })
}

export const logout = (): Promise<ApiResponse<void>> => {
  return request.post('/auth/logout')
}

export const getProfile = (): Promise<ApiResponse<UserInfo>> => {
  return request.get('/user/profile')
}

export const updateProfile = (data: { nickname?: string; avatar_url?: string }): Promise<ApiResponse<UserInfo>> => {
  return request.put('/user/profile', data)
}

export const updatePassword = (old_password: string, new_password: string): Promise<ApiResponse<void>> => {
  return request.put('/user/pwd', { old_password, new_password })
}

export const cancelAllTasksAdmin = (): Promise<ApiResponse<{ matched_count: number; modified_count: number }>> => {
  return request.post('/admin/tasks/cancel/all')
}

export const cancelTaskAdmin = (task_id: string): Promise<ApiResponse<{ message: string }>> => {
  return request.post(`/admin/tasks/${task_id}/cancel`)
}

// ==================== 资源管理 ====================
export const listAssets = (params?: {
  page?: number
  page_size?: number
  category?: string
  source_type?: 'upload' | 'generated'
}): Promise<ApiResponse<AssetListResponse>> => {
  return request.get('/assets', { params })
}

export const getAsset = (asset_id: string): Promise<ApiResponse<AssetItem>> => {
  return request.get(`/assets/${asset_id}`)
}

export const uploadAsset = (
  file: File,
  options?: { category?: string; source_type?: 'upload' | 'generated' }
): Promise<ApiResponse<AssetItem>> => {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/assets/upload', formData, {
    params: options,
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export const deleteAsset = (asset_id: string): Promise<ApiResponse<{ id: string; deleted: boolean }>> => {
  return request.delete(`/assets/${asset_id}`)
}
