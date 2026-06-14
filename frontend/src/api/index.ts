import request from './request'
import type { ApiResponse, ModelItem, TaskItem, TaskResult } from '@/types'

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
