import type { DramaStylePreset } from '@/types/drama'

/** v2 规范：视觉维度独立分节（与后端 style_description.py 一致） */
export const STYLE_DESCRIPTION_SECTIONS = [
  { key: 'summary', title: '风格摘要' },
  { key: 'category', title: '画风大类' },
  { key: 'artist_refs', title: '画师/工作室参考' },
  { key: 'era_texture', title: '年代质感' },
  { key: 'line_control', title: '线条与轮廓控制' },
  { key: 'lighting_color', title: '光影与色彩' },
  { key: 'palette_strategy', title: '配色搭配' },
  { key: 'atmosphere', title: '氛围气质' },
  { key: 'materials', title: '材质细节' },
  { key: 'quality', title: '画质要求' },
  { key: 'taboos', title: '约束禁忌' },
  { key: 'characters', title: '人物角色' },
  { key: 'scenes', title: '场景描述' },
  { key: 'colors', title: '色彩倾向' },
  { key: 'references', title: '代表作品' },
  { key: 'image_prompt', title: '生图提示词参考' },
  { key: 'video_prompt', title: '生视频提示词参考' },
] as const

const TITLE_TO_KEY: Record<string, string> = {
  ...Object.fromEntries(STYLE_DESCRIPTION_SECTIONS.map((s) => [s.title, s.key])),
  风格特点: 'traits', // 旧版兼容
}

const SECTION_HINTS: Record<string, string> = {
  summary: '2–4 句概括美学定位、叙事气质、适用场景与 AI 出图/出视频要点。',
  category: '如：二维赛璐璐动画 / 真人电影摄影 / 三维风格化渲染。',
  artist_refs: '具体画师、摄影指导、工作室或参考 IP 美术方向。',
  era_texture: '年代、媒介、颗粒/印刷/胶片/数字渲染质感。',
  line_control: '勾线粗细、轮廓策略、silhouette 与内外线关系。',
  lighting_color: '主光方向、光比、色温、阴影层级、LUT 倾向。',
  palette_strategy: '主色/辅色/点缀色组织原则与叙事用色。',
  atmosphere: '情绪基调、空气透视、天气与叙事张力。',
  materials: '皮肤/布料/金属/环境材质的可执行描述。',
  quality: '分辨率、锐度、完成度、平台画幅（9:16 等）。',
  taboos: '须规避的错误美学（如 3D 写实、错误比例等）。',
  characters: '中文造型要点 + 空行 + English character prompt fragment。',
  scenes: '中文场景构图要点 + 空行 + English scene prompt fragment。',
  colors: '主色与辅助色，可逗号或换行分隔。',
  references: '每行一部参考作品，可带年份。',
  image_prompt: 'English positive prompt for image models (40–80 words).',
  video_prompt: 'English positive prompt for video models (20–40 words).',
}

export function buildStyleDescriptionTemplate(name = ''): string {
  const head = name ? `# ${name}\n\n` : ''
  const blocks = STYLE_DESCRIPTION_SECTIONS.map(
    ({ key, title }) => `## ${title}\n\n${SECTION_HINTS[key] || ''}\n`,
  )
  return `${head}${blocks.join('\n')}`.trim() + '\n'
}

export function parseStyleDescriptionMd(text: string): Record<string, string> {
  if (!text?.trim()) return {}
  const sections: Record<string, string> = {}
  let currentKey: string | null = null
  let currentLines: string[] = []

  for (const line of text.split('\n')) {
    const stripped = line.trim()
    let matchedKey: string | null = null
    if (stripped.startsWith('##')) {
      const heading = stripped.replace(/^#+\s*/, '')
      matchedKey = TITLE_TO_KEY[heading] ?? null
    }
    if (matchedKey) {
      if (currentKey) sections[currentKey] = currentLines.join('\n').trim()
      currentKey = matchedKey
      currentLines = []
    } else if (currentKey) {
      currentLines.push(line)
    }
  }
  if (currentKey) sections[currentKey] = currentLines.join('\n').trim()
  return sections
}

export function legacyStyleToDescriptionMd(style: {
  name?: string
  style_description_md?: string
  model_prompts?: Record<string, string>
  visual?: {
    reference_films?: string[]
    color_palette?: string[]
  }
}): string {
  if (style.style_description_md?.trim()) return style.style_description_md.trim()

  const mp = style.model_prompts || {}
  const visual = style.visual || {}
  const blocks: string[] = []
  if (style.name) blocks.push(`# ${style.name}\n`)

  const content: Record<string, string> = {
    summary: mp.style_summary_zh || '',
    category: '',
    artist_refs: '',
    era_texture: '',
    line_control: '',
    lighting_color: '',
    palette_strategy: '',
    atmosphere: '',
    materials: '',
    quality: '',
    taboos: '',
    characters: mp.character_suffix_en || '',
    scenes: mp.scene_suffix_en || '',
    colors: (visual.color_palette || []).join(', '),
    references: (visual.reference_films || []).join('\n'),
    image_prompt: mp.image_positive_en || '',
    video_prompt: mp.video_positive_en || '',
  }

  for (const { key, title } of STYLE_DESCRIPTION_SECTIONS) {
    blocks.push(`## ${title}\n\n${content[key] || ''}\n`)
  }
  return blocks.join('\n').trim() + '\n'
}

export function getStyleDescriptionExcerpt(style: DramaStylePreset, maxLen = 120): string {
  if (style.style_description_md?.trim()) {
    const sections = parseStyleDescriptionMd(style.style_description_md)
    const summary = sections.summary || style.style_description_md.replace(/^#+\s.*$/gm, '').trim()
    return summary.length > maxLen ? `${summary.slice(0, maxLen)}…` : summary
  }
  return (
    style.model_protocol?.summary?.zh ||
    style.model_prompts?.style_summary_zh ||
    style.description ||
    ''
  )
}
