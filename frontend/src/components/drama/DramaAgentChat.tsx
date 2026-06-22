import { useCallback, useEffect, useLayoutEffect, useRef, type ReactNode } from 'react'
import { Button, Spin, Tag, Tooltip, message } from 'antd'
import { CopyOutlined, PictureOutlined, PlusOutlined } from '@ant-design/icons'
import type { DramaAgentMessage, DramaAgentMode, DramaAgentProcessStep } from '@/types/dramaAgent'
import { getAgentModeLabel, STAGE_LABELS } from '@/types/dramaAgent'
import {
  getScrollTop,
  saveScrollTop,
  type DramaAgentScrollSurface,
} from '@/utils/dramaAgentSessionCache'
import { canvasAgentBridge } from '@/utils/canvasAgentBridge'
import {
  characterImageTaskButtonLabel,
  parseAgentImageTasksFromReply,
  type CharacterImageTask,
} from '@/utils/characterImageTasks'
import DramaAgentProcessTrace from './DramaAgentProcessTrace'
import DramaAgentRefStrip from './DramaAgentRefStrip'

interface DramaAgentChatProps {
  messages: DramaAgentMessage[]
  loading?: boolean
  stage?: string
  suggestedNext?: string[]
  agentMode?: DramaAgentMode
  modeLocked?: boolean
  stylePresetId?: string
  styleName?: string
  liveProcessTrace?: DramaAgentProcessStep[]
  threadId?: string | null
  scrollSurface?: DramaAgentScrollSurface
  headerActions?: ReactNode
  /** 将当前消息正文写入画布文本节点（仅画布侧栏等场景传入） */
  onAddToCanvas?: (content: string, meta: { role: DramaAgentMessage['role'] }) => void | Promise<void>
  /** 角色阶段一键出图（解析 look/card 任务块） */
  onSpawnImageTask?: (task: CharacterImageTask) => void | Promise<void>
}

function parseProcessTrace(meta?: Record<string, unknown>): DramaAgentProcessStep[] {
  const raw = meta?.process_trace
  return Array.isArray(raw) ? (raw as DramaAgentProcessStep[]) : []
}

const STICK_THRESHOLD = 96

function buildMessageCopyText(messages: DramaAgentMessage[], index: number): string {
  const current = messages[index]
  if (!current?.content) return ''

  if (current.role === 'user') {
    return `【用户】\n${current.content}`
  }

  let userContent = ''
  for (let i = index - 1; i >= 0; i -= 1) {
    const prev = messages[i]
    if (prev.role === 'user') {
      userContent = prev.content
      break
    }
    if (prev.role === 'assistant') break
  }

  if (userContent) {
    return `【用户】\n${userContent}\n\n【创作助手】\n${current.content}`
  }
  return `【创作助手】\n${current.content}`
}

async function copyMessageText(text: string) {
  if (!text.trim()) return
  try {
    await navigator.clipboard.writeText(text)
    message.success('已复制到剪贴板')
  } catch {
    message.error('复制失败，请检查浏览器权限')
  }
}

function MessageBubbleActions({
  messages,
  index,
  stage,
  onAddToCanvas,
  onSpawnImageTask,
  onPrepareAddToCanvas,
}: {
  messages: DramaAgentMessage[]
  index: number
  stage?: string
  onAddToCanvas?: DramaAgentChatProps['onAddToCanvas']
  onSpawnImageTask?: DramaAgentChatProps['onSpawnImageTask']
  onPrepareAddToCanvas?: () => void
}) {
  const current = messages[index]
  const isAssistant = current.role === 'assistant'
  const copyLabel = isAssistant ? '复制本轮' : '复制'
  const copyText = buildMessageCopyText(messages, index)
  const canvasContent = current.content?.trim() || ''
  const imageTasks =
    isAssistant && onSpawnImageTask
      ? parseAgentImageTasksFromReply(current.content || '', stage)
      : []

  return (
    <div className="drama-agent-chat__bubble-actions">
      <div className="drama-agent-chat__bubble-actions-row">
        <Tooltip title={copyLabel}>
          <Button
            type="text"
            size="small"
            className="drama-agent-chat__action-btn"
            icon={<CopyOutlined />}
            aria-label={copyLabel}
            onClick={() => void copyMessageText(copyText)}
          />
        </Tooltip>
        {onAddToCanvas && canvasContent && (
          <Tooltip title="添加到画布">
            <Button
              type="text"
              size="small"
              className="drama-agent-chat__action-btn"
              icon={<PlusOutlined />}
              aria-label="添加到画布"
              onMouseDown={(e) => {
                e.preventDefault()
                onPrepareAddToCanvas?.()
              }}
              onClick={() => void onAddToCanvas(canvasContent, { role: current.role })}
            />
          </Tooltip>
        )}
      </div>
      {imageTasks.length > 0 && (
        <div className="drama-agent-chat__bubble-actions-images">
          {imageTasks.map((task) => (
            <Button
              key={task.task_id}
              type="default"
              size="small"
              className="drama-agent-chat__image-task-btn"
              icon={<PictureOutlined />}
              aria-label={characterImageTaskButtonLabel(task)}
              onMouseDown={(e) => {
                e.preventDefault()
                onPrepareAddToCanvas?.()
              }}
              onClick={() => void onSpawnImageTask?.(task)}
            >
              {characterImageTaskButtonLabel(task)}
            </Button>
          ))}
        </div>
      )}
    </div>
  )
}

