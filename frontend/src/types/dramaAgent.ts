export type DramaAgentMode =
  | 'creative_short_drama'
  | 'aigc_manga'
  | 'mv'
  | 'marketing_ad'

export interface DramaAgentModeDef {
  mode: DramaAgentMode
  name: string
  description: string
  default_stage: string
  knowledge_categories: string[]
}

export interface DramaAgentThread {
  id: string
  thread_id: string
  project_id?: string
  user_id?: string
  canvas_project_id?: string
  agent_mode: DramaAgentMode
  model_code?: string
  style_preset_id?: string
  multi_episode: boolean
  stage: string
  title: string
  status: string
  created_at?: string
  updated_at?: string
  message_count?: number
  last_message_preview?: string
  last_message_at?: string
}

export interface DramaAgentProcessStep {
  step_id: string
  kind: 'context' | 'knowledge' | 'skill' | 'style' | 'model' | 'thinking' | string
  title: string
  status: 'ok' | 'empty' | 'skip' | 'error' | string
  summary?: string
  detail?: string
  items?: { id?: string; title?: string }[]
}

export interface DramaAgentMessage {
  id: string
  message_id: string
  thread_id: string
  role: 'user' | 'assistant' | 'tool' | 'system'
  content: string
  refs?: DramaAgentRef[]
  meta?: Record<string, unknown>
  created_at?: string
}

export interface DramaAgentRef {
  type: string
  id?: string
  name?: string
  url?: string
}

export interface DramaAgentChatResult {
  thread_id: string
  message: DramaAgentMessage
  reply_markdown: string
  stage: string
  agent_mode: DramaAgentMode
  mode_name?: string
  model_code?: string
  style_preset_id?: string
  style_name?: string
  knowledge_refs?: string[]
  context_meta?: Record<string, unknown>
  compact_applied?: boolean
  process_trace?: DramaAgentProcessStep[]
  task_id?: string
  trace_id?: string
  suggested_next?: string[]
}

export const AGENT_MODE_SHORTCUTS: {
  mode: DramaAgentMode
  label: string
  icon: string
  gradient: string
  placeholder: string
}[] = [
  {
    mode: 'creative_short_drama',
    label: '创意短剧',
    icon: '🎬',
    gradient: 'linear-gradient(135deg,#ff6b9d 0%,#c44569 100%)',
    placeholder: '创意短剧 / 输入你的灵感，如重生复仇、豪门甜宠… AI 将帮你脑暴剧本与分镜',
  },
  {
    mode: 'aigc_manga',
    label: 'AIGC漫剧',
    icon: '📖',
    gradient: 'linear-gradient(135deg,#a18cd1 0%,#fbc2eb 100%)',
    placeholder: 'AIGC漫剧 / 描述条漫或动态漫创意，AI 将帮你梳理世界观、角色与分格脚本',
  },
  {
    mode: 'mv',
    label: 'MV',
    icon: '🎵',
    gradient: 'linear-gradient(135deg,#667eea 0%,#764ba2 100%)',
    placeholder: 'MV / 输入歌曲情绪或视觉概念，AI 将设计场景序列与镜头氛围',
  },
  {
    mode: 'marketing_ad',
    label: '营销广告',
    icon: '📣',
    gradient: 'linear-gradient(135deg,#43e97b 0%,#38f9d7 100%)',
    placeholder: '营销广告 / 输入产品与核心卖点，AI 将撰写秒级脚本与信息流分镜',
  },
]

export const AGENT_MODE_PLACEHOLDERS: Record<DramaAgentMode, string> = Object.fromEntries(
  AGENT_MODE_SHORTCUTS.map((s) => [s.mode, s.placeholder]),
) as Record<DramaAgentMode, string>

export function getAgentModeLabel(mode: DramaAgentMode): string {
  return AGENT_MODE_SHORTCUTS.find((s) => s.mode === mode)?.label ?? mode
}

export const STAGE_LABELS: Record<string, string> = {
  concept: '创意脑暴',
  outline: '大纲',
  script: '剧本',
  character: '角色',
  scene: '场景',
  storyboard: '分镜',
  production: '生产',
}

/** 创作助手阶段下拉（与后端 STAGE_SKILL_MAP 对齐，production 无 Skill） */
export const AGENT_STAGE_OPTIONS = [
  { value: 'concept', label: STAGE_LABELS.concept },
  { value: 'outline', label: STAGE_LABELS.outline },
  { value: 'script', label: STAGE_LABELS.script },
  { value: 'character', label: STAGE_LABELS.character },
  { value: 'scene', label: STAGE_LABELS.scene },
  { value: 'storyboard', label: STAGE_LABELS.storyboard },
  { value: 'production', label: STAGE_LABELS.production },
]
