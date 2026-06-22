/** 接入工单 — 选项与内置协议画像 */

export const INVOCATION_MODES = [
  { value: 'text_chat', label: '生文 (text_chat)', category: 'text' },
  { value: 'text_to_image', label: '文生图 (text_to_image)', category: 'image' },
  { value: 'image_to_image', label: '图生图 (image_to_image)', category: 'image' },
  { value: 'text_to_video', label: '文生视频 (text_to_video)', category: 'video' },
  { value: 'image_to_video', label: '图生视频 (image_to_video)', category: 'video' },
] as const

export const CATEGORY_OPTIONS = [
  { value: 'text', label: '文本 text' },
  { value: 'image', label: '图片 image' },
  { value: 'video', label: '视频 video' },
]

export const CHANNEL_PROVIDER_OPTIONS = [
  { value: 'apiyi', label: 'APIYi (聚合)' },
  { value: 'weelinking', label: 'Weelinking (聚合)' },
  { value: 'volcengine', label: '火山引擎 (直连)' },
]

export const BUILDER_OPTIONS = [
  { value: 'apiyi_chat_image', label: 'apiyi_chat_image' },
  { value: 'apiyi_vip_generations', label: 'apiyi_vip_generations' },
  { value: 'weelink_default', label: 'weelink_default' },
  { value: 'volcengine_video_multimodal', label: 'volcengine_video_multimodal（火山多模态视频）' },
  { value: 'config_engine', label: 'config_engine' },
  { value: 'custom', label: '新插件（需开发）' },
]

export const PARSER_OPTIONS = [
  { value: 'markdown_image', label: 'markdown_image' },
  { value: 'openai_images', label: 'openai_images' },
  { value: 'weelink_default', label: 'weelink_default' },
  { value: 'config_engine', label: 'config_engine' },
]

export const SIZE_STRATEGY_OPTIONS = [
  { value: 'api_field', label: 'api_field（写入 size 字段）' },
  { value: 'prompt_hint', label: 'prompt_hint（写入 prompt）' },
  { value: 'none', label: 'none（不传尺寸）' },
]

/** 内置协议画像 — 绑定下拉可快速选用 */
export const BUILTIN_PROFILE_OPTIONS = [
  { value: 'apiyi.gpt-image-2-all.text_to_image', label: 'APIYI all 文生图', mode: 'text_to_image', provider: 'apiyi', protocol_slot: 'openai.chat.image.text_to_image', endpoint_type: 'chat' },
  { value: 'apiyi.gpt-image-2-all.image_to_image', label: 'APIYI all 图生图', mode: 'image_to_image', provider: 'apiyi', protocol_slot: 'openai.chat.image.image_to_image', endpoint_type: 'chat' },
  { value: 'apiyi.gpt-image-2-vip.text_to_image', label: 'APIYI vip 文生图', mode: 'text_to_image', provider: 'apiyi', protocol_slot: 'openai.chat.image.text_to_image', endpoint_type: 'chat' },
  { value: 'apiyi.gpt-image-2-vip.image_to_image', label: 'APIYI vip 图生图', mode: 'image_to_image', provider: 'apiyi', protocol_slot: 'openai.chat.image.image_to_image', endpoint_type: 'chat' },
  { value: 'apiyi.gemini.chat.text_to_image', label: 'APIYI Gemini/Banana 文生图', mode: 'text_to_image', provider: 'apiyi', protocol_slot: 'openai.chat.image.text_to_image', endpoint_type: 'chat' },
  { value: 'apiyi.gemini.chat.image_to_image', label: 'APIYI Gemini/Banana 图生图', mode: 'image_to_image', provider: 'apiyi', protocol_slot: 'openai.chat.image.image_to_image', endpoint_type: 'chat' },
  { value: 'weelinking.openai-image.text_to_image', label: 'Weelink 文生图', mode: 'text_to_image', provider: 'weelinking', protocol_slot: 'openai.images.generations', endpoint_type: 'image' },
  { value: 'weelinking.openai-image.image_to_image', label: 'Weelink 图生图', mode: 'image_to_image', provider: 'weelinking', protocol_slot: 'openai.images.edits', endpoint_type: 'image_edits' },
  { value: 'openai.chat.text_chat', label: 'OpenAI 生文', mode: 'text_chat', provider: '*' },
  { value: 'volcengine.video.text_to_video', label: '火山 多模态视频（文/混合）', mode: 'text_to_video', provider: 'volcengine', protocol_slot: 'volcengine.video.multimodal', endpoint_type: 'video' },
  { value: 'volcengine.video.image_to_video', label: '火山 多模态视频（含参考素材）', mode: 'image_to_video', provider: 'volcengine', protocol_slot: 'volcengine.video.multimodal', endpoint_type: 'video' },
]

export const DEFAULT_ENDPOINTS_BY_MODE: Record<string, { protocol_slot: string; type: string; endpoint: string; content_type: string }> = {
  text_chat: { protocol_slot: 'openai.chat.completions', type: 'chat', endpoint: 'chat/completions', content_type: 'application/json' },
  text_to_image: { protocol_slot: 'openai.images.generations', type: 'image', endpoint: 'images/generations', content_type: 'application/json' },
  image_to_image: { protocol_slot: 'openai.images.edits', type: 'image_edits', endpoint: 'images/edits', content_type: 'multipart/form-data' },
  text_to_video: { protocol_slot: 'volcengine.video.multimodal', type: 'video', endpoint: 'contents/generations/tasks', content_type: 'application/json' },
  image_to_video: { protocol_slot: 'volcengine.video.multimodal', type: 'video', endpoint: 'contents/generations/tasks', content_type: 'application/json' },
}