export default function DramaAgentChat({
  messages,
  loading,
  stage,
  suggestedNext,
  agentMode,
  modeLocked,
  stylePresetId,
  styleName,
  liveProcessTrace,
  threadId,
  scrollSurface,
  headerActions,
  onAddToCanvas,
  onSpawnImageTask,
}: DramaAgentChatProps) {
  const messagesRef = useRef<HTMLDivElement>(null)
  const stickToBottomRef = useRef(false)
  const prevCountRef = useRef(messages.length)
  const pendingFollowBottomRef = useRef(false)
  const scrollLockRef = useRef(false)

  const canPersistScroll = Boolean(threadId && scrollSurface)

  const restoreScrollFromCache = useCallback(() => {
    const el = messagesRef.current
    if (!el || !threadId || !scrollSurface) return
    if (pendingFollowBottomRef.current) return
    if (loading && stickToBottomRef.current) return

    const saved = getScrollTop(threadId, scrollSurface)
    if (saved == null) {
      if (messages.length > 0) {
        el.scrollTop = el.scrollHeight
        saveScrollTop(threadId, scrollSurface, el.scrollTop)
        stickToBottomRef.current = true
      }
      return
    }

    const maxScroll = Math.max(0, el.scrollHeight - el.clientHeight)
    const target = Math.min(saved, maxScroll)
    if (Math.abs(el.scrollTop - target) > 2) {
      el.scrollTop = target
    }
    stickToBottomRef.current = target >= maxScroll - STICK_THRESHOLD
  }, [threadId, scrollSurface, loading, messages.length])

  useEffect(() => {
    if (!threadId || !scrollSurface) return
    const saved = getScrollTop(threadId, scrollSurface)
    if (saved == null) {
      stickToBottomRef.current = true
      return
    }
    stickToBottomRef.current = false
  }, [threadId, scrollSurface])

  useLayoutEffect(() => {
    const el = messagesRef.current
    if (!el) return

    const savedScroll =
      canPersistScroll && threadId && scrollSurface
        ? getScrollTop(threadId, scrollSurface)
        : null

    const grew = messages.length > prevCountRef.current
    const last = messages[messages.length - 1]
    const userJustSent = grew && last?.role === 'user'
    const assistantReplied = grew && last?.role === 'assistant'
    prevCountRef.current = messages.length

    const shouldFollowBottom =
      pendingFollowBottomRef.current ||
      userJustSent ||
      (assistantReplied && stickToBottomRef.current) ||
      (loading && stickToBottomRef.current) ||
      (savedScroll == null && messages.length > 0)

    if (shouldFollowBottom) {
      el.scrollTop = el.scrollHeight
      if (threadId && scrollSurface) {
        saveScrollTop(threadId, scrollSurface, el.scrollTop)
      }
      stickToBottomRef.current = true
      pendingFollowBottomRef.current = false
      return
    }

    if (!canPersistScroll || !threadId || !scrollSurface) return
    if (savedScroll == null) return

    const maxScroll = Math.max(0, el.scrollHeight - el.clientHeight)
    const target = Math.min(savedScroll, maxScroll)
    if (Math.abs(el.scrollTop - target) > 2) {
      el.scrollTop = target
      stickToBottomRef.current = target >= maxScroll - STICK_THRESHOLD
    }
  }, [messages, loading, threadId, scrollSurface, canPersistScroll])

  useEffect(() => {
    const el = messagesRef.current
    if (!el || !canPersistScroll || !threadId || !scrollSurface) return

    const onScroll = () => {
      if (scrollLockRef.current) return
      saveScrollTop(threadId, scrollSurface, el.scrollTop)
      stickToBottomRef.current =
        el.scrollTop >= el.scrollHeight - el.clientHeight - STICK_THRESHOLD
    }

    el.addEventListener('scroll', onScroll, { passive: true })
    const ro = new ResizeObserver(() => {
      if (scrollLockRef.current) {
        restoreScrollFromCache()
        return
      }
      restoreScrollFromCache()
    })
    ro.observe(el)

    return () => {
      el.removeEventListener('scroll', onScroll)
      ro.disconnect()
    }
  }, [threadId, scrollSurface, canPersistScroll, restoreScrollFromCache])

  const pinScrollBeforeCanvas = useCallback(() => {
    const el = messagesRef.current
    if (el && threadId && scrollSurface) {
      scrollLockRef.current = true
      saveScrollTop(threadId, scrollSurface, el.scrollTop)
      stickToBottomRef.current =
        el.scrollTop >= el.scrollHeight - el.clientHeight - STICK_THRESHOLD
    }
  }, [threadId, scrollSurface])

  useEffect(() => {
    if (!threadId || !scrollSurface) {
      canvasAgentBridge.setScrollGuard(null)
      return
    }
    const guard = {
      pin: pinScrollBeforeCanvas,
      restore: () => {
        restoreScrollFromCache()
        scrollLockRef.current = false
      },
    }
    canvasAgentBridge.setScrollGuard(guard)
    return () => canvasAgentBridge.setScrollGuard(null)
  }, [threadId, scrollSurface, pinScrollBeforeCanvas, restoreScrollFromCache])

  const handleAddToCanvas = useCallback(
    (content: string, meta: { role: DramaAgentMessage['role'] }) => {
      pinScrollBeforeCanvas()
      return onAddToCanvas?.(content, meta)
    },
    [onAddToCanvas, pinScrollBeforeCanvas],
  )

  const handleSpawnImageTask = useCallback(
    (task: CharacterImageTask) => {
      pinScrollBeforeCanvas()
      return onSpawnImageTask?.(task)
    },
    [onSpawnImageTask, pinScrollBeforeCanvas],
  )

  const displayStyleName = styleName

  return (
    <div className="drama-agent-chat">
      {(stage || agentMode || stylePresetId || displayStyleName || headerActions) && (
        <div className="drama-agent-chat__meta">
          <div className="drama-agent-chat__meta-left">
            {agentMode && (
              <Tag color="purple" className="drama-agent-chat__mode-tag">
                {getAgentModeLabel(agentMode)}
                {modeLocked ? ' · 已锁定' : ''}
              </Tag>
            )}
            {(stylePresetId || displayStyleName) && (
              <Tag color="gold" className="drama-agent-chat__style-tag">
                风格：{displayStyleName || stylePresetId}
              </Tag>
            )}
            {stage && (
              <span className="drama-agent-chat__stage">
                当前阶段：
                <Tag color="default">{STAGE_LABELS[stage] || stage}</Tag>
              </span>
            )}
          </div>
          {headerActions && <div className="drama-agent-chat__meta-actions">{headerActions}</div>}
        </div>
      )}

      <div className="drama-agent-chat__messages" ref={messagesRef}>
        {messages.map((m, index) => (
          <div
            key={m.message_id}
            className={`drama-agent-chat__bubble drama-agent-chat__bubble--${m.role}`}
          >
            <div className="drama-agent-chat__bubble-head">
              <div className="drama-agent-chat__role">{m.role === 'user' ? '你' : '创作助手'}</div>
            </div>
            {m.role === 'assistant' && (
              <DramaAgentProcessTrace steps={parseProcessTrace(m.meta)} />
            )}
            {m.role === 'user' && m.refs && m.refs.length > 0 && (
              <DramaAgentRefStrip refs={m.refs} size="sm" className="drama-agent-chat__refs" />
            )}
            <div className="drama-agent-chat__content">{m.content}</div>
            <MessageBubbleActions
              messages={messages}
              index={index}
              stage={stage}
              onAddToCanvas={handleAddToCanvas}
              onSpawnImageTask={onSpawnImageTask ? handleSpawnImageTask : undefined}
              onPrepareAddToCanvas={pinScrollBeforeCanvas}
            />
          </div>
        ))}
        {loading && (
          <div className="drama-agent-chat__loading-block">
            <div className="drama-agent-chat__loading">
              <Spin size="small" /> 思考中…
            </div>
            {liveProcessTrace && liveProcessTrace.length > 0 && (
              <DramaAgentProcessTrace steps={liveProcessTrace} defaultOpen live />
            )}
          </div>
        )}
      </div>

    </div>
  )
}
