import type { StyleModelProtocol } from '@/utils/stylePreview'

export type { StyleModelProtocol } from '@/utils/stylePreview'

export type DramaRenderClass = 'live_action' | 'illustration_2d' | 'render_3d'

export interface DramaStylePreset {
  id: string
  style_id: string
  name: string
  render_class: DramaRenderClass
  genre_tags: string[]
  status: string
  origin?: string
  immutable?: boolean
  description?: string
  style_description_md?: string
  cover_asset_id?: string
  model_prompts?: Record<string, string>
  model_protocol?: StyleModelProtocol
  visual?: {
    reference_films?: string[]
    color_palette?: string[]
    lighting?: string
    texture?: string
  }
  catalog_version?: string
  created_by?: string
}

export interface DramaProject {
  id: string
  project_id: string
  title: string
  stage: string
  genre: string
  target_platform: string
  episode_count: number
  episode_duration_sec: number
  style_preset_id?: string
  style_modifiers: string[]
}

export interface DramaSkill {
  id: string
  skill_code: string
  name: string
  stage: string
  source: string
  source_type?: 'online' | 'repo' | string
  repo_path?: string
  version: string
  version_num?: number
  status: string
  description?: string
  skill_content_md?: string
  skill_meta?: Record<string, string>
  script_files?: string[]
  system_markdown?: string
  user_markdown?: string
  output_schema_id?: string
  default_knowledge_tags?: string[]
  immutable?: boolean
  /** 代码库同步状态（列表 API 附加） */
  repo_folder?: string
  repo_available?: boolean
  repo_has_changes?: boolean
  repo_version?: string
}

export interface RepoSkillCatalogItem {
  folder: string
  path: string
  skill_id: string
  skill_name: string
  version: string
  tag: string
  author: string
  update_time: string
  script_files: string[]
  valid: boolean
  registered?: boolean
  published_version?: string
  target_skill_id?: string
  latest_status?: string
}

export interface RepoSkillPreview extends RepoSkillCatalogItem {
  skill_content_md: string
  validation_error?: string
}

export interface SkillPublishCompare {
  skill_code: string
  draft_id: string
  draft_version?: string
  draft_status?: string
  published_id?: string
  published_version?: string
  has_published: boolean
  has_changes: boolean
  unified_diff: string
  draft_content: string
  published_content: string
  old_line_count: number
  new_line_count: number
}

/** 代码库导入/更新 API 附加字段 */
export interface SkillRepoSyncResult {
  unchanged?: boolean
  needs_publish?: boolean
  repo_version?: string
  published_version?: string
  draft_version?: string
  draft_status?: string
  action?: 'published' | 'already_published'
}

export const RENDER_CLASS_LABELS: Record<DramaRenderClass, string> = {
  live_action: '真人',
  illustration_2d: '2D',
  render_3d: '3D',
}

export const RENDER_CLASS_TABS: { key: string; label: string; value?: DramaRenderClass }[] = [
  { key: 'all', label: '全部' },
  { key: 'live_action', label: '真人', value: 'live_action' },
  { key: 'illustration_2d', label: '2D', value: 'illustration_2d' },
  { key: 'render_3d', label: '3D', value: 'render_3d' },
]
