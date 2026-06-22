import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { Button, Space, Spin, message } from 'antd'
import { BlockOutlined, FolderOutlined, PlusOutlined } from '@ant-design/icons'
import { getModels } from '@/api'
import { listDramaStylesUser } from '@/api/drama'
import {
  createAgentThread,
  getAgentThread,
  listAgentMessages,
  spawnAgentCanvas,
  updateAgentThread,
} from '@/api/dramaAgent'
import { createCanvasNode } from '@/api/canvas'
import { openCanvasProject } from '@/utils/canvasNav'
import { extractApiErrorMessage } from '@/utils/apiError'
import {
  buildCanvasNodeConfigFromAgentTask,
  characterImageTaskButtonLabel,
  resolveAgentTaskNodeType,
  type CharacterImageTask,
} from '@/utils/characterImageTasks'
import DramaAgentChat from '@/components/drama/DramaAgentChat'
import DramaAgentComposer from '@/components/drama/DramaAgentComposer'
import type { ModelItem } from '@/types'
import type { DramaStylePreset } from '@/types/drama'
import type {
  DramaAgentMessage,
  DramaAgentMode,
  DramaAgentProcessStep,
  DramaAgentRef,
} from '@/types/dramaAgent'
import { getAgentModeLabel } from '@/types/dramaAgent'
import { pickDefaultModelCode, sortModelsByAdminOrder } from '@/utils/modelOrder'
import {
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

export default function DramaSuperAgentPage() {
  const { threadId: routeThreadId } = useParams<{ threadId?: string }>()
  const navigate = useNavigate()
  const [hydrating, setHydrating] = useState(!!routeThreadId)
  const [started, setStarted] = useState(false)
  const [threadId, setThreadId] = useState<string | null>(routeThreadId || null)
  const [threadTitle, setThreadTitle] = useState('')
  const [messages, setMessages] = useState<DramaAgentMessage[]>([])
  const [loading, setLoading] = useState(false)
  const [models, setModels] = useState<ModelItem[]>([])
  const [styles, setStyles] = useState<DramaStylePreset[]>([])
  const [agentMode, setAgentMode] = useState<DramaAgentMode>('creative_short_drama')
  const [modelCode, setModelCode] = useState<string>()
  const [stylePresetId, setStylePresetId] = useState<string>()
  const [multiEpisode, setMultiEpisode] = useState(false)
  const [refs, setRefs] = useState<DramaAgentRef[]>([])
  const [stage, setStage] = useState('concept')
  const [suggestedNext, setSuggestedNext] = useState<string[]>([])
  const [canvasProjectId, setCanvasProjectId] = useState<string>()
  const [spawningCanvas, setSpawningCanvas] = useState(false)
  const [liveProcessTrace, setLiveProcessTrace] = useState<DramaAgentProcessStep[]>([])
  const agentTextSpawnRef = useRef(0)
  const agentImageSpawnRef = useRef(0)
  const imageModelsRef = useRef<ModelItem[] | null>(null)
  const videoModelsRef = useRef<ModelItem[] | null>(null)

  useEffect(() => {
    Promise.all([
      getModels('text'),
      listDramaStylesUser({ page: 1, page_size: 100 }),
    ]).then(([mRes, sRes]) => {
      const list = sortModelsByAdminOrder(mRes.data || [])
      setModels(list)
      const defaultCode = pickDefaultModelCode(list)
      if (defaultCode) setModelCode(defaultCode)
      setStyles((sRes.data as DramaStylePreset[]) || [])
    })
  }, [])

  useEffect(() => {
    if (!routeThreadId) {
      setHydrating(false)
      setStarted(false)
      setThreadId(null)
      setThreadTitle('')
      setMessages([])
      setStage('concept')
      setSuggestedNext([])
      return
    }

    let cancelled = false
    const cached = getThreadSession(routeThreadId)
    if (cached) {
      setThreadId(cached.threadId)
      setThreadTitle(cached.threadTitle || '')
      setAgentMode(cached.agentMode)
      setModelCode(cached.modelCode)
      setStylePresetId(cached.stylePresetId)
      setMultiEpisode(cached.multiEpisode)
      setStage(cached.stage || 'concept')
      setSuggestedNext(cached.suggestedNext)
      setMessages(cached.messages)
      setStarted(cached.messages.some((m) => m.role === 'user') || cached.messages.length > 0)
      setHydrating(false)
    } else {
      setHydrating(true)
    }

    Promise.all([getAgentThread(routeThreadId), listAgentMessages(routeThreadId, 200)])
      .then(([tRes, mRes]) => {
        if (cancelled) return
        const thread = tRes.data
        if (!thread) {
          message.error('对话不存在')
          navigate('/my-space', { replace: true })
          return
        }
        const list = (mRes.data as DramaAgentMessage[]) || []
        const prev = getThreadSession(routeThreadId)?.messages ?? cached?.messages
        setThreadId(thread.thread_id)
        setThreadTitle(thread.title || '')
        setAgentMode(thread.agent_mode)
        setModelCode(thread.model_code)
        setStylePresetId(thread.style_preset_id || undefined)
        setMultiEpisode(thread.multi_episode)
        setStage(thread.stage || 'concept')
        setCanvasProjectId(thread.canvas_project_id)
        if (messagesChanged(prev, list)) {
          setMessages((current) => mergeAgentMessageList(current, list))
        }
        setStarted(true)
        upsertThreadSession(thread.thread_id, {
          canvasProjectId: thread.canvas_project_id,
          messages: list,
          agentMode: thread.agent_mode,
          modelCode: thread.model_code,
          stylePresetId: thread.style_preset_id,
          multiEpisode: thread.multi_episode,
          stage: thread.stage || 'concept',
          threadTitle: thread.title || '',
        })
      })
      .catch(() => {
        if (!cancelled && !cached) {
          message.error('加载对话失败')
          navigate('/my-space', { replace: true })
        }
      })
      .finally(() => {
        if (!cancelled) setHydrating(false)
      })

    return () => {
      cancelled = true
    }
  }, [routeThreadId, navigate])

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
        upsertThreadSession(threadId!, { messages: polled })
      }
    })()
    return () => {
      cancelled = true
    }
  }, [awaitingRecoverKey, hydrating, loading, threadId])

  const handleSend = async (msg: string, sendRefs: DramaAgentRef[]) => {
    if (loading) return

    setLoading(true)
    setLiveProcessTrace([])
    setRefs([])
    setStarted(true)

    let tid = threadId
    let optimistic = buildOptimisticUserMessage(tid || 'pending', msg, sendRefs)
    setMessages((prev) => [...prev, optimistic])
    if (tid) {
      upsertThreadSession(tid, { messages: [...messages, optimistic] })
    }

    try {
      if (!tid) {
        const createRes = await createAgentThread({
          agent_mode: agentMode,
          model_code: modelCode,
          style_preset_id: stylePresetId,
          multi_episode: multiEpisode,
          title: msg.slice(0, 40),
        })
        const thread = createRes.data!
        tid = thread.thread_id
        optimistic = { ...optimistic, thread_id: tid }
        if (thread.agent_mode) setAgentMode(thread.agent_mode)
        setThreadId(tid)
        setThreadTitle(thread.title || msg.slice(0, 40))
        setStarted(true)
        upsertThreadSession(tid, {
          messages: [optimistic],
          agentMode: thread.agent_mode,
          modelCode: thread.model_code,
          stylePresetId: thread.style_preset_id,
          multiEpisode: thread.multi_episode,
          stage: thread.stage || 'concept',
          threadTitle: thread.title || msg.slice(0, 40),
        })
        navigate(`/drama/${tid}`, { replace: true })
      }

      const outcome = await sendDramaAgentChat({
        threadId: tid!,
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
            const polled = await pollAgentMessagesUntilReply(tid!)
            if (polled) {
              setMessages(polled)
              upsertThreadSession(tid!, { messages: polled })
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
      upsertThreadSession(tid!, {
        messages: outcome.messages,
        agentMode: data.agent_mode || agentMode,
        modelCode: data.model_code || modelCode,
        stylePresetId: data.style_preset_id ?? stylePresetId,
        stage: data.stage || stage,
        suggestedNext: data.suggested_next || [],
        threadTitle: threadTitle || msg.slice(0, 40),
        canvasProjectId,
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

  const handleStylePresetChange = useCallback(
    async (styleId?: string) => {
      setStylePresetId(styleId)
      if (!threadId) return
      try {
        await updateAgentThread(threadId, { style_preset_id: styleId ?? null })
        upsertThreadSession(threadId, { stylePresetId: styleId })
      } catch {
        message.error('风格保存失败，请重试')
      }
    },
    [threadId],
  )

  const handleGoToCanvas = async () => {
    if (!threadId) return
    if (messages.length === 0) {
      message.info('请先与创作助手完成至少一轮对话')
      return
    }
    if (canvasProjectId) {
      openCanvasProject(canvasProjectId)
      message.success('已打开绑定的出图画布')
      return
    }
    setSpawningCanvas(true)
    try {
      const res = await spawnAgentCanvas(threadId)
      const pid = res.data?.project_id
      if (!pid) {
        message.error(res.message || '打开画布失败')
        return
      }
      setCanvasProjectId(pid)
      upsertThreadSession(threadId, { canvasProjectId: pid })
      openCanvasProject(pid)
      message.success(
        res.data?.already_bound || res.data?.binding_repaired
          ? '已打开绑定的出图画布，可在此继续创作对话'
          : '画布已创建并在新标签页打开，可在此继续创作对话',
      )
    } catch (e) {
      message.error(extractApiErrorMessage(e, '进入画布失败'))
    } finally {
      setSpawningCanvas(false)
    }
  }

  const handleSpawnTextNode = useCallback(
    async (content: string, meta: { role: DramaAgentMessage['role'] }) => {
      if (meta.role !== 'user' && meta.role !== 'assistant') return
      if (!canvasProjectId) {
        message.info('请先点击「打开出图画布」创建画布')
        return
      }
      const trimmed = content.trim()
      if (!trimmed) {
        message.warning('内容为空，无法添加到画布')
        return
      }
      const offset = agentTextSpawnRef.current
      agentTextSpawnRef.current += 1
      const pos = { x: 120 + offset * 32, y: 120 + offset * 24 }
      try {
        const res = await createCanvasNode(canvasProjectId, {
          node_type: 'text',
          title: meta.role === 'assistant' ? '助手回复' : '用户消息',
          position: pos,
          config: {
            text_mode: 'manual',
            content: trimmed,
            prompt: '',
            params: {},
            width: 260,
            height: 200,
          },
        })
        if (res.code === 'success') {
          message.success('已添加到画布，可在画布页查看')
        } else {
          message.error(res.message || '添加失败')
        }
      } catch (e) {
        message.error(extractApiErrorMessage(e, '添加到画布失败'))
      }
    },
    [canvasProjectId],
  )

  const resolveCanvasProjectId = useCallback(async (): Promise<string | undefined> => {
    if (canvasProjectId) return canvasProjectId
    if (!threadId) return undefined
    const res = await spawnAgentCanvas(threadId)
    const pid = res.data?.project_id
    if (pid) {
      setCanvasProjectId(pid)
      upsertThreadSession(threadId, { canvasProjectId: pid })
    }
    return pid
  }, [canvasProjectId, threadId])

  const handleSpawnImageTask = useCallback(
    async (task: CharacterImageTask) => {
      const nodeType = resolveAgentTaskNodeType(task)
      if (nodeType === 'video') {
        if (!videoModelsRef.current) {
          const res = await getModels('video')
          videoModelsRef.current = sortModelsByAdminOrder(res.data || [])
        }
      } else if (!imageModelsRef.current) {
        const res = await getModels('image')
        imageModelsRef.current = sortModelsByAdminOrder(res.data || [])
      }
      const models = nodeType === 'video' ? videoModelsRef.current : imageModelsRef.current
      const modelCode = pickDefaultModelCode(models || [])
      if (!modelCode) {
        message.warning(nodeType === 'video' ? '暂无可用出视频模型' : '暂无可用出图模型')
        return
      }
      let pid: string | undefined
      try {
        pid = await resolveCanvasProjectId()
      } catch (e) {
        message.error(extractApiErrorMessage(e, '绑定画布失败'))
        return
      }
      if (!pid) {
        message.info('请先点击「去画布出图」')
        return
      }
      const offset = agentImageSpawnRef.current
      agentImageSpawnRef.current += 1
      const pos = { x: 120 + offset * 48, y: 120 + offset * 36 }
      const config = buildCanvasNodeConfigFromAgentTask(task, {
        modelCode,
        stylePresetId,
        stylePresetName: selectedStyle?.name,
      })
      const nodeTitle = characterImageTaskButtonLabel(task)
      try {
        const createRes = await createCanvasNode(pid, {
          node_type: nodeType,
          title: nodeTitle,
          position: pos,
          config,
        })
        if (createRes.code !== 'success' || !createRes.data) {
          message.error(createRes.message || `创建${nodeType === 'video' ? '视频' : '出图'}节点失败`)
          return
        }
        message.success(`已创建「${nodeTitle}」节点，请在画布中手动运行`)
        openCanvasProject(pid)
      } catch (e) {
        message.error(extractApiErrorMessage(e, `创建${nodeType === 'video' ? '视频' : '出图'}节点失败`))
      }
    },
    [resolveCanvasProjectId, stylePresetId, selectedStyle?.name],
  )

  const canvasAction =
    threadId && messages.length > 0 ? (
      <Button
        size="small"
        type="primary"
        icon={<BlockOutlined />}
        loading={spawningCanvas}
        onClick={handleGoToCanvas}
      >
        {canvasProjectId ? '打开出图画布' : '去画布出图'}
      </Button>
    ) : null

  const topbarCanvasAction =
    threadId && messages.length > 0 ? (
      <Button
        size="small"
        icon={<BlockOutlined />}
        loading={spawningCanvas}
        onClick={handleGoToCanvas}
      >
        {canvasProjectId ? '打开出图画布' : '去画布出图'}
      </Button>
    ) : null

  useEffect(() => {
    if (!threadId) return
    upsertThreadSession(threadId, {
      messages,
      agentMode,
      modelCode,
      stylePresetId,
      multiEpisode,
      stage,
      suggestedNext,
      threadTitle,
      canvasProjectId,
    })
  }, [
    threadId,
    messages,
    agentMode,
    modelCode,
    stylePresetId,
    multiEpisode,
    stage,
    suggestedNext,
    threadTitle,
    canvasProjectId,
  ])

  if (hydrating && !messages.length) {
    return (
      <div className="drama-super-agent-page drama-super-agent-page--loading">
        <Spin size="large" tip="加载对话上下文…" />
      </div>
    )
  }

  return (
    <div className="drama-super-agent-page">
      {!started ? (
        <div className="drama-super-agent-page__landing">
          <DramaAgentComposer
            variant="landing"
            agentMode={agentMode}
            onAgentModeChange={setAgentMode}
            modelCode={modelCode}
            onModelCodeChange={setModelCode}
            models={models}
            stylePresetId={stylePresetId}
            onStylePresetChange={(id) => void handleStylePresetChange(id)}
            styles={styles}
            refs={refs}
            onRefsChange={setRefs}
            loading={loading}
            onSend={handleSend}
          />
        </div>
      ) : (
        <div className="drama-super-agent-page__chat">
          <div className="drama-super-agent-page__topbar">
            <span className="drama-super-agent-page__topbar-title">
              {threadTitle || getAgentModeLabel(agentMode)}
            </span>
            <Space wrap>
              {topbarCanvasAction}
              <Link to="/my-space">
                <Button size="small" icon={<FolderOutlined />}>
                  我的空间
                </Button>
              </Link>
              <Link to="/drama">
                <Button size="small" icon={<PlusOutlined />}>
                  新建对话
                </Button>
              </Link>
            </Space>
          </div>

          <DramaAgentChat
            messages={messages}
            loading={loading}
            stage={stage}
            suggestedNext={suggestedNext}
            agentMode={agentMode}
            modeLocked={started}
            stylePresetId={stylePresetId}
            styleName={selectedStyle?.name}
            liveProcessTrace={liveProcessTrace}
            threadId={threadId}
            scrollSurface="page"
            headerActions={canvasAction}
            onAddToCanvas={canvasProjectId ? handleSpawnTextNode : undefined}
            onSpawnImageTask={handleSpawnImageTask}
          />
          <div className="drama-super-agent-page__composer-bar">
            <DramaAgentComposer
              variant="compact"
              agentMode={agentMode}
              onAgentModeChange={setAgentMode}
              modeLocked={started}
              styleLocked={!!stylePresetId && started}
              modelCode={modelCode}
              onModelCodeChange={setModelCode}
              models={models}
              stylePresetId={stylePresetId}
              onStylePresetChange={(id) => void handleStylePresetChange(id)}
              styles={styles}
              refs={refs}
              onRefsChange={setRefs}
              loading={loading}
              onSend={handleSend}
            />
          </div>
        </div>
      )}
    </div>
  )
}
