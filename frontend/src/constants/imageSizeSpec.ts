/**
 * 图像模型官方尺寸标准（与 PROTOCOL_SPEC.md §2.3.1 同步）
 * 来源：GPT Image 2 OpenAI Images 兼容协议（Weelink / APIYi 聚合渠道）
 */
import type { ModelItem } from '@/types'

export type ImageClarity = '1k' | '2k' | '4k'
export type AspectRatioKey =
  | '1:1'
  | '3:2'
  | '2:3'
  | '4:3'
  | '3:4'
  | '5:4'
  | '4:5'
  | '16:9'
  | '9:16'
  | '2:1'
  | '1:2'
  | '3:1'
  | '1:3'
  | '21:9'
  | '9:21'

export interface RatioOption {
  key: AspectRatioKey
  w: number
  h: number
  label: string
}

export interface ImageSizePreset {
  aspectRatio: AspectRatioKey
  clarity: ImageClarity
  width: number
  height: number
  /** API size 字段（像素 WxH） */
  size: string
  /** API aspect_ratio 字段 */
  aspect_ratio: string
  /** API resolution 字段 */
  resolution: ImageClarity
}

export interface ImageModelSizeSpec {
  specId: string
  label: string
  /** 匹配的 model_code / channel_model_id 关键词（小写） */
  matchPatterns: string[]
  presets: ImageSizePreset[]
  supportsAutoRatio?: boolean
}

const preset = (
  aspectRatio: AspectRatioKey,
  clarity: ImageClarity,
  width: number,
  height: number,
): ImageSizePreset => ({
  aspectRatio,
  clarity,
  width,
  height,
  size: `${width}x${height}`,
  aspect_ratio: aspectRatio,
  resolution: clarity,
})

/** GPT Image 2 官方 size × resolution 像素映射表 */
const GPT_IMAGE_2_PRESETS: ImageSizePreset[] = [
  // 1:1
  preset('1:1', '1k', 1024, 1024),
  preset('1:1', '2k', 2048, 2048),
  preset('1:1', '4k', 2880, 2880),
  // 3:2
  preset('3:2', '1k', 1536, 1024),
  preset('3:2', '2k', 2048, 1360),
  preset('3:2', '4k', 3520, 2336),
  // 2:3
  preset('2:3', '1k', 1024, 1536),
  preset('2:3', '2k', 1360, 2048),
  preset('2:3', '4k', 2336, 3520),
  // 4:3
  preset('4:3', '1k', 1024, 768),
  preset('4:3', '2k', 2048, 1536),
  preset('4:3', '4k', 3312, 2480),
  // 3:4
  preset('3:4', '1k', 768, 1024),
  preset('3:4', '2k', 1536, 2048),
  preset('3:4', '4k', 2480, 3312),
  // 5:4
  preset('5:4', '1k', 1280, 1024),
  preset('5:4', '2k', 2560, 2048),
  preset('5:4', '4k', 3216, 2576),
  // 4:5
  preset('4:5', '1k', 1024, 1280),
  preset('4:5', '2k', 2048, 2560),
  preset('4:5', '4k', 2576, 3216),
  // 16:9
  preset('16:9', '1k', 1536, 864),
  preset('16:9', '2k', 2048, 1152),
  preset('16:9', '4k', 3840, 2160),
  // 9:16
  preset('9:16', '1k', 864, 1536),
  preset('9:16', '2k', 1152, 2048),
  preset('9:16', '4k', 2160, 3840),
  // 2:1
  preset('2:1', '1k', 2048, 1024),
  preset('2:1', '2k', 2688, 1344),
  preset('2:1', '4k', 3840, 1920),
  // 1:2
  preset('1:2', '1k', 1024, 2048),
  preset('1:2', '2k', 1344, 2688),
  preset('1:2', '4k', 1920, 3840),
  // 3:1
  preset('3:1', '1k', 1881, 836),
  preset('3:1', '2k', 3072, 1024),
  preset('3:1', '4k', 3840, 1280),
  // 1:3
  preset('1:3', '1k', 887, 1774),
  preset('1:3', '2k', 1024, 3072),
  preset('1:3', '4k', 1280, 3840),
  // 21:9
  preset('21:9', '1k', 2016, 864),
  preset('21:9', '2k', 2688, 1152),
  preset('21:9', '4k', 3840, 1648),
  // 9:21
  preset('9:21', '1k', 864, 2016),
  preset('9:21', '2k', 1152, 2688),
  preset('9:21', '4k', 1648, 3840),
]

/** DALL·E 3 官方固定尺寸（仅 1K 档） */
const DALL_E_3_PRESETS: ImageSizePreset[] = [
  preset('1:1', '1k', 1024, 1024),
  preset('9:16', '1k', 1024, 1792),
  preset('16:9', '1k', 1792, 1024),
]

export const IMAGE_MODEL_SIZE_SPECS: ImageModelSizeSpec[] = [
  {
    specId: 'gpt-image-2',
    label: 'GPT Image 2',
    matchPatterns: ['gpt-image-2', 'gpt-image', 'gpt_image'],
    presets: GPT_IMAGE_2_PRESETS,
    supportsAutoRatio: true,
  },
  {
    specId: 'dall-e-3',
    label: 'DALL·E 3',
    matchPatterns: ['dall-e-3', 'dalle-3', 'dall_e_3'],
    presets: DALL_E_3_PRESETS,
    supportsAutoRatio: false,
  },
]

