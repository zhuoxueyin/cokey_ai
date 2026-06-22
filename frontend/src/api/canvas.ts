import request, { longRunningService } from './request'
import type { ApiResponse, PaginatedResponse } from '@/types'
import type { CanvasProject, CanvasNode, CanvasEdge, CanvasViewport, CanvasNodeConfig, CanvasRunRecord, CanvasRunDetail } from '@/types/canvas'

export const createCanvasProject = (params: {
  title?: string
  user_id?: string
}): Promise<ApiResponse<CanvasProject>> => {
  return request.post('/canvas/projects', params)
}

/** 创作工作台固定画布（每用户一个，ID 不变） */
export const getWorkspaceDefaultCanvas = (user_id?: string): Promise<ApiResponse<CanvasProject>> => {
  return request.get('/canvas/projects/workspace-default', { params: { user_id } })
}

export const listCanvasProjects = (params?: {
  user_id?: string
  page?: number
  page_size?: number
}): Promise<PaginatedResponse<CanvasProject>> => {
  return request.get('/canvas/projects', { params })
}

export const getCanvasProject = (projectId: string): Promise<ApiResponse<CanvasProject>> => {
  return request.get(`/canvas/projects/${projectId}`)
}

export const updateCanvasProject = (
  projectId: string,
  data: { title?: string; viewport?: CanvasViewport; user_id?: string },
): Promise<ApiResponse<CanvasProject>> => {
  return request.put(`/canvas/projects/${projectId}`, data)
}

export const deleteCanvasProject = (projectId: string): Promise<ApiResponse<{ deleted: boolean }>> => {
  return request.delete(`/canvas/projects/${projectId}`)
}

export const createCanvasNode = (
  projectId: string,
  data: {
    node_type: string
    title?: string
    position?: { x: number; y: number }
    config?: CanvasNodeConfig
    parent_id?: string | null
  },
): Promise<ApiResponse<CanvasNode>> => {
  return request.post(`/canvas/projects/${projectId}/nodes`, data)
}

export const updateCanvasNode = (
  projectId: string,
  nodeId: string,
  data: Partial<{
    title: string
    position: { x: number; y: number }
    config: CanvasNodeConfig
    status: CanvasNode['status']
    input_stale: boolean
    result: Record<string, any> | null
    task_id: string | null
    error_message: string | null
    result_version: number
    upstream_snapshot: Record<string, unknown>
    parent_id: string | null
  }>,
): Promise<ApiResponse<CanvasNode>> => {
  return request.put(`/canvas/projects/${projectId}/nodes/${nodeId}`, data)
}

export const deleteCanvasNode = (
  projectId: string,
  nodeId: string,
): Promise<ApiResponse<{ deleted: boolean }>> => {
  return request.delete(`/canvas/projects/${projectId}/nodes/${nodeId}`)
}

export const duplicateCanvasNode = (
  projectId: string,
  nodeId: string,
  data?: { position?: { x: number; y: number } },
): Promise<ApiResponse<CanvasNode>> => {
  return request.post(`/canvas/projects/${projectId}/nodes/${nodeId}/duplicate`, data || {})
}

export const createCanvasEdge = (
  projectId: string,
  data: { source_node_id: string; target_node_id: string },
): Promise<ApiResponse<CanvasEdge>> => {
  return request.post(`/canvas/projects/${projectId}/edges`, data)
}

export const deleteCanvasEdge = (
  projectId: string,
  edgeId: string,
): Promise<ApiResponse<{ deleted: boolean }>> => {
  return request.delete(`/canvas/projects/${projectId}/edges/${edgeId}`)
}

export const syncCanvasProject = (
  projectId: string,
  data: {
    viewport?: CanvasViewport
    nodes?: Array<{ node_id: string; position?: { x: number; y: number }; title?: string; parent_id?: string | null }>
  },
): Promise<ApiResponse<CanvasProject>> => {
  return request.put(`/canvas/projects/${projectId}/sync`, data)
}

export const runCanvasNode = (
  projectId: string,
  nodeId: string,
  data?: {
    user_id?: string
    session_id?: string
    config_override?: CanvasNodeConfig
  },
): Promise<ApiResponse<{ node: CanvasNode; task_id: string }>> => {
  return longRunningService.post(`/canvas/projects/${projectId}/nodes/${nodeId}/run`, data || {})
}

export const ackCanvasNodeStale = (
  projectId: string,
  nodeId: string,
): Promise<ApiResponse<CanvasNode>> => {
  return request.post(`/canvas/projects/${projectId}/nodes/${nodeId}/ack-stale`)
}

export const uploadCanvasResource = (
  projectId: string,
  file: File,
  options?: { resource_type?: 'image' | 'video'; x?: number; y?: number },
): Promise<ApiResponse<CanvasNode>> => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('resource_type', options?.resource_type || (file.type.startsWith('video/') ? 'video' : 'image'))
  formData.append('x', String(options?.x ?? 0))
  formData.append('y', String(options?.y ?? 0))
  return request.post(`/canvas/projects/${projectId}/upload-resource`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export const listCanvasRuns = (
  projectId: string,
  params?: { page?: number; page_size?: number },
): Promise<PaginatedResponse<CanvasRunRecord>> => {
  return request.get(`/canvas/projects/${projectId}/runs`, { params })
}

export const getCanvasRunDetail = (
  projectId: string,
  taskId: string,
): Promise<ApiResponse<CanvasRunDetail>> => {
  return request.get(`/canvas/projects/${projectId}/runs/${taskId}`)
}
