/**
 * Body 入参配置 — 取值来源与配置值分离（与后端 body_param_resolver 对齐）
 */
import type { BodyParam } from '@/types'

export const BODY_PARAM_SOURCE = {
  LITERAL: 'literal',
  TASK_PARAM: 'task_param',
  BUILTIN: 'builtin',
  IMAGE_URLS: 'image_urls',
  CHAT_MESSAGES: 'chat_messages',
} as const

export type BodyParamSource = (typeof BODY_PARAM_SOURCE)[keyof typeof BODY_PARAM_SOURCE]

export const BODY_PARAM_SOURCE_LABELS: Record<BodyParamSource, string> = {
  literal: '固定值',
  task_param: '任务参数',
  builtin: '系统内置',
  image_urls: '图片 URL',
  chat_messages: '对话 messages',
}

export const BUILTIN_OPTIONS = [
  { value: 'channel_model_id', label: '渠道模型 ID（绑定 ep-xxx）' },
  { value: 'channel_code', label: '渠道编码' },
  { value: 'trace_id', label: '链路 trace_id' },
] as const

/** 协议槽位 → 推荐 body_params（空数组 = 走适配器 builder，勿配） */
export const BODY_PARAM_PRESETS: Record<
  string,
  { label: string; hint: string; params: BodyParam[] }
> = {
  'openai.chat.completions': {
    label: 'OpenAI 对话',
    hint: '标准 Chat Completions',
    params: [
      { key: 'model', source: 'builtin', builtin: 'channel_model_id' },
      { key: 'messages', source: 'chat_messages' },
      { key: 'stream', source: 'literal', literal: 'false' },
    ],
  },
  'openai.chat.image.text_to_image': {
    label: '对话式文生图',
    hint: '推荐留空，走 apiyi_chat_image builder；仅纯 ConfigEngine 渠道时使用',
    params: [
      { key: 'model', source: 'builtin', builtin: 'channel_model_id' },
      { key: 'messages', source: 'chat_messages' },
      { key: 'stream', source: 'literal', literal: 'false' },
    ],
  },
  'openai.chat.image.image_to_image': {
    label: '对话式图生图',
    hint: '推荐留空，走 apiyi_chat_image builder',
    params: [
      { key: 'model', source: 'builtin', builtin: 'channel_model_id' },
      { key: 'messages', source: 'chat_messages' },
      { key: 'stream', source: 'literal', literal: 'false' },
    ],
  },
  'openai.images.generations': {
    label: '文生图 generations',
    hint: 'OpenAI Images API 文生图',
    params: [
      { key: 'model', source: 'builtin', builtin: 'channel_model_id' },
      { key: 'prompt', source: 'task_param', param: 'prompt' },
      { key: 'size', source: 'task_param', param: 'size' },
      { key: 'n', source: 'literal', literal: '1' },
    ],
  },
  'openai.images.edits': {
    label: '图生图 edits',
    hint: 'multipart 时图片字段仍由适配器处理；此处映射文本字段',
    params: [
      { key: 'model', source: 'builtin', builtin: 'channel_model_id' },
      { key: 'prompt', source: 'task_param', param: 'prompt' },
      { key: 'size', source: 'task_param', param: 'size' },
    ],
  },
  'volcengine.video.multimodal': {
    label: '火山多模态视频',
    hint: '推荐留空走 volcengine_video_multimodal builder；若强制 ConfigEngine 用此模板',
    params: [
      { key: 'model', source: 'builtin', builtin: 'channel_model_id' },
      { key: 'content', source: 'task_param', param: 'content' },
      { key: 'ratio', source: 'task_param', param: 'ratio' },
      { key: 'duration', source: 'task_param', param: 'duration' },
      { key: 'generate_audio', source: 'task_param', param: 'audio' },
      { key: 'watermark', source: 'task_param', param: 'watermark' },
    ],
  },
}

export function getBodyParamPreset(protocolSlot?: string) {
  if (!protocolSlot) return undefined
  if (protocolSlot === 'openai.chat.image') {
    return BODY_PARAM_PRESETS['openai.chat.image.text_to_image']
  }
  return BODY_PARAM_PRESETS[protocolSlot]
}

/** 旧 value_type/value → 新 source 格式（表单展示用） */
export function normalizeBodyParam(bp: BodyParam): BodyParam {
  if (bp.source) return bp
  const key = bp.key?.trim()
  if (!key) return bp

  const vt = bp.value_type || 'dynamic'
  const val = bp.value || ''

  if (vt === 'fixed') {
    return { ...bp, source: 'literal', literal: val }
  }
  if (vt === 'image') {
    return { ...bp, source: 'image_urls', param: val || 'images' }
  }
  if (key === 'messages') {
    return { ...bp, source: 'chat_messages' }
  }
  if (val === 'channel_model_id' || (key === 'model' && (!val || val === 'model'))) {
    return { ...bp, source: 'builtin', builtin: 'channel_model_id' }
  }
  if (val === 'channel_code' || val === 'trace_id') {
    return { ...bp, source: 'builtin', builtin: val }
  }
  return { ...bp, source: 'task_param', param: val || key }
}

export function createEmptyBodyParam(): BodyParam {
  return { key: '', source: 'task_param', param: '' }
}