const RATIO_META: Record<AspectRatioKey, { w: number; h: number }> = {
  '1:1': { w: 1, h: 1 },
  '3:2': { w: 3, h: 2 },
  '2:3': { w: 2, h: 3 },
  '4:3': { w: 4, h: 3 },
  '3:4': { w: 3, h: 4 },
  '5:4': { w: 5, h: 4 },
  '4:5': { w: 4, h: 5 },
  '16:9': { w: 16, h: 9 },
  '9:16': { w: 9, h: 16 },
  '2:1': { w: 2, h: 1 },
  '1:2': { w: 1, h: 2 },
  '3:1': { w: 3, h: 1 },
  '1:3': { w: 1, h: 3 },
  '21:9': { w: 21, h: 9 },
  '9:21': { w: 9, h: 21 },
}

export function getModelChannelId(model: ModelItem | null | undefined): string {
  if (!model) return ''
  const binding =
    model.channel_bindings?.find((b) => b.status === 'active') || model.channel_bindings?.[0]
  return (binding?.channel_model_id || model.model_code || '').toLowerCase()
}

export function resolveImageSizeSpec(model: ModelItem | null | undefined): ImageModelSizeSpec {
  const haystack = `${getModelChannelId(model)} ${model?.model_code || ''}`.toLowerCase()
  for (const spec of IMAGE_MODEL_SIZE_SPECS) {
    if (spec.matchPatterns.some((p) => haystack.includes(p))) {
      return spec
    }
  }
  return IMAGE_MODEL_SIZE_SPECS[0]
}

export function getSpecRatios(spec: ImageModelSizeSpec): AspectRatioKey[] {
  return [...new Set(spec.presets.map((p) => p.aspectRatio))]
}

export function getSpecClarities(spec: ImageModelSizeSpec): ImageClarity[] {
  return [...new Set(spec.presets.map((p) => p.clarity))] as ImageClarity[]
}

export function getRatiosForClarity(
  spec: ImageModelSizeSpec,
  clarity: ImageClarity,
): AspectRatioKey[] {
  return [
    ...new Set(spec.presets.filter((p) => p.clarity === clarity).map((p) => p.aspectRatio)),
  ]
}

export function getClaritiesForRatio(
  spec: ImageModelSizeSpec,
  ratio: AspectRatioKey,
): ImageClarity[] {
  return [
    ...new Set(spec.presets.filter((p) => p.aspectRatio === ratio).map((p) => p.clarity)),
  ] as ImageClarity[]
}

export function findPreset(
  spec: ImageModelSizeSpec,
  ratio: AspectRatioKey,
  clarity: ImageClarity,
): ImageSizePreset | undefined {
  return spec.presets.find((p) => p.aspectRatio === ratio && p.clarity === clarity)
}

export function findPresetBySize(
  spec: ImageModelSizeSpec,
  size: string,
): ImageSizePreset | undefined {
  const normalized = size.trim().toLowerCase()
  return spec.presets.find((p) => p.size === normalized)
}

export function resolveOfficialSize(
  spec: ImageModelSizeSpec,
  ratio: AspectRatioKey,
  clarity: ImageClarity,
): ImageSizePreset {
  const presetFound = findPreset(spec, ratio, clarity)
  if (presetFound) return presetFound
  const ratios = getRatiosForClarity(spec, clarity)
  const fallbackRatio = ratios[0] || getSpecRatios(spec)[0]
  const clarities = getClaritiesForRatio(spec, fallbackRatio)
  const fallbackClarity = clarities[0] || getSpecClarities(spec)[0]
  return findPreset(spec, fallbackRatio, fallbackClarity)!
}

export function clampSizeSelection(
  spec: ImageModelSizeSpec,
  ratio: AspectRatioKey | 'auto',
  clarity: ImageClarity,
): { ratio: AspectRatioKey; clarity: ImageClarity } {
  const ratios = getSpecRatios(spec)
  const clarities = getSpecClarities(spec)

  let nextRatio: AspectRatioKey =
    ratio !== 'auto' && ratios.includes(ratio) ? ratio : ratios[0]
  let nextClarity: ImageClarity = clarities.includes(clarity) ? clarity : clarities[0]

  if (!findPreset(spec, nextRatio, nextClarity)) {
    const forRatio = getClaritiesForRatio(spec, nextRatio)
    nextClarity = forRatio.includes(nextClarity) ? nextClarity : forRatio[0]
  }
  if (!findPreset(spec, nextRatio, nextClarity)) {
    const forClarity = getRatiosForClarity(spec, nextClarity)
    nextRatio = forClarity.includes(nextRatio) ? nextRatio : forClarity[0]
  }

  return { ratio: nextRatio, clarity: nextClarity }
}

export function toRatioOptions(spec: ImageModelSizeSpec, clarity?: ImageClarity): RatioOption[] {
  const ratioKeys = clarity ? getRatiosForClarity(spec, clarity) : getSpecRatios(spec)
  return ratioKeys.map((key) => ({
    key,
    ...RATIO_META[key],
    label: key,
  }))
}

export const CLARITY_LABELS: Record<ImageClarity, string> = {
  '1k': '1K',
  '2k': '2K',
  '4k': '4K',
}

export const CLARITY_HINTS: Record<ImageClarity, string> = {
  '1k': '日常首选，速度最快',
  '2k': '商用高清',
  '4k': '印刷/大屏（实验性）',
}

/** 构建提交给后端的尺寸参数 */
export function buildImageSizeParams(
  spec: ImageModelSizeSpec,
  ratio: AspectRatioKey,
  clarity: ImageClarity,
): Record<string, string> {
  const p = resolveOfficialSize(spec, ratio, clarity)
  const params: Record<string, string> = {
    size: p.size,
    aspect_ratio: p.aspect_ratio,
    resolution: p.resolution,
  }
  if (spec.specId === 'gpt-image-2') {
    params.resolution = p.resolution
  }
  return params
}
