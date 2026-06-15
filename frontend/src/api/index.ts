import request from './request'
import type { ApiResponse, PaginatedResponse, ModelItem, TaskItem, TaskResult, ChannelItem, TaskStats } from '@/types'

export interface PaginatedParams {
  page?: number
  page_size?: number
  category?: string
  status?: string
  session_id?: string
  model_code?: string
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

export const createSession = (category: string): Promise<ApiResponse<{ session_id: string; category: string }>> => {
  return request.post('/sessions', { category })
}

export const generate = (params: {
  model_code: string
  category: string
  session_id?: string
  params: Record<string, any>
}): Promise<ApiResponse<TaskResult & { task_id: string; status: string; duration_ms?: number; created_at: string }>> => {
  return request.post('/tasks/generate', params)
}

export const createTask = (params: {
  model_code: string
  category: string
  session_id?: string
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

export const getSessionTasks = (session_id: string): Promise<ApiResponse<TaskItem[]>> => {
  return request.get(`/tasks/session/${session_id}`)
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
