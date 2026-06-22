import type { DramaRenderClass } from '@/types/drama'

export interface StyleModelProtocol {
  version: string
  render_class: DramaRenderClass
  trait_tags: string[]
  summary: { zh: string; en: string }
  image: { positive_en: string; negative_en: string; aspect_ratio?: string }
  video: { positive_en: string; negative_en: string; aspect_ratio?: string }
  character: { suffix_en: string }
  scene: { suffix_en: string }
  visual: { lighting: string; texture: string; color_palette: string[] }
  preview: { gradient: string; cover_asset_id?: string; cover_url?: string }
}

export function stylePreviewGradient(styleId: string): string {
  const gradients = [
    'linear-gradient(135deg,#667eea 0%,#764ba2 100%)',
    'linear-gradient(135deg,#f093fb 0%,#f5576c 100%)',
    'linear-gradient(135deg,#4facfe 0%,#00f2fe 100%)',
    'linear-gradient(135deg,#43e97b 0%,#38f9d7 100%)',
    'linear-gradient(135deg,#fa709a 0%,#fee140 100%)',
    'linear-gradient(135deg,#a18cd1 0%,#fbc2eb 100%)',
  ]
  let hash = 0
  for (let i = 0; i < styleId.length; i++) hash = (hash * 31 + styleId.charCodeAt(i)) >>> 0
  return gradients[hash % gradients.length]
}

export function resolveStylePreview(style: {
  style_id: string
  model_protocol?: StyleModelProtocol
}): { gradient: string; coverUrl?: string } {
  const mp = style.model_protocol?.preview
  return {
    gradient: mp?.gradient || stylePreviewGradient(style.style_id),
    coverUrl: mp?.cover_url,
  }
}
