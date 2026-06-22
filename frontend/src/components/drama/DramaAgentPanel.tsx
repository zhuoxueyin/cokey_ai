import { memo, useCallback, useEffect, useRef, useState, type MutableRefObject } from 'react'
import { message } from 'antd'
import { CloseOutlined, RobotOutlined } from '@ant-design/icons'
import { getModels } from '@/api'
import { listDramaStylesUser } from '@/api/drama'
import {
  createAgentThread,
  getAgentThreadByCanvas,
  listAgentMessages,
  updateAgentThread,
} from '@/api/dramaAgent'
import type { ModelItem } from '@/types'
import type { DramaStylePreset } from '@/types/drama'
import type {
  DramaAgentMessage,
  DramaAgentMode,
  DramaAgentProcessStep,
  DramaAgentRef,
} from '@/types/dramaAgent'
import { extractApiErrorMessage } from '@/utils/apiError'
import {
  bindCanvasThread,
  getSessionByCanvas,
  getThreadSession,
  messagesChanged,
  upsertThreadSession,
} from '@/utils/dramaAgentSessionCache'
import {
  buildOptimisticUserMessage,
  isPendingAgentMessage,
  mergeAgentMessageList,
  pollAgentMessagesUntilReply,
  sendDramaAgentChat,
  threadAwaitingAssistantReply,
} from '@/utils/dramaAgentSend'
import { pickDefaultModelCode, sortModelsByAdminOrder } from '@/utils/modelOrder'
import { canvasAgentBridge } from '@/utils/canvasAgentBridge'
import type { CharacterImageTask } from '@/utils/characterImageTasks'
import DramaAgentChat from './DramaAgentChat'
import DramaAgentComposer from './DramaAgentComposer'

const MIN_W = 280
const MAX_W_RATIO = 0.5
const DEFAULT_W = 380

function getMaxPanelWidth(viewportWidth = window.innerWidth) {
  return Math.max(MIN_W, Math.floor(viewportWidth * MAX_W_RATIO))
}

function clampPanelWidth(value: number, viewportWidth = window.innerWidth) {
  return Math.min(getMaxPanelWidth(viewportWidth), Math.max(MIN_W, value))
}

function panelOpenKey(canvasProjectId: string) {
  return `drama_agent_panel_open_${canvasProjectId}`
}

function panelWidthKey(canvasProjectId: string) {
  return `drama_agent_panel_width_${canvasProjectId}`
}

interface DramaAgentPanelProps {
  canvasProjectId: string
  /** 真实已落库的画布 id；new 草稿态时为空，不做后端 canvas 绑定 */
  bindableCanvasProjectId?: string
  /** 稳定 ref，避免画布 setNodes 导致侧栏重渲染 */
  spawnTextNodeRef?: MutableRefObject<
    ((content: string, meta: { role: 'user' | 'assistant' }) => void | Promise<void>) | undefined
  >
  spawnImageTaskRef?: MutableRefObject<
    | ((
        task: CharacterImageTask,
        opts: { modelCode?: string; stylePresetId?: string; stylePresetName?: string },
      ) => void | Promise<void>)
    | undefined
  >
  /** @deprecated 请用 spawnTextNodeRef */
  onSpawnTextNode?: (content: string, meta: { role: 'user' | 'assistant' }) => void | Promise<void>
}

function applyThreadToPanelState(
  thread: {
    thread_id: string
    agent_mode: DramaAgentMode
    model_code?: string
    style_preset_id?: string
    multi_episode: boolean
    stage?: string
    title?: string
  },
  messages: DramaAgentMessage[],
  setters: {
    setThreadId: (v: string) => void
    setAgentMode: (v: DramaAgentMode) => void
    setModelCode: (v?: string) => void
    setStylePresetId: (v?: string) => void
    setMultiEpisode: (v: boolean) => void
    setStage: (v: string) => void
    setMessages: (v: DramaAgentMessage[]) => void
  },
) {
  setters.setThreadId(thread.thread_id)
  setters.setAgentMode(thread.agent_mode)
  setters.setModelCode(thread.model_code)
  setters.setStylePresetId(thread.style_preset_id || undefined)
  setters.setMultiEpisode(thread.multi_episode)
  setters.setStage(thread.stage || 'concept')
  setters.setMessages(messages)
}

