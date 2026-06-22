import request from './request'
import type { ApiResponse, PaginatedResponse } from '@/types'
import type { DramaProject, DramaSkill, DramaStylePreset, RepoSkillCatalogItem, RepoSkillPreview, SkillPublishCompare } from '@/types/drama'

type PaginatedParams = { page?: number; page_size?: number }

export const listDramaStylesAdmin = (params?: PaginatedParams & {
  render_class?: string
  status?: string
  keyword?: string
}): Promise<PaginatedResponse<DramaStylePreset>> => {
  return request.get('/admin/drama/styles', { params })
}

export const createDramaStyleAdmin = (data: {
  name: string
  render_class?: string
  genre_tags?: string[]
  style_id?: string
  cover_url?: string
  style_description_md?: string
  model_prompts?: Record<string, string>
  publish?: boolean
}): Promise<ApiResponse<DramaStylePreset>> => {
  return request.post('/admin/drama/styles', data)
}

export const publishDramaStyle = (styleId: string): Promise<ApiResponse<DramaStylePreset>> => {
  return request.post(`/admin/drama/styles/${styleId}/publish`)
}

export const getDramaStyleAdmin = (styleId: string): Promise<ApiResponse<DramaStylePreset>> => {
  return request.get(`/admin/drama/styles/${styleId}`)
}

export const updateDramaStyleAdmin = (
  styleId: string,
  data: Partial<{
    name: string
    render_class: string
    genre_tags: string[]
    cover_url: string
    style_description_md?: string
    model_prompts?: Record<string, string>
    visual?: Record<string, unknown>
  }>,
): Promise<ApiResponse<DramaStylePreset>> => {
  return request.put(`/admin/drama/styles/${styleId}`, data)
}

export const listDramaStylesUser = (params?: PaginatedParams & {
  render_class?: string
  keyword?: string
}): Promise<PaginatedResponse<DramaStylePreset>> => {
  return request.get('/drama/styles', { params })
}

export const getDramaStyle = (styleId: string): Promise<ApiResponse<DramaStylePreset>> => {
  return request.get(`/drama/styles/${styleId}`)
}

export const createUserStyle = (data: {
  name: string
  render_class?: string
  genre_tags?: string[]
  style_id?: string
  cover_url?: string
  style_description_md?: string
  model_prompts?: Record<string, string>
  publish?: boolean
}): Promise<ApiResponse<DramaStylePreset>> => {
  return request.post('/drama/styles', data)
}

export const updateUserStyle = (
  styleId: string,
  data: Partial<{
    name: string
    render_class: string
    genre_tags: string[]
    cover_url: string
    style_description_md?: string
    model_prompts?: Record<string, string>
    visual?: Record<string, unknown>
  }>,
): Promise<ApiResponse<DramaStylePreset>> => {
  return request.put(`/drama/styles/${styleId}`, data)
}

export const deleteDramaStyleAdmin = (styleId: string): Promise<ApiResponse<{ deleted: boolean }>> => {
  return request.delete(`/admin/drama/styles/${styleId}`)
}

export const deleteUserStyle = (styleId: string): Promise<ApiResponse<{ deleted: boolean }>> => {
  return request.delete(`/drama/styles/${styleId}`)
}

export const getCharacterPromptTemplate = (): Promise<
  ApiResponse<{
    version: string
    markdown: string
    section_order: { key: string; label: string }[]
    output_fields: string[]
  }>
> => {
  return request.get('/drama/character-prompt-template')
}

export const listDramaProjects = (params?: PaginatedParams): Promise<PaginatedResponse<DramaProject>> => {
  return request.get('/drama/projects', { params })
}

export const createDramaProject = (data: {
  title: string
  genre?: string
  style_preset_id?: string
}): Promise<ApiResponse<DramaProject>> => {
  return request.post('/drama/projects', data)
}

export const dramaProjectChat = (
  projectId: string,
  data: { message: string; stage?: string },
): Promise<ApiResponse<Record<string, unknown>>> => {
  return request.post(`/drama/projects/${projectId}/chat`, data)
}

export const listDramaSkillsAdmin = (params?: PaginatedParams & {
  stage?: string
  status?: string
}): Promise<PaginatedResponse<DramaSkill>> => {
  return request.get('/admin/drama/skills', { params })
}

export const listRepoSkillCatalog = (): Promise<ApiResponse<RepoSkillCatalogItem[]>> => {
  return request.get('/admin/drama/skills/repo-catalog')
}

export const listRepoSkillFolders = (): Promise<ApiResponse<string[]>> => {
  return request.get('/admin/drama/skills/repo-folders')
}

export const previewRepoSkill = (folder: string): Promise<ApiResponse<RepoSkillPreview>> => {
  return request.get('/admin/drama/skills/repo-preview', { params: { folder } })
}

export const importRepoSkillAdmin = (data: {
  folder: string
  stage?: string
  publish?: boolean
  target_skill_id?: string
}): Promise<ApiResponse<DramaSkill>> => {
  return request.post('/admin/drama/skills/import-repo', data)
}

export const reimportRepoSkillAdmin = (
  skillId: string,
  data?: { folder?: string; publish?: boolean },
): Promise<ApiResponse<DramaSkill>> => {
  return request.post(`/admin/drama/skills/${skillId}/reimport-repo`, data || {})
}

export const getDramaSkillAdmin = (skillId: string): Promise<ApiResponse<DramaSkill>> => {
  return request.get(`/admin/drama/skills/${skillId}`)
}

export const createDramaSkillAdmin = (data: {
  skill_code: string
  name: string
  stage?: string
  source_type?: string
  description?: string
  skill_content_md?: string
  output_schema_id?: string
  default_knowledge_tags?: string[]
}): Promise<ApiResponse<DramaSkill>> => {
  return request.post('/admin/drama/skills', data)
}

export const updateDramaSkillAdmin = (
  skillId: string,
  data: Partial<{
    name: string
    stage: string
    description: string
    skill_content_md: string
    output_schema_id: string
    default_knowledge_tags: string[]
  }>,
): Promise<ApiResponse<DramaSkill>> => {
  return request.put(`/admin/drama/skills/${skillId}`, data)
}

export const publishDramaSkillAdmin = (skillId: string): Promise<ApiResponse<DramaSkill>> => {
  return request.post(`/admin/drama/skills/${skillId}/publish`)
}

export const compareSkillBeforePublish = (
  skillId: string,
): Promise<ApiResponse<SkillPublishCompare>> => {
  return request.get(`/admin/drama/skills/${skillId}/publish-compare`)
}

export const listSkillVersionsAdmin = (skillCode: string): Promise<ApiResponse<DramaSkill[]>> => {
  return request.get(`/admin/drama/skills/by-code/${encodeURIComponent(skillCode)}/versions`)
}

export const rollbackSkillAdmin = (
  skillCode: string,
  versionNum: number,
): Promise<ApiResponse<DramaSkill>> => {
  return request.post(`/admin/drama/skills/by-code/${encodeURIComponent(skillCode)}/rollback`, {
    version_num: versionNum,
  })
}

export const deleteDramaSkillAdmin = (skillId: string): Promise<ApiResponse<{ deleted: boolean }>> => {
  return request.delete(`/admin/drama/skills/${skillId}`)
}
