import type { CanvasNodeConfig } from '@/types/canvas'

export interface CharacterImageTask {
  task_id: string
  character_name?: string
  scene_id?: string
  scene_name?: string
  grid_id?: string
  chapter_id?: string
  shot_number?: string
  label?: string
  aspect_ratio?: string
  prompt_ref?: string
  negative_en?: string
  video_negative_en?: string
  duration_sec?: number
  image_count?: number
  width?: number
  height?: number
  prompt_markdown: string
  /** 画布节点类型：prod_video 等走 video 节点 */
  node_type?: 'image' | 'video'
}

const FENCE_PATTERN = /```([\w-]+)\s*\n([\s\S]*?)```/g

function extractFencedBlocks(content: string): Record<string, string> {
  const out: Record<string, string> = {}
  let match: RegExpExecArray | null
  while ((match = FENCE_PATTERN.exec(content)) !== null) {
    const lang = (match[1] || '').trim().toLowerCase()
    const body = (match[2] || '').trim()
    if (lang && body) out[lang] = body
  }
  return out
}

function parseRawTasks(raw: string): Array<Record<string, unknown>> {
  const text = (raw || '').trim()
  if (!text) return []
  const data = JSON.parse(text)
  if (Array.isArray(data)) return data as Array<Record<string, unknown>>
  if (data && typeof data === 'object') {
    const tasks = (data as { tasks?: unknown }).tasks
    if (Array.isArray(tasks)) return tasks as Array<Record<string, unknown>>
    return [data as Record<string, unknown>]
  }
  return []
}

function resolvePrompt(task: Record<string, unknown>, prompts: Record<string, string>): string {
  const ref = String(task.prompt_ref || '').trim().toLowerCase()
  if (ref && prompts[ref]) return prompts[ref]
  const taskId = String(task.task_id || '').trim().toLowerCase()
  if (taskId === 'look' && prompts['look-prompt']) return prompts['look-prompt']
  if (taskId === 'card' && prompts['card-prompt']) return prompts['card-prompt']
  if (taskId === 'scene_master' && prompts['scene-prompt']) return prompts['scene-prompt']
  if (taskId === 'scene_grid_6' && prompts['scene-grid-prompt']) return prompts['scene-grid-prompt']
  if (taskId === 'prod_image' && prompts['image-prompt']) return prompts['image-prompt']
  if (taskId === 'prod_video' && prompts['video-prompt']) return prompts['video-prompt']
  return String(task.positive_en || '').trim()
}

function mapRawTasksToImageTasks(
  parsed: Array<Record<string, unknown>>,
  prompts: Record<string, string>,
): CharacterImageTask[] {
  return parsed
    .map((item) => {
      const prompt = resolvePrompt(item, prompts)
      if (!prompt) return null
      const taskId = String(item.task_id || item.task || '').trim().toLowerCase()
      if (!taskId) return null
      const durationRaw = Number(item.duration_sec)
      const duration_sec =
        Number.isFinite(durationRaw) && durationRaw > 0 ? Math.floor(durationRaw) : undefined
      const node_type: 'image' | 'video' | undefined =
        taskId === 'prod_video' ? 'video' : taskId === 'prod_image' ? 'image' : undefined
      return {
        task_id: taskId,
        character_name: String(item.character_name || '').trim() || undefined,
        scene_id: String(item.scene_id || '').trim() || undefined,
        scene_name: String(item.scene_name || '').trim() || undefined,
        grid_id: String(item.grid_id || '').trim() || undefined,
        chapter_id: String(item.chapter_id || '').trim() || undefined,
        shot_number: String(item.shot_number || '').trim() || undefined,
        label: String(item.label || '').trim() || undefined,
        aspect_ratio: String(item.aspect_ratio || '').trim() || undefined,
        prompt_ref: String(item.prompt_ref || '').trim() || undefined,
        negative_en: String(item.negative_en || '').trim() || undefined,
        video_negative_en: String(item.video_negative_en || '').trim() || undefined,
        duration_sec,
        image_count: parsePositiveInt(item.image_count),
        width: parsePositiveInt(item.width),
        height: parsePositiveInt(item.height),
        prompt_markdown: prompt,
        node_type,
      } as CharacterImageTask
    })
    .filter((x): x is CharacterImageTask => Boolean(x))
}

function parsePositiveInt(value: unknown): number | undefined {
  const n = Number(value)
  if (!Number.isFinite(n) || n <= 0) return undefined
  return Math.floor(n)
}

export function parseCharacterImageTasksFromReply(content: string): CharacterImageTask[] {
  const blocks = extractFencedBlocks(content || '')
  const prompts: Record<string, string> = {}
  if (blocks['look-prompt']) prompts['look-prompt'] = blocks['look-prompt']
  if (blocks['card-prompt']) prompts['card-prompt'] = blocks['card-prompt']
  const rawTasks = blocks['character-image-tasks']
  if (!rawTasks) return []

  try {
    return mapRawTasksToImageTasks(parseRawTasks(rawTasks), prompts)
  } catch {
    return []
  }
}

