import type { DramaAgentMessage, DramaAgentMode } from '@/types/dramaAgent'

export type DramaAgentScrollSurface = 'panel' | 'page'

export interface DramaAgentThreadSession {
  threadId: string
  canvasProjectId?: string
  messages: DramaAgentMessage[]
  agentMode: DramaAgentMode
  modelCode?: string
  stylePresetId?: string
  multiEpisode: boolean
  stage: string
  suggestedNext: string[]
  threadTitle?: string
  scrollTop: Partial<Record<DramaAgentScrollSurface, number>>
  lastMessageId?: string
  updatedAt: number
}

const sessions = new Map<string, DramaAgentThreadSession>()
const canvasToThread = new Map<string, string>()
/** 同步滚动快照，不依赖 session 是否已建立 */
const liveScrollTop = new Map<string, number>()

function scrollKey(threadId: string, surface: DramaAgentScrollSurface) {
  return `${threadId}:${surface}`
}

function fingerprint(messages: DramaAgentMessage[]): string {
  if (!messages.length) return '0'
  const last = messages[messages.length - 1]
  return `${messages.length}:${last.message_id}`
}

export function getThreadSession(threadId: string): DramaAgentThreadSession | undefined {
  return sessions.get(threadId)
}

export function getSessionByCanvas(canvasProjectId: string): DramaAgentThreadSession | undefined {
  const tid = canvasToThread.get(canvasProjectId)
  return tid ? sessions.get(tid) : undefined
}

export function bindCanvasThread(canvasProjectId: string, threadId: string) {
  canvasToThread.set(canvasProjectId, threadId)
  const existing = sessions.get(threadId)
  if (existing) {
    sessions.set(threadId, { ...existing, canvasProjectId, updatedAt: Date.now() })
  }
}

export function upsertThreadSession(
  threadId: string,
  patch: Partial<Omit<DramaAgentThreadSession, 'threadId' | 'updatedAt'>> & {
    threadId?: string
  },
): DramaAgentThreadSession {
  const prev = sessions.get(threadId)
  const messages = patch.messages ?? prev?.messages ?? []
  const next: DramaAgentThreadSession = {
    threadId,
    canvasProjectId: patch.canvasProjectId ?? prev?.canvasProjectId,
    messages,
    agentMode: patch.agentMode ?? prev?.agentMode ?? 'creative_short_drama',
    modelCode: patch.modelCode ?? prev?.modelCode,
    stylePresetId: 'stylePresetId' in patch ? patch.stylePresetId : prev?.stylePresetId,
    multiEpisode: patch.multiEpisode ?? prev?.multiEpisode ?? false,
    stage: patch.stage ?? prev?.stage ?? 'concept',
    suggestedNext: patch.suggestedNext ?? prev?.suggestedNext ?? [],
    threadTitle: patch.threadTitle ?? prev?.threadTitle,
    scrollTop: { ...(prev?.scrollTop ?? {}), ...(patch.scrollTop ?? {}) },
    lastMessageId: messages.length ? messages[messages.length - 1].message_id : prev?.lastMessageId,
    updatedAt: Date.now(),
  }
  sessions.set(threadId, next)
  if (next.canvasProjectId) {
    canvasToThread.set(next.canvasProjectId, threadId)
  }
  return next
}

export function messagesChanged(
  prev: DramaAgentMessage[] | undefined,
  next: DramaAgentMessage[],
): boolean {
  return fingerprint(prev ?? []) !== fingerprint(next)
}

export function saveScrollTop(
  threadId: string,
  surface: DramaAgentScrollSurface,
  scrollTop: number,
) {
  liveScrollTop.set(scrollKey(threadId, surface), scrollTop)
  const prev = sessions.get(threadId)
  if (!prev) {
    upsertThreadSession(threadId, { scrollTop: { [surface]: scrollTop } })
    return
  }
  sessions.set(threadId, {
    ...prev,
    scrollTop: { ...prev.scrollTop, [surface]: scrollTop },
    updatedAt: Date.now(),
  })
}

export function getScrollTop(
  threadId: string,
  surface: DramaAgentScrollSurface,
): number | undefined {
  const live = liveScrollTop.get(scrollKey(threadId, surface))
  if (live != null) return live
  return sessions.get(threadId)?.scrollTop[surface]
}
