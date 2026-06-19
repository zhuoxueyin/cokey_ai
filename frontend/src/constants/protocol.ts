/** 协议槽位预设 — 渠道端点快速添加 */
export const VOLCENGINE_VIDEO_MULTIMODAL_SLOT = 'volcengine.video.multimodal'

export const VOLCENGINE_VIDEO_MODALITIES = ['text', 'image', 'video', 'audio'] as const

/** 对话式生图（Chat Completions）— 文生图 / 图生图分槽 */
export const OPENAI_CHAT_IMAGE_TEXT_TO_IMAGE_SLOT = 'openai.chat.image.text_to_image'
export const OPENAI_CHAT_IMAGE_IMAGE_TO_IMAGE_SLOT = 'openai.chat.image.image_to_image'
/** @deprecated 兼容旧配置，等同于文生图槽位 */
export const OPENAI_CHAT_IMAGE_LEGACY_SLOT = 'openai.chat.image'

export const PROTOCOL_SLOT_PRESETS = [
  {
    protocol_slot: 'openai.chat.completions',
    type: 'chat',
    endpoint: 'chat/completions',
    method: 'POST',
    content_type: 'application/json',
    label: 'OpenAI 对话',
  },
  {
    protocol_slot: OPENAI_CHAT_IMAGE_TEXT_TO_IMAGE_SLOT,
    type: 'chat',
    endpoint: 'chat/completions',
    method: 'POST',
    content_type: 'application/json',
    label: '对话式文生图',
  },
  {
    protocol_slot: OPENAI_CHAT_IMAGE_IMAGE_TO_IMAGE_SLOT,
    type: 'chat',
    endpoint: 'chat/completions',
    method: 'POST',
    content_type: 'application/json',
    label: '对话式图生图',
  },
  {
    protocol_slot: 'openai.images.generations',
    type: 'image',
    endpoint: 'images/generations',
    method: 'POST',
    content_type: 'application/json',
    label: '文生图 generations',
  },
  {
    protocol_slot: 'openai.images.edits',
    type: 'image_edits',
    endpoint: 'images/edits',
    method: 'POST',
    content_type: 'multipart/form-data',
    label: '图生图 edits',
  },
  {
    protocol_slot: VOLCENGINE_VIDEO_MULTIMODAL_SLOT,
    type: 'video',
    endpoint: 'contents/generations/tasks',
    method: 'POST',
    content_type: 'application/json',
    label: '火山 多模态视频（文/图/视频/音频）',
    modalities: [...VOLCENGINE_VIDEO_MODALITIES],
  },
] as const

/** 旧槽位 openai.chat.image → 文生图预设（表单联动用） */
export function normalizeChatImageProtocolSlot(protocolSlot?: string): string | undefined {
  if (!protocolSlot) return undefined
  if (protocolSlot === OPENAI_CHAT_IMAGE_LEGACY_SLOT) {
    return OPENAI_CHAT_IMAGE_TEXT_TO_IMAGE_SLOT
  }
  return protocolSlot
}

/** 协议槽位 → 预设（含联动的 type / path 等） */
export function getPresetByProtocolSlot(protocolSlot?: string) {
  if (!protocolSlot) return undefined
  const normalized =
    protocolSlot === 'volcengine.video.task'
      ? VOLCENGINE_VIDEO_MULTIMODAL_SLOT
      : normalizeChatImageProtocolSlot(protocolSlot) ?? protocolSlot
  return PROTOCOL_SLOT_PRESETS.find((p) => p.protocol_slot === normalized)
}

/**
 * 协议槽位 vs 类型（endpoint_type）
 * - protocol_slot：语义层，「哪套 API 契约」（可跨渠道复用）
 * - type：运行层，适配器在渠道 endpoints[] 里查找配置的键
 * 火山视频：统一用 volcengine.video.multimodal + type=video（不再区分 video_image）
 */
export const PROTOCOL_SLOT_TYPE_HINT =
  '协议槽位描述 API 契约；类型是系统查找端点配置的兼容键。选择预设槽位后，类型/路径/方法会自动联动填充。'

export const INVOCATION_MODE_LABELS: Record<string, string> = {
  text_chat: '生文',
  text_to_image: '文生图',
  image_to_image: '图生图',
  text_to_video: '文生视频',
  image_to_video: '图生视频',
}
