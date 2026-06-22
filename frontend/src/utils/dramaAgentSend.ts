import { agentThreadChat, listAgentMessages } from '@/api/dramaAgent'
import type { DramaAgentChatResult, DramaAgentMessage, DramaAgentRef } from '@/types/dramaAgent'

/** 发送瞬间插入的用户消息（待服务端列表回填后替换） */
export function buildOptimisticUserMessage(
  threadId: string,
  content: string,
  refs: DramaAgentRef[],
): DramaAgentMessage {
  const now = new Date().toISOString()
  const id = `pending_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
  return {
    id,
    message_id: id,
    thread_id: threadId,
    role: 'user',
    content,
    refs: refs.map((r) => ({ ...r })),
    created_at: now,
  }
}

export function isPendingAgentMessage(msg: DramaAgentMessage): boolean {
  return msg.message_id.startsWith('pending_')
}

/** 路由 hydrate 时避免用空列表或截断列表覆盖较新的本地消息 */
export function mergeAgentMessageList(
  current: DramaAgentMessage[],
  server: DramaAgentMessage[],
): DramaAgentMessage[] {
  if (!server.length && current.some(isPendingAgentMessage)) {
    return current
  }
  if (!server.length) return current

  const serverLast = server[server.length - 1]
  const currentLast = current[current.length - 1]
  const serverNewer =
    serverLast?.created_at &&
    currentLast?.created_at &&
    serverLast.created_at >= currentLast.created_at

  if (server.length >= current.length && (serverNewer || !currentLast?.created_at)) {
    return server
  }
  if (!current.some(isPendingAgentMessage)) {
    return server.length > current.length ? server : current
  }
  return current
}

const chatInflightKeys = new Set<string>()

export function chatInflightKey(threadId: string | null): string {
  return threadId ?? '__pending_thread__'
}

export function tryAcquireChatInflight(key: string): boolean {
  if (chatInflightKeys.has(key)) return false
  chatInflightKeys.add(key)
  return true
}

export function releaseChatInflight(key: string) {
  chatInflightKeys.delete(key)
}

/** 优先用 chat 响应里的 assistant 消息更新 UI，再与全量列表合并 */
export function applyChatResultToMessages(
  prev: DramaAgentMessage[],
  optimistic: DramaAgentMessage,
  data: DramaAgentChatResult,
  serverList?: DramaAgentMessage[],
): DramaAgentMessage[] {
  const base = prev.filter((m) => m.message_id !== optimistic.message_id)
  const assistant = data.message

  if (serverList?.length) {
    let merged = mergeAgentMessageList(base, serverList)
    if (assistant?.message_id && !merged.some((m) => m.message_id === assistant.message_id)) {
      merged = [...merged, assistant]
    }
    return merged
  }
  if (assistant?.message_id) {
    const exists = base.some((m) => m.message_id === assistant.message_id)
    return exists ? base : [...base, assistant]
  }
  return base
}

export async function fetchAgentMessages(threadId: string): Promise<DramaAgentMessage[]> {
  const hist = await listAgentMessages(threadId, 200)
  return (hist.data as DramaAgentMessage[]) || []
}

/** 请求失败时从服务端拉取真实消息（用户消息可能已落库） */
export async function recoverMessagesAfterChatFailure(
  threadId: string | null,
  prev: DramaAgentMessage[],
  optimisticId: string,
): Promise<DramaAgentMessage[]> {
  if (!threadId) {
    return prev.filter((m) => m.message_id !== optimisticId)
  }
  try {
    const list = await fetchAgentMessages(threadId)
    if (list.length) return list
  } catch {
    /* ignore */
  }
  return prev.filter((m) => m.message_id !== optimisticId)
}

export type DramaAgentChatSendOutcome =
  | { ok: true; data: DramaAgentChatResult; messages: DramaAgentMessage[] }
  | { ok: false; reason: 'in_flight' | 'error'; error?: unknown; messages?: DramaAgentMessage[] }

export async function sendDramaAgentChat(params: {
  threadId: string
  message: string
  refs: DramaAgentRef[]
  currentMessages: DramaAgentMessage[]
  optimistic: DramaAgentMessage
}): Promise<DramaAgentChatSendOutcome> {
  const { threadId, message, refs, currentMessages, optimistic } = params
  const lockKey = chatInflightKey(threadId)
  if (!tryAcquireChatInflight(lockKey)) {
    return { ok: false, reason: 'in_flight' }
  }
  try {
    const res = await agentThreadChat(threadId, { message, refs })
    const data = res.data
    if (!data) {
      return { ok: false, reason: 'error', error: new Error('empty chat response') }
    }
    let messages = applyChatResultToMessages(
      [...currentMessages, optimistic],
      optimistic,
      data,
    )
    try {
      const list = await fetchAgentMessages(threadId)
      messages = applyChatResultToMessages(
        [...currentMessages, optimistic],
        optimistic,
        data,
        list,
      )
    } catch {
      /* 保留 chat 响应合并结果 */
    }
    return { ok: true, data, messages }
  } catch (error) {
    let messages: DramaAgentMessage[] | undefined
    try {
      messages = await recoverMessagesAfterChatFailure(
        threadId,
        [...currentMessages, optimistic],
        optimistic.message_id,
      )
    } catch {
      messages = currentMessages.filter((m) => m.message_id !== optimistic.message_id)
    }
    return { ok: false, reason: 'error', error, messages }
  } finally {
    releaseChatInflight(lockKey)
  }
}

/** 最后一条是否为「仅有用户消息、尚无助手回复」 */
export function threadAwaitingAssistantReply(messages: DramaAgentMessage[]): boolean {
  const conversational = messages.filter((m) => m.role === 'user' || m.role === 'assistant')
  const last = conversational[conversational.length - 1]
  return last?.role === 'user' && !isPendingAgentMessage(last)
}

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

/** 请求断开但后端可能仍在处理时，轮询直到出现助手回复 */
export async function pollAgentMessagesUntilReply(
  threadId: string,
  options?: { maxAttempts?: number; intervalMs?: number },
): Promise<DramaAgentMessage[] | null> {
  const maxAttempts = options?.maxAttempts ?? 30
  const intervalMs = options?.intervalMs ?? 3000
  for (let i = 0; i < maxAttempts; i += 1) {
    await sleep(intervalMs)
    try {
      const list = await fetchAgentMessages(threadId)
      if (!threadAwaitingAssistantReply(list)) {
        return list
      }
    } catch {
      /* retry */
    }
  }
  return null
}
