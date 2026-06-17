import request from './request'
import type { PromptItem, PromptVersion, PromptListResponse, PromptResponse, PromptVersionResponse } from '../types/prompt'

export async function createPrompt(data: {
  name: string
  content: string
  category?: 'text' | 'image' | 'video'
  tags?: string[]
  description?: string
}): Promise<PromptResponse> {
  return request.post('/prompts', data)
}

export async function updatePrompt(
  promptId: string,
  data: Partial<{
    name: string
    content: string
    category: 'text' | 'image' | 'video'
    tags: string[]
    description: string
  }>,
): Promise<PromptResponse> {
  return request.put(`/prompts/${promptId}`, data)
}

export async function deletePrompt(promptId: string): Promise<{ code: string; message: string }> {
  return request.delete(`/prompts/${promptId}`)
}

export async function getPrompt(promptId: string): Promise<PromptResponse> {
  return request.get(`/prompts/${promptId}`)
}

export async function listPrompts(params: {
  category?: 'text' | 'image' | 'video'
  page?: number
  page_size?: number
}): Promise<PromptListResponse> {
  return request.get('/prompts', { params })
}

export async function publishPrompt(promptId: string): Promise<PromptResponse> {
  return request.post(`/prompts/${promptId}/publish`)
}

export async function rollbackPrompt(promptId: string, version: number): Promise<PromptResponse> {
  return request.post(`/prompts/${promptId}/rollback`, { version })
}

export async function getPromptVersions(promptId: string): Promise<PromptVersionResponse> {
  return request.get(`/prompts/${promptId}/versions`)
}

export async function getPublishedPrompts(): Promise<{ code: string; data: PromptItem[] }> {
  return request.get('/prompts/published/list')
}

export async function getPublishedContent(
  promptId: string,
): Promise<{ code: string; data: { prompt_id: string; content: string } }> {
  return request.get(`/prompts/${promptId}/published/content`)
}
