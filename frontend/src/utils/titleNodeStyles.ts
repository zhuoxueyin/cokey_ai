import type { CSSProperties } from 'react'
import type { CanvasNodeConfig } from '@/types/canvas'

export const TITLE_FONT_SIZE_MIN = 14
export const TITLE_FONT_SIZE_MAX = 40
export const TITLE_FONT_SIZE_DEFAULT = 26

const SIZE_BY_LEVEL: Record<number, number> = {
  1: 32,
  2: 26,
  3: 22,
  4: 18,
  5: 15,
}

export const FONT_FAMILY_MAP: Record<NonNullable<CanvasNodeConfig['font_family']>, string> = {
  system: 'inherit',
  sans: '"PingFang SC", "Microsoft YaHei", "Helvetica Neue", sans-serif',
  serif: '"Noto Serif SC", "Songti SC", Georgia, serif',
  mono: '"JetBrains Mono", "Consolas", monospace',
}

export const FONT_OPTIONS: { value: NonNullable<CanvasNodeConfig['font_family']>; label: string }[] = [
  { value: 'system', label: '默认' },
  { value: 'sans', label: '黑体' },
  { value: 'serif', label: '宋体' },
  { value: 'mono', label: '等宽' },
]

export function clampToTwoLines(text: string): string {
  const lines = text.split('\n')
  if (lines.length <= 2) return text
  return lines.slice(0, 2).join('\n')
}

export function resolveTitleContent(config: CanvasNodeConfig): string {
  return config.content?.trim() ? config.content : '标题'
}

export function resolveTitleFontSize(config: CanvasNodeConfig): number {
  if (typeof config.title_font_size === 'number' && Number.isFinite(config.title_font_size)) {
    return Math.min(TITLE_FONT_SIZE_MAX, Math.max(TITLE_FONT_SIZE_MIN, Math.round(config.title_font_size)))
  }
  const level = config.heading_level ?? 2
  return SIZE_BY_LEVEL[level] ?? TITLE_FONT_SIZE_DEFAULT
}

export function titleFontWeight(fontSize: number): number {
  if (fontSize >= 30) return 700
  if (fontSize >= 22) return 600
  return 500
}

export function titleTextStyle(config: CanvasNodeConfig): CSSProperties {
  const fontSize = resolveTitleFontSize(config)
  return {
    color: config.color || '#ffffff',
    fontFamily: FONT_FAMILY_MAP[config.font_family || 'sans'] || FONT_FAMILY_MAP.sans,
    fontSize,
    fontWeight: titleFontWeight(fontSize),
    lineHeight: 1.25,
  }
}

export function buildTitleRenderKey(config: CanvasNodeConfig): string {
  return [
    config.content ?? '',
    config.title_font_size ?? '',
    config.heading_level ?? '',
    config.color ?? '',
    config.font_family ?? '',
  ].join('|')
}