function DramaAgentPanelInner({
  canvasProjectId,
  bindableCanvasProjectId,
  spawnTextNodeRef,
  spawnImageTaskRef,
  onSpawnTextNode,
}: DramaAgentPanelProps) {
  const cachedInit = getSessionByCanvas(canvasProjectId)
  const [open, setOpen] = useState(
    () => localStorage.getItem(panelOpenKey(canvasProjectId)) === '1',
  )
  const [width, setWidth] = useState(() => {
    const n = Number(localStorage.getItem(panelWidthKey(canvasProjectId)))
    return clampPanelWidth(Number.isFinite(n) && n >= MIN_W ? n : DEFAULT_W)
  })
  const [dragging, setDragging] = useState(false)
  const [threadId, setThreadId] = useState<string | null>(() => cachedInit?.threadId ?? null)
  const [messages, setMessages] = useState<DramaAgentMessage[]>(() => cachedInit?.messages ?? [])
  const [loading, setLoading] = useState(false)
  const [hydrating, setHydrating] = useState(() => !cachedInit)
  const [chatVisible, setChatVisible] = useState(
    () => Boolean(cachedInit && (cachedInit.messages.length > 0 || cachedInit.threadId)),
  )
  const [models, setModels] = useState<ModelItem[]>([])
  const [styles, setStyles] = useState<DramaStylePreset[]>([])
  const [agentMode, setAgentMode] = useState<DramaAgentMode>(
    () => cachedInit?.agentMode ?? 'creative_short_drama',
  )
  const [modelCode, setModelCode] = useState<string | undefined>(() => cachedInit?.modelCode)
  const [stylePresetId, setStylePresetId] = useState<string | undefined>(() => cachedInit?.stylePresetId)
  const [multiEpisode, setMultiEpisode] = useState(() => cachedInit?.multiEpisode ?? false)
  const [refs, setRefs] = useState<DramaAgentRef[]>([])
  const [stage, setStage] = useState(() => cachedInit?.stage ?? 'concept')
  const [suggestedNext, setSuggestedNext] = useState<string[]>(() => cachedInit?.suggestedNext ?? [])
  const [liveProcessTrace, setLiveProcessTrace] = useState<DramaAgentProcessStep[]>([])
  const dragStartX = useRef(0)
  const dragStartW = useRef(DEFAULT_W)

  const handleAddToCanvas = useCallback(
    (content: string, meta: { role: DramaAgentMessage['role'] }) => {
      if (meta.role !== 'user' && meta.role !== 'assistant') return
      const fn = spawnTextNodeRef?.current ?? onSpawnTextNode
      return fn?.(content, { role: meta.role })
    },
    [spawnTextNodeRef, onSpawnTextNode],
  )

  const syncCache = useCallback(
    (
      tid: string,
      patch?: {
        messages?: DramaAgentMessage[]
        suggestedNext?: string[]
        stylePresetId?: string
      },
    ) => {
      upsertThreadSession(tid, {
        canvasProjectId,
        messages: patch?.messages ?? messages,
        agentMode,
        modelCode,
        stylePresetId:
          patch && 'stylePresetId' in patch ? patch.stylePresetId : stylePresetId,
        multiEpisode,
        stage,
        suggestedNext: patch?.suggestedNext ?? suggestedNext,
      })
    },
    [canvasProjectId, messages, agentMode, modelCode, stylePresetId, multiEpisode, stage, suggestedNext],
  )

  useEffect(() => {
    localStorage.setItem(panelOpenKey(canvasProjectId), open ? '1' : '0')
  }, [open, canvasProjectId])

  useEffect(() => {
    localStorage.setItem(panelWidthKey(canvasProjectId), String(width))
  }, [width, canvasProjectId])

  useEffect(() => {
    const onResize = () => {
      setWidth((current) => clampPanelWidth(current))
    }
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [])

  useEffect(() => {
    setWidth((current) => clampPanelWidth(current))
  }, [canvasProjectId])

  useEffect(() => {
    getModels('text').then((res) => {
      const list = sortModelsByAdminOrder(res.data || [])
      setModels(list)
      const defaultCode = pickDefaultModelCode(list)
      if (!modelCode && defaultCode) setModelCode(defaultCode)
    })
    listDramaStylesUser({ page: 1, page_size: 100 }).then((res) => {
      setStyles((res.data as DramaStylePreset[]) || [])
    })
  }, [])

  useEffect(() => {
    let cancelled = false
    const setters = {
      setThreadId,
      setAgentMode,
      setModelCode,
      setStylePresetId,
      setMultiEpisode,
      setStage,
      setMessages,
    }

    const cached = getSessionByCanvas(canvasProjectId)
    if (cached) {
      applyThreadToPanelState(
        {
          thread_id: cached.threadId,
          agent_mode: cached.agentMode,
          model_code: cached.modelCode,
          style_preset_id: cached.stylePresetId,
          multi_episode: cached.multiEpisode,
          stage: cached.stage,
        },
        cached.messages,
        setters,
      )
      setSuggestedNext(cached.suggestedNext)
      setHydrating(false)
      setChatVisible(true)
    }

    const loadBoundThread = async () => {
      if (!bindableCanvasProjectId) {
        if (!cancelled) {
          setHydrating(false)
          setChatVisible(true)
        }
        return
      }
      try {
        const res = await getAgentThreadByCanvas(bindableCanvasProjectId)
        if (cancelled || !res.data) return
        const thread = res.data
        bindCanvasThread(canvasProjectId, thread.thread_id)

        const session = getThreadSession(thread.thread_id)
        if (session && !cancelled) {
          applyThreadToPanelState(thread, session.messages, setters)
          setSuggestedNext(session.suggestedNext)
        } else if (!cancelled) {
          applyThreadToPanelState(thread, [], setters)
        }

        const hist = await listAgentMessages(thread.thread_id, 200)
        if (cancelled) return
        const list = (hist.data as DramaAgentMessage[]) || []
        const base = getThreadSession(thread.thread_id)?.messages ?? session?.messages ?? []
        if (messagesChanged(base, list)) {
          setMessages((current) => mergeAgentMessageList(current, list))
        }
        setStylePresetId(thread.style_preset_id || undefined)
        upsertThreadSession(thread.thread_id, {
          canvasProjectId,
          messages: list,
          agentMode: thread.agent_mode,
          modelCode: thread.model_code,
          stylePresetId: thread.style_preset_id || undefined,
          multiEpisode: thread.multi_episode,
          stage: thread.stage || 'concept',
        })
      } catch {
        /* 画布尚未绑定对话，首次发送时创建 */
      } finally {
        if (!cancelled) {
          setHydrating(false)
          setChatVisible(true)
        }
      }
    }

    if (!cached) {
      setHydrating(true)
    } else {
      setChatVisible(true)
    }
    loadBoundThread()
    return () => {
      cancelled = true
    }
  }, [canvasProjectId, bindableCanvasProjectId])

  /** 画布从 new 落库后，将已创建的 thread 与真实 project_id 对齐 */
  useEffect(() => {
    if (!threadId || !bindableCanvasProjectId) return
    bindCanvasThread(bindableCanvasProjectId, threadId)
    upsertThreadSession(threadId, { canvasProjectId: bindableCanvasProjectId })
    void updateAgentThread(threadId, { canvas_project_id: bindableCanvasProjectId }).catch(() => {
      /* 已绑定或冲突时忽略 */
    })
  }, [threadId, bindableCanvasProjectId])

  useEffect(() => {
    if (threadId) syncCache(threadId)
  }, [threadId, messages, stage, agentMode, stylePresetId, modelCode, multiEpisode, suggestedNext, syncCache])

  const ensureCanvasReady = useCallback(async (): Promise<string | undefined> => {
    if (bindableCanvasProjectId) return bindableCanvasProjectId
    const fn = canvasAgentBridge.ensureCanvasPersistedRef.current
    if (!fn) return undefined
    const id = await fn()
    return id
  }, [bindableCanvasProjectId])

  const handleTogglePanel = useCallback(async () => {
    if (!open) {
      try {
        await ensureCanvasReady()
      } catch (e) {
        message.error(extractApiErrorMessage(e, '创建画布失败'))
        return
      }
    }
    setOpen((v) => !v)
  }, [open, ensureCanvasReady])

  const ensureThread = useCallback(async () => {
    if (threadId) return threadId
    const canvasId = await ensureCanvasReady()
    const res = await createAgentThread({
      canvas_project_id: canvasId,
      agent_mode: agentMode,
      model_code: modelCode,
      style_preset_id: stylePresetId,
      multi_episode: multiEpisode,
      title: '画布创作助手',
    })
    const thread = res.data!
    if (thread.agent_mode) setAgentMode(thread.agent_mode)
    setThreadId(thread.thread_id)
    const bindKey = canvasId || canvasProjectId
    if (bindKey) bindCanvasThread(bindKey, thread.thread_id)
    return thread.thread_id
  }, [
    threadId,
    ensureCanvasReady,
    canvasProjectId,
    agentMode,
    modelCode,
    stylePresetId,
    multiEpisode,
  ])

  const handleSend = async (msg: string, sendRefs: DramaAgentRef[]) => {
    if (loading) return

    setLoading(true)
    setLiveProcessTrace([])
    setRefs([])

    let tid = threadId
    let optimistic = buildOptimisticUserMessage(tid || 'pending', msg, sendRefs)
    try {
      tid = tid || (await ensureThread())
      optimistic = buildOptimisticUserMessage(tid, msg, sendRefs)
      setMessages((prev) => [...prev, optimistic])
      upsertThreadSession(tid, {
        canvasProjectId,
        messages: [...messages, optimistic],
        agentMode,
        modelCode,
        stylePresetId,
        multiEpisode,
        stage,
        suggestedNext,
      })

      const outcome = await sendDramaAgentChat({
        threadId: tid,
        message: msg,
        refs: sendRefs,
        currentMessages: messages,
        optimistic,
      })

      if (outcome.ok === false && outcome.reason === 'in_flight') {
        message.warning('上一条消息仍在处理中，请稍候')
        setMessages((prev) => prev.filter((m) => m.message_id !== optimistic.message_id))
        return
      }

      if (outcome.ok === false) {
        message.error(
          extractApiErrorMessage(outcome.error, '发送失败，请检查文本模型是否已上线并绑定渠道'),
        )
        if (outcome.messages) {
          setMessages(outcome.messages)
          if (threadAwaitingAssistantReply(outcome.messages)) {
            message.info('连接可能已断开，正在等待服务端回复…')
            const polled = await pollAgentMessagesUntilReply(tid)
            if (polled) {
              setMessages(polled)
              syncCache(tid, { messages: polled })
              message.success('已收到创作助手回复')
              return
            }
            message.info('您的消息可能仍在处理中，请稍候再发，避免重复提问')
          }
        } else {
          setMessages((prev) => prev.filter((m) => m.message_id !== optimistic.message_id))
        }
        console.error(outcome.error)
        return
      }

      const { data } = outcome
      setMessages(outcome.messages)
      setStage(data.stage)
      setSuggestedNext(data.suggested_next || [])
      if (data.agent_mode) setAgentMode(data.agent_mode)
      if (data.process_trace) setLiveProcessTrace(data.process_trace)
      upsertThreadSession(tid, {
        canvasProjectId,
        messages: outcome.messages,
        agentMode: data.agent_mode || agentMode,
        modelCode: data.model_code || modelCode,
        stylePresetId: data.style_preset_id ?? stylePresetId,
        stage: data.stage || stage,
        suggestedNext: data.suggested_next ?? suggestedNext,
      })
      const lastAssistant = [...outcome.messages].reverse().find((m) => m.role === 'assistant')
      if (lastAssistant?.meta?.error) {
        message.warning(lastAssistant.content || '模型调用失败，请检查渠道绑定')
      }
    } catch (e) {
      message.error(extractApiErrorMessage(e, '发送失败，请检查文本模型是否已上线并绑定渠道'))
      setMessages((prev) => prev.filter((m) => !m.message_id.startsWith('pending_')))
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const selectedStyle = styles.find((s) => s.style_id === stylePresetId)

  const awaitingRecoverKey = (() => {
    if (!threadId || !threadAwaitingAssistantReply(messages)) return null
    const lastUser = [...messages].reverse().find((m) => m.role === 'user' && !isPendingAgentMessage(m))
    return lastUser ? `${threadId}:${lastUser.message_id}` : null
  })()

  useEffect(() => {
    if (!awaitingRecoverKey || hydrating || loading) return
    let cancelled = false
    void (async () => {
      const polled = await pollAgentMessagesUntilReply(threadId!, { maxAttempts: 24, intervalMs: 2500 })
      if (!cancelled && polled) {
        setMessages(polled)
        syncCache(threadId!, { messages: polled })
      }
    })()
    return () => {
      cancelled = true
    }
  }, [awaitingRecoverKey, hydrating, loading, threadId, syncCache])

  const handleSpawnImageTask = useCallback(
    (task: CharacterImageTask) => {
      const fn = spawnImageTaskRef?.current ?? canvasAgentBridge.spawnImageTaskRef.current
      return fn?.(task, {
        modelCode,
        stylePresetId,
        stylePresetName: selectedStyle?.name,
      })
    },
    [spawnImageTaskRef, modelCode, stylePresetId, selectedStyle?.name],
  )

  const onResizeStart = (e: React.MouseEvent) => {
    e.preventDefault()
    setDragging(true)
    dragStartX.current = e.clientX
    dragStartW.current = width
  }

  useEffect(() => {
    if (!dragging) return
    const onMove = (e: MouseEvent) => {
      const delta = dragStartX.current - e.clientX
      setWidth(clampPanelWidth(dragStartW.current + delta))
    }
    const onUp = () => setDragging(false)
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
    return () => {
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mouseup', onUp)
    }
  }, [dragging])

  const handleStylePresetChange = useCallback(
    async (styleId?: string) => {
      setStylePresetId(styleId)
      if (!threadId) return
      try {
        await updateAgentThread(threadId, { style_preset_id: styleId ?? null })
        syncCache(threadId, { stylePresetId: styleId })
      } catch {
        message.error('风格保存失败，请重试')
      }
    },
    [threadId, syncCache],
  )

  const modeLocked = !!threadId && messages.some((m) => m.role === 'user')
  const styleLocked = !!stylePresetId && !!threadId

  return (
    <>
      <button
        type="button"
        className="drama-agent-fab"
        title="创作助手"
        onClick={() => void handleTogglePanel()}
      >
        <RobotOutlined />
      </button>

      <aside
        className={`drama-agent-panel${open ? '' : ' drama-agent-panel--closed'}`}
        style={{ width }}
        aria-hidden={!open}
      >
        <div
          className="drama-agent-panel__resize"
          onMouseDown={onResizeStart}
          role="separator"
          aria-orientation="vertical"
        />
        <div className="drama-agent-panel__header">
          <div className="drama-agent-panel__header-main">
            <span>创作助手</span>
          </div>
          <button type="button" className="drama-agent-panel__close" onClick={() => setOpen(false)}>
            <CloseOutlined />
          </button>
        </div>
        <div className="drama-agent-panel__body">
          {!chatVisible && hydrating && messages.length === 0 ? (
            <div className="drama-agent-panel__hydrating">加载对话历史…</div>
          ) : (
            <DramaAgentChat
              messages={messages}
              loading={loading}
              stage={stage}
              suggestedNext={suggestedNext}
              agentMode={agentMode}
              modeLocked={modeLocked}
              stylePresetId={stylePresetId}
              styleName={selectedStyle?.name}
              liveProcessTrace={liveProcessTrace}
              threadId={threadId}
              scrollSurface="panel"
              onAddToCanvas={handleAddToCanvas}
              onSpawnImageTask={handleSpawnImageTask}
            />
          )}
        </div>
        <div className="drama-agent-panel__footer">
          <DramaAgentComposer
            variant="compact"
            agentMode={agentMode}
            onAgentModeChange={setAgentMode}
            modeLocked={modeLocked}
            styleLocked={styleLocked}
            modelCode={modelCode}
            onModelCodeChange={setModelCode}
            models={models}
            stylePresetId={stylePresetId}
            onStylePresetChange={(id) => void handleStylePresetChange(id)}
            styles={styles}
            refs={refs}
            onRefsChange={setRefs}
            loading={loading || (hydrating && messages.length === 0)}
            onSend={handleSend}
            canvasProjectId={canvasProjectId}
          />
        </div>
      </aside>
    </>
  )
}

export default memo(DramaAgentPanelInner, (prev, next) => prev.canvasProjectId === next.canvasProjectId)
