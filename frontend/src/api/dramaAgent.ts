import request, { longRunningService } from './request'
import type { ApiResponse } from '@/types'
import type {
  DramaAgentChatResult,
  DramaAgentMessage,
  DramaAgentModeDef,
  DramaAgentRef,
  DramaAgentThread,
} from '@/types/dramaAgent'

export const listAgentModes = (): Promise<ApiResponse<DramaAgentModeDef[]>> => {
  return request.get('/drama/agent/modes')
}

export const listAgentThreads = (params?: {
  page?: number
  page_size?: number
  standalone_only?: boolean
}): Promise<import('@/types').PaginatedResponse<DramaAgentThread & {
  message_count?: number
  last_message_preview?: string
  last_message_at?: string
}>> => {
  return request.get('/drama/agent/threads', { params })
}

export const getAgentThreadByCanvas = (
  canvasProjectId: string,
): Promise<ApiResponse<DramaAgentThread>> => {
  return request.get(`/drama/agent/threads/by-canvas/${canvasProjectId}`)
}

export const createAgentThread = (data: {
  project_id?: string
  canvas_project_id?: string
  agent_mode?: string
  model_code?: string
  style_preset_id?: string
  multi_episode?: boolean
  title?: string
}): Promise<ApiResponse<DramaAgentThread>> => {
  return request.post('/drama/agent/threads', data)
}

export const getAgentThread = (threadId: string): Promise<ApiResponse<DramaAgentThread>> => {
  return request.get(`/drama/agent/threads/${threadId}`)
}

export const updateAgentThread = (
  threadId: string,
  data: Partial<{
    stage: string
    model_code: string
    style_preset_id?: string | null
    agent_mode: string
    multi_episode: boolean
    title: string
    canvas_project_id?: string | null
  }>,
): Promise<ApiResponse<DramaAgentThread>> => {
  return request.patch(`/drama/agent/threads/${threadId}`, data)
}

export const deleteAgentThread = (threadId: string): Promise<ApiResponse<{ deleted: boolean }>> => {
  return request.delete(`/drama/agent/threads/${threadId}`)
}

export const spawnAgentCanvas = (
  threadId: string,
): Promise<
  ApiResponse<{
    thread_id: string
    project_id: string
    already_bound: boolean
    binding_repaired?: boolean
    seed_node_ids: string[]
  }>
> => {
  return request.post(`/drama/agent/threads/${threadId}/spawn-canvas`)
}

export const listAgentMessages = (
  threadId: string,
  limit = 50,
): Promise<ApiResponse<DramaAgentMessage[]>> => {
  return request.get(`/drama/agent/threads/${threadId}/messages`, { params: { limit } })
}

export const compactAgentThread = (
  threadId: string,
): Promise<
  ApiResponse<{
    thread_id: string
    compacted: boolean
    reason?: string
    covers_message_count?: number
    compacted_turns?: number
    summary_md?: string
  }>
> => {
  return longRunningService.post(`/drama/agent/threads/${threadId}/compact`)
}

export const agentThreadChat = (
  threadId: string,
  data: { message: string; refs?: DramaAgentRef[]; style_preset_id?: string | null },
): Promise<ApiResponse<DramaAgentChatResult>> => {
  return longRunningService.post(`/drama/agent/threads/${threadId}/chat`, data)
}
