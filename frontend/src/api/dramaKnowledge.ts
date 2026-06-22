import request from './request'
import type { ApiResponse, PaginatedResponse } from '@/types'

type PaginatedParams = { page?: number; page_size?: number }

export interface KnowledgeCategory {
  id: string
  code: string
  name: string
  builtin?: boolean
  description?: string
  applicable_stages?: string[]
  entry_count?: number
  created_at?: string
  updated_at?: string
}

export interface CreationStageOption {
  stage: string
  label: string
}

export interface KnowledgeSource {
  type: string
  url?: string
  filename?: string
  fetch_status?: string
  message?: string
}

export interface KnowledgeEntry {
  id: string
  entry_id: string
  category: string
  domain: string
  title: string
  summary: string
  content_markdown: string
  tags: string[]
  status: string
  source?: KnowledgeSource
  version?: number
  updated_at?: string
  import_hint?: string
}

export const listKnowledgeCategories = (): Promise<ApiResponse<KnowledgeCategory[]>> => {
  return request.get('/admin/drama/knowledge/categories')
}

export const listKnowledgeStages = (): Promise<ApiResponse<CreationStageOption[]>> => {
  return request.get('/admin/drama/knowledge/stages')
}

export const createKnowledgeCategory = (data: {
  code: string
  name: string
  description?: string
  applicable_stages?: string[]
}): Promise<ApiResponse<KnowledgeCategory>> => {
  return request.post('/admin/drama/knowledge/categories', data)
}

export const updateKnowledgeCategory = (
  code: string,
  data: { name?: string; description?: string; applicable_stages?: string[] },
): Promise<ApiResponse<KnowledgeCategory>> => {
  return request.put(`/admin/drama/knowledge/categories/${encodeURIComponent(code)}`, data)
}

export const deleteKnowledgeCategory = (
  code: string,
): Promise<ApiResponse<{ deleted: boolean }>> => {
  return request.delete(`/admin/drama/knowledge/categories/${encodeURIComponent(code)}`)
}

export const listKnowledgeTags = (limit = 200): Promise<ApiResponse<string[]>> => {
  return request.get('/admin/drama/knowledge/tags', { params: { limit } })
}

export const listKnowledgeAdmin = (params?: PaginatedParams & {
  category?: string
  keyword?: string
  status?: string
}): Promise<PaginatedResponse<KnowledgeEntry>> => {
  return request.get('/admin/drama/knowledge', { params })
}

export const getKnowledgeAdmin = (entryId: string): Promise<ApiResponse<KnowledgeEntry>> => {
  return request.get(`/admin/drama/knowledge/entry/${entryId}`)
}

export const createKnowledgeAdmin = (data: {
  entry_id?: string
  category: string
  title: string
  summary?: string
  content_markdown?: string
  tags?: string[]
}): Promise<ApiResponse<KnowledgeEntry>> => {
  return request.post('/admin/drama/knowledge', data)
}

export const updateKnowledgeAdmin = (
  entryId: string,
  data: Partial<{
    category: string
    title: string
    summary: string
    content_markdown: string
    tags: string[]
  }>,
): Promise<ApiResponse<KnowledgeEntry>> => {
  return request.put(`/admin/drama/knowledge/entry/${entryId}`, data)
}

export const previewFeishuKnowledge = (url: string): Promise<ApiResponse<{
  status: string
  title?: string
  content_markdown?: string
  message?: string
}>> => {
  return request.post('/admin/drama/knowledge/preview-feishu', { url })
}

export const importKnowledgeAdmin = (data: {
  source_type: 'manual' | 'file' | 'feishu'
  category: string
  title?: string
  summary?: string
  content_markdown?: string
  tags?: string[]
  feishu_url?: string
  filename?: string
  publish?: boolean
}): Promise<ApiResponse<KnowledgeEntry>> => {
  return request.post('/admin/drama/knowledge/import', data)
}

export const publishKnowledgeAdmin = (entryId: string): Promise<ApiResponse<KnowledgeEntry>> => {
  return request.post(`/admin/drama/knowledge/entry/${entryId}/publish`)
}

export const deleteKnowledgeAdmin = (entryId: string): Promise<ApiResponse<{ deleted: boolean }>> => {
  return request.delete(`/admin/drama/knowledge/entry/${entryId}`)
}

export const reindexKnowledgeVectors = (): Promise<ApiResponse<{ reindexed: number }>> => {
  return request.post('/admin/drama/knowledge/reindex-vectors')
}
