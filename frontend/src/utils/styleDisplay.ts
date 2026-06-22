import type { DramaStylePreset } from '@/types/drama'
import { getStyleDescriptionExcerpt } from '@/utils/styleDescription'

export function getStyleSummary(style: DramaStylePreset): string {
  return getStyleDescriptionExcerpt(style)
}

export function getStyleReferenceFilms(style: DramaStylePreset): string[] {
  return style.visual?.reference_films || []
}

export function getStyleColorPalette(style: DramaStylePreset): string[] {
  return style.model_protocol?.visual?.color_palette || style.visual?.color_palette || []
}

/** 展示用标签：去掉比例/尺寸类（如 竖屏9:16） */
const SIZE_TAG_RE = /^(竖屏|横屏)?\d+\s*:\s*\d+$|^尺寸$|aspect/i

export function getStyleDisplayTags(style: DramaStylePreset, limit?: number): string[] {
  const raw = style.genre_tags?.length
    ? style.genre_tags
    : style.model_protocol?.trait_tags || []
  const tags = raw.filter((t) => t && !SIZE_TAG_RE.test(String(t).trim()))
  return limit != null ? tags.slice(0, limit) : tags
}