export function parseSceneImageTasksFromReply(content: string): CharacterImageTask[] {
  const blocks = extractFencedBlocks(content || '')
  const prompts: Record<string, string> = {}
  if (blocks['scene-prompt']) prompts['scene-prompt'] = blocks['scene-prompt']
  if (blocks['scene-grid-prompt']) prompts['scene-grid-prompt'] = blocks['scene-grid-prompt']
  const rawTasks = blocks['scene-image-tasks']
  if (!rawTasks) return []

  try {
    return mapRawTasksToImageTasks(parseRawTasks(rawTasks), prompts)
  } catch {
    return []
  }
}

export function parseProductionTasksFromReply(content: string): CharacterImageTask[] {
  const blocks = extractFencedBlocks(content || '')
  const prompts: Record<string, string> = {}
  if (blocks['image-prompt']) prompts['image-prompt'] = blocks['image-prompt']
  if (blocks['video-prompt']) prompts['video-prompt'] = blocks['video-prompt']
  const rawTasks = blocks['production-tasks']
  if (!rawTasks) return []

  try {
    return mapRawTasksToImageTasks(parseRawTasks(rawTasks), prompts)
  } catch {
    return []
  }
}

/** 按创作阶段解析助手回复中的一键出图任务块 */
export function parseAgentImageTasksFromReply(content: string, stage?: string): CharacterImageTask[] {
  if (stage === 'production') {
    const prodTasks = parseProductionTasksFromReply(content)
    if (prodTasks.length) return prodTasks
  }
  if (stage === 'scene') {
    const sceneTasks = parseSceneImageTasksFromReply(content)
    if (sceneTasks.length) return sceneTasks
  }
  return parseCharacterImageTasksFromReply(content)
}

export function characterImageTaskButtonLabel(task: CharacterImageTask): string {
  if (task.label) return task.label
  if (task.task_id === 'look') return '定妆图生图'
  if (task.task_id === 'card') return '角色卡生图'
  if (task.task_id === 'scene_master') return task.scene_name ? `${task.scene_name}·场景主图` : '场景主图生图'
  if (task.task_id === 'scene_grid_6') return task.scene_name ? `${task.scene_name}·六宫格` : '场景六宫格生图'
  if (task.task_id === 'prod_image') return task.label || (task.grid_id ? `${task.grid_id}·生图` : '生产生图')
  if (task.task_id === 'prod_video') return task.label || (task.grid_id ? `${task.grid_id}·生视频` : '生产生视频')
  return '一键生图'
}

export function buildVideoNodeConfigFromTask(
  task: CharacterImageTask,
  opts: {
    modelCode?: string
    stylePresetId?: string
    stylePresetName?: string
    width?: number
    height?: number
  },
): CanvasNodeConfig {
  const params: Record<string, unknown> = {}
  if (task.aspect_ratio) params.aspect_ratio = task.aspect_ratio
  const neg = task.video_negative_en || task.negative_en
  if (neg) params.negative_prompt = neg
  if (task.duration_sec) params.duration = Math.min(15, Math.max(2, task.duration_sec))
  const def = { width: 320, height: 240 }
  return {
    prompt: task.prompt_markdown,
    model_code: opts.modelCode,
    style_preset_id: opts.stylePresetId,
    style_preset_name: opts.stylePresetName,
    params,
    width: task.width ?? opts.width ?? def.width,
    height: task.height ?? opts.height ?? def.height,
  }
}

export function buildImageNodeConfigFromTask(
  task: CharacterImageTask,
  opts: {
    modelCode?: string
    stylePresetId?: string
    stylePresetName?: string
    width?: number
    height?: number
  },
): CanvasNodeConfig {
  const params: Record<string, unknown> = {}
  if (task.aspect_ratio) params.aspect_ratio = task.aspect_ratio
  if (task.negative_en) params.negative_prompt = task.negative_en
  if (task.image_count) params.n = Math.min(4, Math.max(1, task.image_count))
  const def = { width: 280, height: 320 }
  return {
    prompt: task.prompt_markdown,
    model_code: opts.modelCode,
    style_preset_id: opts.stylePresetId,
    style_preset_name: opts.stylePresetName,
    params,
    width: task.width ?? opts.width ?? def.width,
    height: task.height ?? opts.height ?? def.height,
  }
}

export function resolveAgentTaskNodeType(task: CharacterImageTask): 'image' | 'video' {
  if (task.node_type === 'video' || task.task_id === 'prod_video') return 'video'
  return 'image'
}

export function buildCanvasNodeConfigFromAgentTask(
  task: CharacterImageTask,
  opts: {
    modelCode?: string
    stylePresetId?: string
    stylePresetName?: string
    width?: number
    height?: number
  },
): CanvasNodeConfig {
  if (resolveAgentTaskNodeType(task) === 'video') {
    return buildVideoNodeConfigFromTask(task, opts)
  }
  return buildImageNodeConfigFromTask(task, opts)
}
