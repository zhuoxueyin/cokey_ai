import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  type Connection,
  type Edge,
  type Node,
  type OnConnectEnd,
  type OnConnectStart,
  BackgroundVariant,
  ReactFlowProvider,
  useReactFlow,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { Spin, message } from 'antd'
import { PlusOutlined, AimOutlined } from '@ant-design/icons'
import {
  getCanvasProject,
  updateCanvasProject,
  createCanvasProject,
  createCanvasNode,
  createCanvasEdge,
  deleteCanvasEdge,
  deleteCanvasNode,
  duplicateCanvasNode,
  syncCanvasProject,
  runCanvasNode,
  ackCanvasNodeStale,
  updateCanvasNode,
  uploadCanvasResource,
} from '@/api/canvas'
import { getModels } from '@/api'
import type {
  CanvasNode,
  CanvasNodeConfig,
  CanvasNodeData,
  CanvasNodeType,
  CanvasProject,
} from '@/types/canvas'
import type { AssetItem } from '@/types'
import type { ModelItem } from '@/types'
import { useGenerationStore } from '@/store/generation'
import { pickCdnUrl } from '@/utils/cdnUrl'
import { collectUpstreamPreview } from '@/utils/canvasUpstream'
import { hasTextSelection, isOverlayPanelTarget, isTextEditingTarget } from '@/utils/keyboardEditing'
import {
  buildPrimaryImageMap,
  clampPrimaryImageIndex,
  resolvePrimaryImageIndex,
  upstreamPreviewKey,
  withPrimaryImageConfig,
} from '@/utils/canvasPrimaryImage'
import {
  listRunningCanvasNodeIds,
  shouldSyncCanvasNodeFromServer,
} from '@/utils/canvasNodeStatus'
import { mergeCanvasNodeConfig } from '@/utils/canvasNodeConfigPatch'
import {
  IMAGE_NODE_DEFAULT,
  computeImageNodeSize,
  loadImageDimensions,
  pickOutputImageUrl,
} from '@/utils/canvasNodeSize'
import { canvasEdgeTypes, canvasNodeTypes } from '@/components/canvas/canvasFlowRegistry'
import CanvasEditorHeader from '@/components/canvas/CanvasEditorHeader'
import CanvasRunHistoryDrawer from '@/components/canvas/CanvasRunHistoryDrawer'
import AddNodePickerModal from '@/components/canvas/AddNodePickerModal'
import NodeInputPanel from '@/components/canvas/NodeInputPanel'
import NodeFloatingPanel from '@/components/canvas/NodeFloatingPanel'
import TitleNodeEditPanel from '@/components/canvas/TitleNodeEditPanel'
import AssetPicker from '@/components/AssetPicker'
import CanvasSelectionToolbar from '@/components/canvas/CanvasSelectionToolbar'
import CanvasAgentPanelPortal from '@/components/drama/CanvasAgentPanelPortal'
import { canvasAgentBridge } from '@/utils/canvasAgentBridge'
import {
  buildCanvasNodeConfigFromAgentTask,
  characterImageTaskButtonLabel,
  resolveAgentTaskNodeType,
  type CharacterImageTask,
} from '@/utils/characterImageTasks'
import { pickDefaultModelCode, sortModelsByAdminOrder } from '@/utils/modelOrder'
import {
  canUngroupSelection,
  computeGroupBounds,
  isGroupableFlowNode,
  nextGroupTitle,
  sortCanvasNodesForFlow,
} from '@/utils/canvasGroup'
import { buildTitleRenderKey } from '@/utils/titleNodeStyles'
import {
  imageDuplicateNeedsServerRepair,
  sanitizeDuplicatedImageNode,
} from '@/utils/canvasDuplicateNode'

const DEFAULT_NODE_SIZE: Record<string, { width: number; height: number }> = {
  text: { width: 260, height: 200 },
  title: { width: 360, height: 96 },
  image: { ...IMAGE_NODE_DEFAULT },
  video: { width: 320, height: 240 },
  resource: { width: 280, height: 180 },
  group: { width: 320, height: 240 },
}

function toFlowEdge(edge: { edge_id: string; source_node_id: string; target_node_id: string }): Edge {
  return {
    id: edge.edge_id,
    source: edge.source_node_id,
    target: edge.target_node_id,
    sourceHandle: 'output',
    targetHandle: 'input',
    type: 'canvas',
    className: 'canvas-edge',
    selectable: true,
    focusable: true,
    deletable: true,
  }
}

function canShowEditPanel(node: CanvasNode): boolean {
  return (
    node.node_type !== 'resource' &&
    node.node_type !== 'group' &&
    node.node_type !== 'title' &&
    !(node.node_type === 'text' && (node.config.text_mode || 'generate') === 'manual')
  )
}

function CanvasEditorInner() {
  const { projectId: routeProjectId } = useParams<{ projectId: string }>()
  const isDraftRoute = routeProjectId === 'new'
  const navigate = useNavigate()
  const { userId } = useGenerationStore()
  const { getViewport, screenToFlowPosition, fitView, setViewport: rfSetViewport } = useReactFlow()
  const didInitialFitRef = useRef(false)
  const viewportInitializedRef = useRef(false)
  const activeProjectIdRef = useRef<string | null>(isDraftRoute ? null : routeProjectId ?? null)
  const skipLoadOnceRef = useRef(false)
  const persistPromiseRef = useRef<Promise<string> | null>(null)
  const [viewport, setViewport] = useState({ x: 0, y: 0, zoom: 0.8 })

  const [project, setProject] = useState<CanvasProject | null>(null)
  const [loading, setLoading] = useState(!isDraftRoute)
  const [title, setTitle] = useState('')
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)
  const selectedNodeIdRef = useRef<string | null>(null)
  const [panelVisible, setPanelVisible] = useState(false)
  const [runningNodeId, setRunningNodeId] = useState<string | null>(null)
  const [addModalOpen, setAddModalOpen] = useState(false)
  const [assetPickerOpen, setAssetPickerOpen] = useState(false)
  const [runHistoryOpen, setRunHistoryOpen] = useState(false)
  const [runHistoryRefresh, setRunHistoryRefresh] = useState(0)
  const [draggingNodeId, setDraggingNodeId] = useState<string | null>(null)
  const [spawnFlowPos, setSpawnFlowPos] = useState<{ x: number; y: number } | null>(null)
  const [pendingConnect, setPendingConnect] = useState<{ sourceNodeId: string; flowPos: { x: number; y: number } } | null>(null)
  const connectDragRef = useRef<{ sourceNodeId: string } | null>(null)
  /** 框选进行中：避免 onSelectionChange 触发面板/重渲染打断框选 */
  const isSelectingRef = useRef(false)
  /** 框选刚结束：避免 mouseup 触发 pane click 清空选区 */
  const justFinishedSelectionRef = useRef(false)
  /** 框选是否真的进入了拖拽阶段，用来避免 onSelectionEnd 把有效选区误清空 */
  const selectionStartedRef = useRef(false)
  /** 框选过程中的最新选区，在 onSelectionEnd 一次性应用 */
  const pendingSelectionRef = useRef<Node[]>([])
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([])
  const canvasNodesRef = useRef<Map<string, CanvasNode>>(new Map())
  /** 多图节点主图索引（运行时权威来源，避免 React Flow data 被覆盖后回退） */
  const [primaryImageByNode, setPrimaryImageByNode] = useState<Record<string, number>>({})
  const runInFlightRef = useRef<string | null>(null)
  const syncTimerRef = useRef<number | null>(null)
  const resizeSaveTimerRef = useRef<number | null>(null)
  const textSaveTimersRef = useRef<Map<string, number>>(new Map())
  const titleSaveTimersRef = useRef<Map<string, number>>(new Map())
  const titlePendingConfigRef = useRef<Map<string, CanvasNodeConfig>>(new Map())
  const persistNodeTitleRef = useRef<(nodeId: string, title: string) => void>(() => {})
  const flushTitleNodeSaveRef = useRef<(nodeId: string) => Promise<void>>(async () => {})
  const updateLocalNodeRef = useRef<(nodeId: string, patch: Partial<CanvasNode>) => void>(() => {})
  const workspaceRef = useRef<HTMLDivElement>(null)

  const selectedCanvasNode = useMemo(() => {
    if (!selectedNodeId) return null
    const flow = nodes.find((n) => n.id === selectedNodeId)
    const fromFlow = (flow?.data as CanvasNodeData | undefined)?.canvasNode
    return fromFlow ?? canvasNodesRef.current.get(selectedNodeId) ?? null
  }, [selectedNodeId, nodes])

  useEffect(() => {
    selectedNodeIdRef.current = selectedNodeId
  }, [selectedNodeId])

  const upstreamPreview = useMemo(() => {
    if (!selectedNodeId) return { texts: [], images: [], videos: [], refs: [] }
    return collectUpstreamPreview(selectedNodeId, edges, canvasNodesRef.current)
  }, [selectedNodeId, edges, nodes])

  const bindNodeActionsRef = useRef<(nodeId: string) => Record<string, unknown>>(() => ({}))
  const copyNodeRef = useRef<(nodeId: string) => void>(() => {})
  const pasteNodeRef = useRef<(flowPos?: { x: number; y: number }) => Promise<void>>(async () => {})
  const selectOutputImageRef = useRef<(nodeId: string, index: number) => Promise<void>>(async () => {})
  const nodeClipboardRef = useRef<{
    projectId: string
    sourceNodeId: string
    pasteCount: number
  } | null>(null)
  const lastPointerFlowPosRef = useRef<{ x: number; y: number } | null>(null)
  const agentTextSpawnRef = useRef(0)
  const agentImageSpawnRef = useRef(0)
  const imageModelsRef = useRef<ModelItem[] | null>(null)
  const videoModelsRef = useRef<ModelItem[] | null>(null)

  useEffect(() => {
    if (routeProjectId && routeProjectId !== 'new') {
      activeProjectIdRef.current = routeProjectId
    }
  }, [routeProjectId])

  const ensurePersisted = useCallback(async (): Promise<string> => {
    if (activeProjectIdRef.current) return activeProjectIdRef.current
    if (persistPromiseRef.current) return persistPromiseRef.current

    persistPromiseRef.current = (async () => {
      const res = await createCanvasProject({
        title: title.trim() || `画布 ${new Date().toLocaleDateString('zh-CN')}`,
        user_id: userId || undefined,
      })
      if (res.code !== 'success' || !res.data?.project_id) {
        persistPromiseRef.current = null
        throw new Error(res.message || '保存画布失败')
      }
      const id = res.data.project_id
      activeProjectIdRef.current = id
      setProject(res.data)
      skipLoadOnceRef.current = true
      navigate(`/canvas/${id}`, { replace: true })
      return id
    })()

    return persistPromiseRef.current
  }, [title, userId, navigate])

  const persistNodeSize = useCallback(
    (nodeId: string, width: number, height: number, options?: { userResized?: boolean }) => {
      const existing = canvasNodesRef.current.get(nodeId)
      if (!existing) return
      const userResized = options?.userResized ?? true
      const config = {
        ...existing.config,
        width: Math.round(width),
        height: Math.round(height),
        ...(userResized ? { user_resized: true } : {}),
      }
      const updated = { ...existing, config }
      canvasNodesRef.current.set(nodeId, updated)
      setNodes((nds) =>
        nds.map((n) =>
          n.id === nodeId
            ? {
                ...n,
                width: config.width,
                height: config.height,
                data: {
                  ...n.data,
                  canvasNode: updated,
                  ...bindNodeActionsRef.current(nodeId),
                },
              }
            : n,
        ),
      )
      if (resizeSaveTimerRef.current) window.clearTimeout(resizeSaveTimerRef.current)
      resizeSaveTimerRef.current = window.setTimeout(async () => {
        const pid = activeProjectIdRef.current
        if (!pid) return
        try {
          await updateCanvasNode(pid, nodeId, { config })
        } catch {
          message.error('节点尺寸保存失败')
        }
      }, 300)
    },
    [setNodes],
  )

  const persistNodeText = useCallback(
    (nodeId: string, text: string) => {
      const existing = canvasNodesRef.current.get(nodeId)
      if (!existing) return
      const textMode = existing.config.text_mode || 'generate'
      const result = { type: 'text' as const, text }
      const config =
        textMode === 'manual' ? { ...existing.config, content: text } : existing.config
      const updated = { ...existing, config, result, status: 'success' as const }
      canvasNodesRef.current.set(nodeId, updated)
      setNodes((nds) =>
        nds.map((n) =>
          n.id === nodeId
            ? {
                ...n,
                data: {
                  ...n.data,
                  canvasNode: updated,
                  ...bindNodeActionsRef.current(nodeId),
                },
              }
            : n,
        ),
      )
      const prev = textSaveTimersRef.current.get(nodeId)
      if (prev) window.clearTimeout(prev)
      textSaveTimersRef.current.set(
        nodeId,
        window.setTimeout(async () => {
          const pid = activeProjectIdRef.current
          if (!pid) return
          try {
            await updateCanvasNode(pid, nodeId, { config, result })
          } catch {
            message.error('文本保存失败')
          }
        }, 400),
      )
    },
    [setNodes],
  )

  const persistNodeTitle = useCallback(
    (nodeId: string, title: string) => {
      const existing = canvasNodesRef.current.get(nodeId)
      if (!existing) return
      const trimmed = title.trim()
      if (!trimmed || trimmed === existing.title) return
      const updated = { ...existing, title: trimmed }
      canvasNodesRef.current.set(nodeId, updated)
      setNodes((nds) =>
        nds.map((n) => {
          if (n.id !== nodeId) return n
          if (updated.node_type === 'group') {
            return {
              ...n,
              data: {
                ...n.data,
                label: trimmed,
                onTitleChange: (next: string) => persistNodeTitleRef.current(nodeId, next),
              },
            }
          }
          return {
            ...n,
            data: {
              ...n.data,
              canvasNode: updated,
              ...bindNodeActionsRef.current(nodeId),
            },
          }
        }),
      )
      const prev = titleSaveTimersRef.current.get(nodeId)
      if (prev) window.clearTimeout(prev)
      titleSaveTimersRef.current.set(
        nodeId,
        window.setTimeout(async () => {
          const pid = activeProjectIdRef.current
          if (!pid) return
          try {
            await updateCanvasNode(pid, nodeId, { title: trimmed })
          } catch {
            message.error('节点标题保存失败')
          }
        }, 400),
      )
    },
    [setNodes],
  )
  persistNodeTitleRef.current = persistNodeTitle

  const flushTitleNodeSave = useCallback(async (nodeId: string) => {
    const pendingTimer = titleSaveTimersRef.current.get(nodeId)
    if (pendingTimer) {
      window.clearTimeout(pendingTimer)
      titleSaveTimersRef.current.delete(nodeId)
    }
    const pendingConfig = titlePendingConfigRef.current.get(nodeId)
    const existing = canvasNodesRef.current.get(nodeId)
    if (!existing && !pendingConfig) return

    let pid = activeProjectIdRef.current
    if (!pid) {
      try {
        pid = await ensurePersisted()
      } catch {
        return
      }
    }

    const config = pendingConfig ?? existing?.config
    if (!config) return
    titlePendingConfigRef.current.delete(nodeId)

    try {
      await updateCanvasNode(pid, nodeId, { config })
      const latest = canvasNodesRef.current.get(nodeId)
      if (latest) {
        updateLocalNodeRef.current(nodeId, { config: latest.config })
      }
    } catch {
      message.error('标题节点保存失败')
    }
  }, [ensurePersisted])
  flushTitleNodeSaveRef.current = flushTitleNodeSave

  const persistTitleContent = useCallback(
    (nodeId: string, content: string, options?: { immediate?: boolean }) => {
      const existing = canvasNodesRef.current.get(nodeId)
      if (!existing) return
      const config = { ...existing.config, content }
      const updated = { ...existing, config }
      canvasNodesRef.current.set(nodeId, updated)
      titlePendingConfigRef.current.set(nodeId, config)
      updateLocalNodeRef.current(nodeId, { config })

      const prev = titleSaveTimersRef.current.get(nodeId)
      if (prev) window.clearTimeout(prev)

      if (options?.immediate) {
        void flushTitleNodeSaveRef.current(nodeId)
        return
      }

      titleSaveTimersRef.current.set(
        nodeId,
        window.setTimeout(() => {
          titleSaveTimersRef.current.delete(nodeId)
          void flushTitleNodeSaveRef.current(nodeId)
        }, 400),
      )
    },
    [],
  )

  const bindNodeActions = useCallback(
    (nodeId: string) => {
      const node = canvasNodesRef.current.get(nodeId)
      const supportsPanel = !!node && canShowEditPanel(node)
      const primaryImageIndex = resolvePrimaryImageIndex(nodeId, node, primaryImageByNode)

      return {
        onResizeEnd: (w: number, h: number) => persistNodeSize(nodeId, w, h, { userResized: true }),
        onAutoSize: (w: number, h: number) => persistNodeSize(nodeId, w, h, { userResized: false }),
        onResizeStart: () => setPanelVisible(false),
        onEditText: (text: string) => persistNodeText(nodeId, text),
        onTitleChange: (title: string) => persistNodeTitle(nodeId, title),
        onEditTitleContent: (content: string) => persistTitleContent(nodeId, content),
        onOpenPanel: supportsPanel
          ? () => {
              setSelectedNodeId(nodeId)
              setPanelVisible(true)
            }
          : undefined,
        onDuplicate: () => {
          copyNodeRef.current(nodeId)
          void pasteNodeRef.current()
        },
        onUpdateConfig: async (patch: Partial<CanvasNodeConfig>) => {
          const pid = activeProjectIdRef.current
          if (!pid) return
          const current = canvasNodesRef.current.get(nodeId)
          const merged = mergeCanvasNodeConfig(current?.config, patch)
          updateLocalNode(nodeId, { config: merged })
          await updateCanvasNode(pid, nodeId, { config: merged })
        },
        primaryImageIndex,
        onSelectPrimaryImage: (index: number) => {
          void selectOutputImageRef.current(nodeId, index)
        },
        onSelectOutputImage: (index: number) => {
          void selectOutputImageRef.current(nodeId, index)
        },
        activeRunNodeId: runningNodeId,
      }
    },
    [persistNodeSize, persistNodeText, persistNodeTitle, persistTitleContent, primaryImageByNode, runningNodeId],
  )

  bindNodeActionsRef.current = bindNodeActions

  const buildFlowNode = useCallback(
    (node: CanvasNode, selId?: string | null): Node => {
      if (node.node_type === 'group') {
        const width = node.config.width ?? DEFAULT_NODE_SIZE.group.width
        const height = node.config.height ?? DEFAULT_NODE_SIZE.group.height
        return {
          id: node.node_id,
          type: 'group',
          position: node.position || { x: 0, y: 0 },
          style: { width, height },
          data: {
            label: node.title,
            onTitleChange: (title: string) => persistNodeTitleRef.current(node.node_id, title),
          },
          draggable: true,
          selectable: true,
          selected: node.node_id === selId,
          zIndex: 0,
        }
      }
      const def = DEFAULT_NODE_SIZE[node.node_type] || { width: 280, height: 180 }
      const width = node.config.width ?? def.width
      const height = node.config.height ?? def.height
      const canvasNode = withPrimaryImageConfig(node, primaryImageByNode)
      const primaryImageIndex = resolvePrimaryImageIndex(node.node_id, canvasNode, primaryImageByNode)
      const actions = bindNodeActionsRef.current(node.node_id)
      const titleRenderKey =
        canvasNode.node_type === 'title' ? buildTitleRenderKey(canvasNode.config) : undefined
      return {
        id: node.node_id,
        type: node.node_type,
        position: node.position || { x: 0, y: 0 },
        width,
        height,
        parentId: node.parent_id || undefined,
        extent: node.parent_id ? ('parent' as const) : undefined,
        expandParent: Boolean(node.parent_id),
        data: {
          canvasNode,
          primaryImageIndex,
          selected: node.node_id === selId,
          ...(titleRenderKey ? { titleRenderKey } : {}),
          ...actions,
        },
        selected: node.node_id === selId,
      }
    },
    [primaryImageByNode],
  )

  const buildFlowNodeRef = useRef(buildFlowNode)
  buildFlowNodeRef.current = buildFlowNode

  const rebuildFlowNodes = useCallback(
    (selId?: string | null) => {
      const sorted = sortCanvasNodesForFlow(Array.from(canvasNodesRef.current.values()))
      setNodes(sorted.map((cn) => buildFlowNode(cn, selId)))
    },
    [buildFlowNode, setNodes],
  )

  const refreshFromProject = useCallback(
    (proj: CanvasProject, keepSelection?: string | null) => {
      const nodeMap = new Map<string, CanvasNode>()
      ;(proj.nodes || []).forEach((n) => nodeMap.set(n.node_id, n))
      canvasNodesRef.current = nodeMap
      const primaryMap = buildPrimaryImageMap(proj.nodes || [])
      setPrimaryImageByNode((prev) => {
        const merged = { ...primaryMap }
        for (const [id, idx] of Object.entries(prev)) {
          if (nodeMap.has(id)) merged[id] = idx
        }
        return merged
      })
      const sel = keepSelection ?? selectedNodeIdRef.current
      const sorted = sortCanvasNodesForFlow(proj.nodes || [])
      setNodes(sorted.map((n) => buildFlowNodeRef.current(n, sel)))
      setEdges((proj.edges || []).map(toFlowEdge))
      setProject(proj)
      setTitle(proj.title)
    },
    [setNodes, setEdges],
  )

  const loadProject = useCallback(async () => {
    if (!routeProjectId) return
    if (routeProjectId === 'new') {
      setLoading(false)
      setProject(null)
      setTitle(`画布 ${new Date().toLocaleDateString('zh-CN')}`)
      setNodes([])
      setEdges([])
      canvasNodesRef.current.clear()
      setPrimaryImageByNode({})
      return
    }
    if (skipLoadOnceRef.current) {
      skipLoadOnceRef.current = false
      setLoading(false)
      return
    }
    setLoading(true)
    try {
      const res = await getCanvasProject(routeProjectId)
      if (res.code === 'success' && res.data) {
        let proj = res.data
        if (userId && userId !== 'default_user' && (!proj.user_id || proj.user_id === 'default_user')) {
          try {
            const claim = await updateCanvasProject(routeProjectId, { user_id: userId })
            if (claim.code === 'success' && claim.data) {
              proj = { ...proj, user_id: claim.data.user_id }
            }
          } catch {
            /* 认领失败不影响编辑 */
          }
        }
        refreshFromProject(proj)
      } else {
        message.error(res.message || '加载失败')
        navigate('/my-space')
      }
    } catch {
      message.error('加载项目失败')
      navigate('/my-space')
    } finally {
      setLoading(false)
    }
  }, [routeProjectId, navigate, refreshFromProject, userId, setNodes, setEdges])

  useEffect(() => {
    void loadProject()
    return () => {
      if (resizeSaveTimerRef.current) window.clearTimeout(resizeSaveTimerRef.current)
      textSaveTimersRef.current.forEach((timer) => window.clearTimeout(timer))
      textSaveTimersRef.current.clear()
      titleSaveTimersRef.current.forEach((timer) => window.clearTimeout(timer))
      titleSaveTimersRef.current.clear()
    }
    // 仅路由切换时拉取项目，避免选区/节点状态变化误触发全量 reload
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [routeProjectId])

  const prevSelectedTitleRef = useRef<string | null>(null)
  useEffect(() => {
    const prev = prevSelectedTitleRef.current
    if (prev && prev !== selectedNodeId) {
      const prevNode = canvasNodesRef.current.get(prev)
      if (prevNode?.node_type === 'title') {
        void flushTitleNodeSaveRef.current(prev)
      }
    }
    prevSelectedTitleRef.current = selectedNodeId
  }, [selectedNodeId])

  useEffect(() => {
    if (loading || didInitialFitRef.current || nodes.length === 0) return
    if (project?.viewport) {
      didInitialFitRef.current = true
      return
    }
    didInitialFitRef.current = true
    fitView({ padding: 0.15, duration: 0 })
  }, [loading, nodes.length, project?.viewport, fitView])

  useEffect(() => {
    setNodes((nds) =>
      nds.map((n) => {
        const prev = (n.data as { activeRunNodeId?: string | null }).activeRunNodeId
        if (prev === runningNodeId) return n
        return { ...n, data: { ...n.data, activeRunNodeId: runningNodeId } }
      }),
    )
  }, [runningNodeId, setNodes])

  const scheduleSync = useCallback(() => {
    const pid = activeProjectIdRef.current
    if (!pid) return
    if (syncTimerRef.current) window.clearTimeout(syncTimerRef.current)
    syncTimerRef.current = window.setTimeout(async () => {
      const viewport = getViewport()
      const nodeUpdates = nodes.map((n) => ({
        node_id: n.id,
        position: n.position,
        parent_id: n.parentId ?? null,
      }))
      try {
        await syncCanvasProject(pid, {
          viewport: { x: viewport.x, y: viewport.y, zoom: viewport.zoom },
          nodes: nodeUpdates,
        })
      } catch {
        /* 静默 */
      }
    }, 800)
  }, [nodes, getViewport])

  const upstreamSyncKey = useMemo(() => {
    let key = edges.map((e) => e.id).join(',')
    canvasNodesRef.current.forEach((n) => {
      const primary = resolvePrimaryImageIndex(n.node_id, n, primaryImageByNode)
      key += `|${n.node_id}:${n.result_version}:${n.status}:${primary}`
    })
    return key
  }, [edges, primaryImageByNode])

  const runningNodeIds = useMemo(
    () =>
      nodes
        .map((n) => (n.data as CanvasNodeData | undefined)?.canvasNode)
        .filter((cn): cn is CanvasNode => !!cn && cn.status === 'running')
        .map((cn) => cn.node_id),
    [nodes],
  )

  /** 仅在上游引用变化时更新 data.upstream，避免全量 setNodes 导致画布闪烁 */
  useEffect(() => {
    setNodes((nds) => {
      let changed = false
      const next = nds.map((n) => {
        const upstream = collectUpstreamPreview(n.id, edges, canvasNodesRef.current)
        const prev = (n.data as { upstream?: { images: string[]; texts: string[] } }).upstream
        const prevKey = upstreamPreviewKey(prev?.images || [], prev?.texts || [])
        const nextKey = upstreamPreviewKey(upstream.images, upstream.texts)
        if (prevKey === nextKey) return n
        changed = true
        return { ...n, data: { ...n.data, upstream } }
      })
      return changed ? next : nds
    })
  }, [upstreamSyncKey, edges, setNodes])

  useEffect(() => {
    if (loading || !project?.viewport || viewportInitializedRef.current) return
    setViewport(project.viewport)
    rfSetViewport(project.viewport)
    viewportInitializedRef.current = true
  }, [loading, project?.viewport, rfSetViewport])

  useEffect(() => {
    didInitialFitRef.current = false
    viewportInitializedRef.current = false
  }, [routeProjectId])

  const nodeLayoutKey = useMemo(
    () =>
      nodes
        .map((n) => `${n.id}:${Math.round(n.position.x)}:${Math.round(n.position.y)}:${n.width ?? ''}:${n.height ?? ''}`)
        .join('|'),
    [nodes],
  )

  useEffect(() => {
    if (!loading) scheduleSync()
    return () => {
      if (syncTimerRef.current) window.clearTimeout(syncTimerRef.current)
    }
  }, [nodeLayoutKey, loading, scheduleSync])

  const updateLocalNode = useCallback(
    (nodeId: string, patch: Partial<CanvasNode>) => {
      const existing = canvasNodesRef.current.get(nodeId)
      if (!existing) return
      const mergedConfig = patch.config ? { ...existing.config, ...patch.config } : existing.config
      let updated = { ...existing, ...patch, config: mergedConfig }
      updated = withPrimaryImageConfig(updated, primaryImageByNode)
      canvasNodesRef.current.set(nodeId, updated)
      const primaryImageIndex = resolvePrimaryImageIndex(nodeId, updated, primaryImageByNode)
      const actions = bindNodeActionsRef.current(nodeId)
      const titleRenderKey =
        updated.node_type === 'title' ? buildTitleRenderKey(mergedConfig) : undefined
      setNodes((nds) =>
        nds.map((n) =>
          n.id === nodeId
            ? {
                ...n,
                width: updated.config.width ?? n.width,
                height: updated.config.height ?? n.height,
                data:
                  updated.node_type === 'group'
                    ? {
                        label: updated.title,
                        onTitleChange: (title: string) => persistNodeTitleRef.current(nodeId, title),
                      }
                    : {
                        canvasNode: updated,
                        primaryImageIndex,
                        selected: n.id === selectedNodeId,
                        upstream: collectUpstreamPreview(nodeId, edges, canvasNodesRef.current),
                        ...(titleRenderKey ? { titleRenderKey } : {}),
                        ...actions,
                      },
              }
            : n,
        ),
      )
    },
    [selectedNodeId, setNodes, edges, primaryImageByNode],
  )
  updateLocalNodeRef.current = updateLocalNode

  const handleTitleNodeUpdateConfig = useCallback(
    async (nodeId: string, patch: Partial<CanvasNodeConfig>) => {
      const existing = canvasNodesRef.current.get(nodeId)
      if (!existing) return
      const merged = { ...existing.config, ...patch }
      updateLocalNode(nodeId, { config: merged })
      titlePendingConfigRef.current.set(nodeId, merged)

      let pid: string
      try {
        pid = await ensurePersisted()
      } catch (e: unknown) {
        message.error(e instanceof Error ? e.message : '保存失败')
        return
      }
      try {
        await updateCanvasNode(pid, nodeId, { config: merged })
        titlePendingConfigRef.current.delete(nodeId)
      } catch {
        message.error('标题样式保存失败')
      }
    },
    [ensurePersisted, updateLocalNode],
  )

  const markDownstreamStale = useCallback(
    (sourceNodeId: string) => {
      const downstreamIds = edges.filter((e) => e.source === sourceNodeId).map((e) => e.target)
      for (const targetId of downstreamIds) {
        updateLocalNode(targetId, { input_stale: true })
      }
    },
    [edges, updateLocalNode],
  )

  selectOutputImageRef.current = async (nodeId: string, index: number) => {
    const existing = canvasNodesRef.current.get(nodeId)
    if (!existing) return
    const imageCount = existing.result?.images?.length ?? 0
    const clamped = clampPrimaryImageIndex(index, imageCount)
    setPrimaryImageByNode((prev) => ({ ...prev, [nodeId]: clamped }))
    const config = { ...existing.config, output_image_index: clamped }
    updateLocalNode(nodeId, { config })
    markDownstreamStale(nodeId)
    const pid = activeProjectIdRef.current
    if (!pid) return
    try {
      const res = await updateCanvasNode(pid, nodeId, { config })
      if (res.code === 'success' && res.data) {
        setPrimaryImageByNode((prev) => ({ ...prev, [nodeId]: clamped }))
        updateLocalNode(nodeId, {
          config: { ...config, ...res.data.config, output_image_index: clamped },
          updated_at: res.data.updated_at,
        })
      }
    } catch {
      message.error('主图选择保存失败')
    }
  }

  const mountPastedNode = (node: CanvasNode) => {
    const cleaned = sanitizeDuplicatedImageNode(node)
    canvasNodesRef.current.set(cleaned.node_id, cleaned)
    if (cleaned.node_type === 'image') {
      setPrimaryImageByNode((prev) => ({ ...prev, [cleaned.node_id]: 0 }))
    }
    setNodes((nds) => [...nds, buildFlowNode(cleaned, cleaned.node_id)])
    setSelectedNodeId(cleaned.node_id)
    setPanelVisible(canShowEditPanel(cleaned))
    canvasAgentBridge.notifyCanvasMutation()
    return cleaned
  }

  const clipProjectKey = routeProjectId || 'new'

  copyNodeRef.current = (nodeId: string) => {
    nodeClipboardRef.current = { projectId: clipProjectKey, sourceNodeId: nodeId, pasteCount: 0 }
    message.success('已复制，Ctrl+V 粘贴')
  }

  pasteNodeRef.current = async (flowPos?: { x: number; y: number }) => {
    const clip = nodeClipboardRef.current
    if (!clip || clip.projectId !== clipProjectKey) {
      message.info('请先复制节点')
      return
    }
    const source = canvasNodesRef.current.get(clip.sourceNodeId)
    if (!source) {
      nodeClipboardRef.current = null
      message.warning('原节点已不存在，请重新复制')
      return
    }
    let pid: string
    try {
      pid = await ensurePersisted()
    } catch (e: unknown) {
      message.error(e instanceof Error ? e.message : '保存失败')
      return
    }
    clip.pasteCount += 1
    const base = source.position || { x: 0, y: 0 }
    const pointer = flowPos ?? lastPointerFlowPosRef.current
    const position = pointer
      ? { x: Math.round(pointer.x - 40), y: Math.round(pointer.y - 30) }
      : {
          x: Math.round(base.x + 40 * clip.pasteCount),
          y: Math.round(base.y + 40 * clip.pasteCount),
        }
    try {
      const res = await duplicateCanvasNode(pid, clip.sourceNodeId, { position })
      if (res.code === 'success' && res.data) {
        const cleaned = mountPastedNode(res.data)
        if (imageDuplicateNeedsServerRepair(res.data)) {
          try {
            await updateCanvasNode(pid, cleaned.node_id, {
              status: 'idle',
              result: null,
              result_version: 0,
              task_id: null,
              error_message: null,
              input_stale: false,
              upstream_snapshot: {},
              config: cleaned.config,
            })
          } catch {
            /* 本地已清空，服务端修复失败不影响继续编辑 */
          }
        }
        message.success('已粘贴节点')
      } else {
        message.error(res.message || '粘贴失败')
      }
    } catch (err: unknown) {
      const ax = err as { response?: { status?: number; data?: { detail?: string; message?: string } }; message?: string }
      if (ax?.response?.status === 404 && ax.response.data?.detail === 'Not Found') {
        message.error('粘贴接口未就绪，请重启后端服务后重试')
        return
      }
      if (!ax?.response) {
        message.error(ax?.message || '粘贴失败')
      }
    }
  }

  const getSpawnPosition = (flowPos?: { x: number; y: number }) => {
    if (flowPos) return flowPos
    const vp = getViewport()
    const el = workspaceRef.current
    const w = el?.clientWidth ?? window.innerWidth
    const h = el?.clientHeight ?? window.innerHeight
    return {
      x: (-vp.x + w / 2) / vp.zoom - 140,
      y: (-vp.y + h / 2) / vp.zoom - 100,
    }
  }

  const handleAddNode = async (
    type: CanvasNodeType,
    flowPos?: { x: number; y: number },
    options?: { text_mode?: 'manual' | 'generate' },
  ) => {
    let pid: string
    try {
      pid = await ensurePersisted()
    } catch (e: unknown) {
      message.error(e instanceof Error ? e.message : '保存失败')
      return
    }
    const connectSource = pendingConnect?.sourceNodeId
    const pos = getSpawnPosition(flowPos ?? pendingConnect?.flowPos ?? spawnFlowPos ?? undefined)
    const def = DEFAULT_NODE_SIZE[type] || { width: 280, height: 180 }
    const config: CanvasNodeConfig =
      type === 'text'
        ? {
            text_mode: options?.text_mode || 'generate',
            prompt: '',
            params: {},
            width: def.width,
            height: def.height,
          }
        : type === 'title'
          ? {
              content: '标题',
              title_font_size: 26,
              color: '#ffffff',
              font_family: 'sans',
              width: def.width,
              height: def.height,
            }
          : { prompt: '', params: {}, width: def.width, height: def.height }
    const res = await createCanvasNode(pid, { node_type: type, position: pos, config })
    if (res.code === 'success' && res.data) {
      canvasNodesRef.current.set(res.data.node_id, res.data)
      setNodes((nds) => [...nds, buildFlowNode(res.data!, res.data!.node_id)])
      setSelectedNodeId(res.data.node_id)
      setPanelVisible(canShowEditPanel(res.data))
      setSpawnFlowPos(null)
      setPendingConnect(null)
      canvasAgentBridge.notifyCanvasMutation()
      if (connectSource) {
        await linkNewNode(res.data.node_id, connectSource)
      }
    } else {
      message.error(res.message || '添加失败')
    }
  }

  const handleSpawnAgentTextNode = useCallback(
    async (content: string, meta: { role: 'user' | 'assistant' }) => {
      const trimmed = content.trim()
      if (!trimmed) {
        message.warning('内容为空，无法添加到画布')
        return
      }
      let pid: string
      try {
        pid = await ensurePersisted()
      } catch (e: unknown) {
        message.error(e instanceof Error ? e.message : '保存失败')
        return
      }
      const base = getSpawnPosition()
      const offset = agentTextSpawnRef.current
      agentTextSpawnRef.current += 1
      const pos = { x: base.x + offset * 32, y: base.y + offset * 24 }
      const def = DEFAULT_NODE_SIZE.text
      const res = await createCanvasNode(pid, {
        node_type: 'text',
        title: meta.role === 'assistant' ? '助手回复' : '用户消息',
        position: pos,
        config: {
          text_mode: 'manual',
          content: trimmed,
          prompt: '',
          params: {},
          width: def.width,
          height: def.height,
        },
      })
      if (res.code === 'success' && res.data) {
        canvasNodesRef.current.set(res.data.node_id, res.data)
        setNodes((nds) => [...nds, buildFlowNode(res.data!, res.data!.node_id)])
        setSelectedNodeId(res.data.node_id)
        setPanelVisible(canShowEditPanel(res.data))
        message.success('已添加到画布')
        canvasAgentBridge.notifyCanvasMutation()
      } else {
        message.error(res.message || '添加失败')
      }
    },
    [ensurePersisted, setNodes],
  )
  canvasAgentBridge.spawnTextNodeRef.current = handleSpawnAgentTextNode

  const handleUploadResource = async (file: File, flowPos?: { x: number; y: number }) => {
    let pid: string
    try {
      pid = await ensurePersisted()
    } catch (e: unknown) {
      message.error(e instanceof Error ? e.message : '保存失败')
      return
    }
    const pos = getSpawnPosition(flowPos ?? spawnFlowPos ?? undefined)
    const res = await uploadCanvasResource(pid, file, { x: pos.x, y: pos.y })
    if (res.code === 'success' && res.data) {
      canvasNodesRef.current.set(res.data.node_id, res.data)
      setNodes((nds) => [...nds, buildFlowNode(res.data!, res.data!.node_id)])
      setSelectedNodeId(res.data.node_id)
      setPanelVisible(false)
      setSpawnFlowPos(null)
      message.success('资源已上传')
      canvasAgentBridge.notifyCanvasMutation()
    } else {
      message.error(res.message || '上传失败')
    }
  }

  const handlePickAssets = async (assets: AssetItem[]) => {
    if (assets.length === 0) return
    let pid: string
    try {
      pid = await ensurePersisted()
    } catch (e: unknown) {
      message.error(e instanceof Error ? e.message : '保存失败')
      return
    }
    const pos = getSpawnPosition(spawnFlowPos ?? undefined)
    for (let i = 0; i < assets.length; i++) {
      const asset = assets[i]
      const url = pickCdnUrl(asset)
      const isVideo = asset.category === 'video'
      const res = await createCanvasNode(pid, {
        node_type: 'resource',
        position: { x: pos.x + i * 40, y: pos.y + i * 30 },
        config: {
          resource_url: url,
          resource_type: isVideo ? 'video' : 'image',
          resource_name: asset.file_name,
        },
      })
      if (res.code === 'success' && res.data) {
        canvasNodesRef.current.set(res.data.node_id, res.data)
        setNodes((nds) => [...nds, buildFlowNode(res.data!)])
      }
    }
    setSpawnFlowPos(null)
    message.success(`已添加 ${assets.length} 个资源`)
    canvasAgentBridge.notifyCanvasMutation()
  }

  const linkNewNode = useCallback(
    async (targetNodeId: string, sourceNodeId: string) => {
      const pid = activeProjectIdRef.current
      if (!pid) return false
      const res = await createCanvasEdge(pid, {
        source_node_id: sourceNodeId,
        target_node_id: targetNodeId,
      })
      if (res.code === 'success' && res.data) {
        setEdges((eds) =>
          addEdge(
            {
              id: res.data!.edge_id,
              source: sourceNodeId,
              target: targetNodeId,
              sourceHandle: 'output',
              targetHandle: 'input',
              type: 'canvas',
              className: 'canvas-edge',
            },
            eds,
          ),
        )
        return true
      }
      message.error(res.message || '连线失败')
      return false
    },
    [setEdges],
  )

  const selectedFlowNodes = useMemo(() => nodes.filter((n) => n.selected), [nodes])
  const groupableSelected = useMemo(
    () => selectedFlowNodes.filter(isGroupableFlowNode),
    [selectedFlowNodes],
  )
  const canGroupSelection = groupableSelected.length >= 2
  const canUngroupSelectionFlag = canUngroupSelection(selectedFlowNodes)

  const handleGroup = useCallback(async () => {
    if (groupableSelected.length < 2) return
    let pid: string
    try {
      pid = await ensurePersisted()
    } catch (e: unknown) {
      message.error(e instanceof Error ? e.message : '保存失败')
      return
    }
    const bounds = computeGroupBounds(groupableSelected)
    const groupTitle = nextGroupTitle(Array.from(canvasNodesRef.current.values()))
    const groupRes = await createCanvasNode(pid, {
      node_type: 'group',
      title: groupTitle,
      position: { x: bounds.x, y: bounds.y },
      config: { width: bounds.width, height: bounds.height },
    })
    if (groupRes.code !== 'success' || !groupRes.data) {
      message.error(groupRes.message || '分组失败')
      return
    }
    const groupId = groupRes.data.node_id
    canvasNodesRef.current.set(groupId, groupRes.data)
    for (const n of groupableSelected) {
      const rel = {
        x: Math.round(n.position.x - bounds.x),
        y: Math.round(n.position.y - bounds.y),
      }
      const upd = await updateCanvasNode(pid, n.id, { position: rel, parent_id: groupId })
      if (upd.code === 'success' && upd.data) {
        canvasNodesRef.current.set(n.id, upd.data)
      }
    }
    rebuildFlowNodes(groupId)
    setSelectedNodeId(groupId)
    setPanelVisible(false)
    message.success('已创建分组')
  }, [groupableSelected, rebuildFlowNodes, ensurePersisted])

  const handleUngroup = useCallback(async () => {
    if (!canUngroupSelectionFlag) return
    const pid = activeProjectIdRef.current
    if (!pid) return
    let groupId: string | null = null
    if (selectedFlowNodes.length === 1 && selectedFlowNodes[0].type === 'group') {
      groupId = selectedFlowNodes[0].id
    } else {
      groupId = selectedFlowNodes[0]?.parentId ?? null
    }
    if (!groupId) return
    const groupNode = nodes.find((n) => n.id === groupId)
    const children = nodes.filter((n) => n.parentId === groupId)
    for (const child of children) {
      const abs = {
        x: Math.round((groupNode?.position.x ?? 0) + child.position.x),
        y: Math.round((groupNode?.position.y ?? 0) + child.position.y),
      }
      const upd = await updateCanvasNode(pid, child.id, { position: abs, parent_id: null })
      if (upd.code === 'success' && upd.data) {
        canvasNodesRef.current.set(child.id, upd.data)
      } else {
        const existing = canvasNodesRef.current.get(child.id)
        if (existing) {
          canvasNodesRef.current.set(child.id, { ...existing, parent_id: null, position: abs })
        }
      }
    }
    const del = await deleteCanvasNode(pid, groupId)
    if (del.code !== 'success') {
      message.error(del.message || '解组失败')
      return
    }
    canvasNodesRef.current.delete(groupId)
    rebuildFlowNodes(children[0]?.id ?? null)
    setSelectedNodeId(children[0]?.id ?? null)
    message.success('已解组')
  }, [canUngroupSelectionFlag, selectedFlowNodes, nodes, rebuildFlowNodes])

  const isValidConnection = useCallback(
    (edgeOrConn: Connection | Edge) => {
      const source = edgeOrConn.source
      const target = edgeOrConn.target
      if (!source || !target) return false
      if (source === target) return false
      const sourceNode = canvasNodesRef.current.get(source)
      const targetNode = canvasNodesRef.current.get(target)
      if (sourceNode?.node_type === 'group' || targetNode?.node_type === 'group') return false
      return true
    },
    [],
  )

  const onConnectStart: OnConnectStart = useCallback((_, params) => {
    if (params.handleId !== 'output' || !params.nodeId) return
    const cn = canvasNodesRef.current.get(params.nodeId)
    if (!cn || cn.node_type === 'group') return
    connectDragRef.current = { sourceNodeId: params.nodeId }
  }, [])

  const onConnectEnd: OnConnectEnd = useCallback(
    (event, state) => {
      const drag = connectDragRef.current
      connectDragRef.current = null
      if (!drag) return
      if (state.isValid && state.toNode) return

      const touch = 'changedTouches' in event ? event.changedTouches[0] : null
      const clientX = touch?.clientX ?? ('clientX' in event ? event.clientX : 0)
      const clientY = touch?.clientY ?? ('clientY' in event ? event.clientY : 0)
      const flowPos = screenToFlowPosition({ x: clientX, y: clientY })
      setPendingConnect({ sourceNodeId: drag.sourceNodeId, flowPos })
      setAddModalOpen(true)
    },
    [screenToFlowPosition],
  )

  const applySelectionUI = useCallback((selNodes: Node[]) => {
    if (selNodes.length === 0) {
      setSelectedNodeId(null)
      setPanelVisible(false)
      return
    }
    const primary = selNodes[selNodes.length - 1]
    setSelectedNodeId(primary.id)
    if (selNodes.length > 1) {
      setPanelVisible(false)
      return
    }
    const canvasNode = canvasNodesRef.current.get(primary.id)
    setPanelVisible(Boolean(canvasNode && canShowEditPanel(canvasNode)))
  }, [])

  const onSelectionStart = useCallback(() => {
    selectionStartedRef.current = true
    isSelectingRef.current = true
    justFinishedSelectionRef.current = false
    pendingSelectionRef.current = []
    setPanelVisible(false)
  }, [])

  const onSelectionEnd = useCallback(() => {
    justFinishedSelectionRef.current = true
    const pending = pendingSelectionRef.current
    try {
      if (selectionStartedRef.current || pending.length > 0) {
        applySelectionUI(pending)
      }
    } finally {
      isSelectingRef.current = false
      selectionStartedRef.current = false
    }
    window.setTimeout(() => {
      justFinishedSelectionRef.current = false
    }, 120)
  }, [applySelectionUI])

  useEffect(() => {
    const syncSelectingClass = (pressed: boolean) => {
      workspaceRef.current?.classList.toggle('canvas-workspace--selecting', pressed)
    }
    const preventSpaceScroll = (e: KeyboardEvent) => {
      if (e.code !== 'Space' && e.key !== ' ') return
      if (e.repeat) return
      if (isTextEditingTarget(e.target)) return
      if (isOverlayPanelTarget(e.target)) return
      e.preventDefault()
      syncSelectingClass(true)
    }
    const onKeyUp = (e: KeyboardEvent) => {
      if (e.code !== 'Space' && e.key !== ' ') return
      syncSelectingClass(false)
    }
    const onBlur = () => syncSelectingClass(false)
    window.addEventListener('keydown', preventSpaceScroll, { capture: true })
    window.addEventListener('keyup', onKeyUp, { capture: true })
    window.addEventListener('blur', onBlur)
    return () => {
      window.removeEventListener('keydown', preventSpaceScroll, { capture: true })
      window.removeEventListener('keyup', onKeyUp, { capture: true })
      window.removeEventListener('blur', onBlur)
      syncSelectingClass(false)
    }
  }, [])

  const onSelectionChange = useCallback(
    ({ nodes: selNodes, edges: selEdges }: { nodes: Node[]; edges: Edge[] }) => {
      if (justFinishedSelectionRef.current && selNodes.length === 0 && selEdges.length === 0) return
      if (isSelectingRef.current) {
        pendingSelectionRef.current = selNodes
        return
      }
      if (selEdges.length > 0 && selNodes.length === 0) {
        setSelectedNodeId(null)
        setPanelVisible(false)
        return
      }
      applySelectionUI(selNodes)
    },
    [applySelectionUI],
  )

  const onConnect = useCallback(
    async (connection: Connection) => {
      connectDragRef.current = null
      setPendingConnect(null)
      if (!connection.source || !connection.target) return
      let pid: string
      try {
        pid = await ensurePersisted()
      } catch (e: unknown) {
        message.error(e instanceof Error ? e.message : '保存失败')
        return
      }
      const normalized: Connection = {
        ...connection,
        sourceHandle: connection.sourceHandle ?? 'output',
        targetHandle: connection.targetHandle ?? 'input',
      }
      const res = await createCanvasEdge(pid, {
        source_node_id: normalized.source!,
        target_node_id: normalized.target!,
      })
      if (res.code === 'success' && res.data) {
        setEdges((eds) =>
          addEdge(
            {
              ...normalized,
              id: res.data!.edge_id,
              type: 'canvas',
              className: 'canvas-edge',
            },
            eds,
          ),
        )
        await loadProject()
      } else {
        message.error(res.message || '连接失败')
      }
    },
    [setEdges, loadProject, ensurePersisted],
  )

  const refreshNodesAfterEdgeDelete = useCallback(
    async (targetNodeIds: string[]) => {
      const pid = activeProjectIdRef.current
      if (!pid || targetNodeIds.length === 0) return
      try {
        const res = await getCanvasProject(pid)
        if (res.code !== 'success' || !res.data?.nodes) return
        const byId = new Map(res.data.nodes.map((n) => [n.node_id, n]))
        for (const id of targetNodeIds) {
          const serverNode = byId.get(id)
          if (serverNode) {
            updateLocalNode(id, {
              input_stale: serverNode.input_stale,
              upstream_snapshot: serverNode.upstream_snapshot,
            })
          }
        }
      } catch {
        /* 连线已删，节点 stale 同步失败不影响主流程 */
      }
    },
    [updateLocalNode],
  )

  const deleteSelectedEdges = useCallback(
    async (toDelete: Edge[]) => {
      if (toDelete.length === 0) return
      const pid = activeProjectIdRef.current
      if (!pid) return
      for (const edge of toDelete) {
        try {
          const res = await deleteCanvasEdge(pid, edge.id)
          if (res.code !== 'success') {
            message.error(res.message || '删除连线失败')
            return
          }
        } catch (e: unknown) {
          message.error(e instanceof Error ? e.message : '删除连线失败')
          return
        }
      }
      const deletedIds = new Set(toDelete.map((e) => e.id))
      setEdges((eds) => eds.filter((e) => !deletedIds.has(e.id)))
      const targetIds = [...new Set(toDelete.map((e) => e.target))]
      await refreshNodesAfterEdgeDelete(targetIds)
      canvasAgentBridge.notifyCanvasMutation()
      message.success(toDelete.length > 1 ? `已删除 ${toDelete.length} 条连线` : '已删除连线')
    },
    [setEdges, refreshNodesAfterEdgeDelete],
  )

  const onEdgesDelete = useCallback(
    (deleted: Edge[]) => {
      void deleteSelectedEdges(deleted)
    },
    [deleteSelectedEdges],
  )

  const onEdgeClick = useCallback((_event: React.MouseEvent, _edge: Edge) => {
    setSelectedNodeId(null)
    setPanelVisible(false)
  }, [])

  const onPaneClick = useCallback((event: React.MouseEvent) => {
    if (isSelectingRef.current || selectionStartedRef.current || justFinishedSelectionRef.current) return
    const target = event.target as HTMLElement
    if (target.closest('.react-flow__node')) return
    if (target.closest('.react-flow__selection')) return
    if (target.closest('.canvas-node-floating-panel')) return
    if (target.closest('.canvas-title-node-edit-panel')) return
    if (target.closest('.canvas-toolbar')) return
    if (target.closest('.canvas-selection-toolbar')) return
    setSelectedNodeId(null)
    setPanelVisible(false)
  }, [])

  const onCanvasDoubleClick = useCallback(
    (event: React.MouseEvent) => {
      const target = event.target as HTMLElement
      if (target.closest('.react-flow__node')) return
      if (target.closest('.canvas-node-floating-panel')) return
      if (target.closest('.canvas-toolbar')) return
      const flowPos = screenToFlowPosition({ x: event.clientX, y: event.clientY })
      setSpawnFlowPos(flowPos)
      setAddModalOpen(true)
    },
    [screenToFlowPosition],
  )

  const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    if (event.ctrlKey || event.metaKey) {
      return
    }
    const canvasNode = canvasNodesRef.current.get(node.id)
    setSelectedNodeId(node.id)
    if (canvasNode && canShowEditPanel(canvasNode)) {
      setPanelVisible(true)
    } else {
      setPanelVisible(false)
    }
  }, [])

  const onNodeDoubleClick = useCallback((_: React.MouseEvent, node: Node) => {
    const canvasNode = canvasNodesRef.current.get(node.id)
    if (!canvasNode) return
    setSelectedNodeId(node.id)
    if (canShowEditPanel(canvasNode)) setPanelVisible(true)
  }, [])

  const onNodesChangeWrapped = useCallback(
    (changes: Parameters<typeof onNodesChange>[0]) => {
      for (const ch of changes) {
        if (ch.type === 'position' && 'dragging' in ch) {
          if (ch.dragging) {
            setDraggingNodeId(ch.id)
          } else {
            setDraggingNodeId((prev) => (prev === ch.id ? null : prev))
          }
        }
        if (ch.type === 'position' && 'dragging' in ch && ch.dragging) {
          setPanelVisible(false)
        }
        if (ch.type === 'dimensions' && 'resizing' in ch && ch.resizing) {
          setPanelVisible(false)
        }
        if (
          ch.type === 'dimensions' &&
          'dimensions' in ch &&
          ch.dimensions &&
          !ch.resizing &&
          activeProjectIdRef.current
        ) {
          const cn = canvasNodesRef.current.get(ch.id)
          if (cn?.node_type === 'group') {
            const width = Math.round(ch.dimensions.width)
            const height = Math.round(ch.dimensions.height)
            const config = { ...cn.config, width, height }
            updateLocalNode(ch.id, { config })
            void updateCanvasNode(activeProjectIdRef.current, ch.id, { config })
          }
        }
      }
      onNodesChange(changes)
    },
    [onNodesChange, updateLocalNode],
  )

  const onMoveStart = useCallback((event?: MouseEvent | TouchEvent | null) => {
    if (isSelectingRef.current) return
    const target = event?.target ?? null
    if (isTextEditingTarget(target)) return
    if (target instanceof HTMLElement && target.closest('.canvas-node-floating-panel, .canvas-prompt-editor')) {
      return
    }
    setPanelVisible(false)
  }, [])

  const applyRunSuccessNode = useCallback(
    async (nodeId: string, node: CanvasNode) => {
      const imageCount = node.result?.images?.length ?? 0
      const prevPrimary = resolvePrimaryImageIndex(nodeId, node, primaryImageByNode)
      const clampedPrimary = clampPrimaryImageIndex(prevPrimary, imageCount)
      setPrimaryImageByNode((prev) => ({ ...prev, [nodeId]: clampedPrimary }))

      let patch: Partial<CanvasNode> = {
        ...node,
        status: 'success',
        error_message: undefined,
        config: { ...node.config, output_image_index: clampedPrimary },
      }
      const url = pickOutputImageUrl(node.result, clampedPrimary)
      if (node.node_type === 'image' && url && !node.config?.user_resized) {
        const { width, height } = await loadImageDimensions(url)
        if (width && height) {
          const size = computeImageNodeSize(width, height)
          patch = {
            ...patch,
            config: { ...patch.config!, width: size.width, height: size.height, output_image_index: clampedPrimary },
          }
        }
      }
      updateLocalNode(nodeId, patch)
      if (patch.config?.width && patch.config?.height) {
        setNodes((nds) =>
          nds.map((n) =>
            n.id === nodeId
              ? { ...n, width: patch.config!.width, height: patch.config!.height }
              : n,
          ),
        )
      }
    },
    [updateLocalNode, setNodes, primaryImageByNode],
  )

  const syncRunningNodesFromServer = useCallback(async () => {
    const pid = activeProjectIdRef.current
    if (!pid) return false
    const runningBefore = listRunningCanvasNodeIds(canvasNodesRef.current.values())
    if (runningBefore.length === 0) return false
    try {
      const res = await getCanvasProject(pid)
      if (res.code !== 'success' || !res.data?.nodes) return false
      let synced = false
      for (const serverNode of res.data.nodes) {
        const local = canvasNodesRef.current.get(serverNode.node_id)
        if (!local || !shouldSyncCanvasNodeFromServer(local, serverNode)) continue
        synced = true
        if (serverNode.status === 'success') {
          await applyRunSuccessNode(serverNode.node_id, serverNode)
        } else {
          updateLocalNode(serverNode.node_id, serverNode)
        }
      }
      return synced
    } catch {
      return false
    }
  }, [applyRunSuccessNode, updateLocalNode])

  useEffect(() => {
    if (loading || runningNodeIds.length === 0) return
    let cancelled = false
    const tick = async () => {
      if (cancelled) return
      await syncRunningNodesFromServer()
    }
    void tick()
    const timer = window.setInterval(() => void tick(), 2500)
    return () => {
      cancelled = true
      window.clearInterval(timer)
    }
  }, [loading, runningNodeIds.join(','), syncRunningNodesFromServer])

  const NODE_GENERATING_MSG = '节点正在生成中，请稍候'

  const isNodeGenerating = (nodeId: string) => {
    if (runInFlightRef.current === nodeId) return true
    return canvasNodesRef.current.get(nodeId)?.status === 'running'
  }

  const isGeneratingConflictMessage = (msg?: string | null) =>
    Boolean(msg?.includes('节点正在生成中') || msg?.includes('正在生成中'))

  const handleRunNode = async (config: CanvasNodeConfig) => {
    const nodeId = selectedNodeId
    if (!nodeId) return
    if (isNodeGenerating(nodeId)) {
      message.info(NODE_GENERATING_MSG)
      return
    }
    let pid: string
    try {
      pid = await ensurePersisted()
    } catch (e: unknown) {
      message.error(e instanceof Error ? e.message : '保存失败')
      return
    }
    const baseConfig = canvasNodesRef.current.get(nodeId)?.config
    runInFlightRef.current = nodeId
    setRunningNodeId(nodeId)
    updateLocalNode(nodeId, {
      status: 'running',
      error_message: undefined,
      config: { ...baseConfig, ...config },
    })
    try {
      const res = await runCanvasNode(pid, nodeId, {
        user_id: userId || undefined,
        config_override: config,
      })
      if (res.code === 'success' && res.data?.node) {
        await applyRunSuccessNode(nodeId, res.data.node)
        message.success('生成成功')
      } else if (isGeneratingConflictMessage(res.message)) {
        updateLocalNode(nodeId, {
          status: 'running',
          error_message: undefined,
          config: { ...baseConfig, ...config },
        })
        message.info(res.message || NODE_GENERATING_MSG)
      } else {
        updateLocalNode(nodeId, { status: 'failed', error_message: res.message })
        message.error(res.message || '生成失败')
      }
    } catch (e: unknown) {
      const errMsg = e instanceof Error ? e.message : '生成失败'
      if (isGeneratingConflictMessage(errMsg)) {
        updateLocalNode(nodeId, { status: 'running', error_message: undefined })
        message.info(errMsg)
      } else {
        const synced = await syncRunningNodesFromServer()
        const latest = canvasNodesRef.current.get(nodeId)
        if (synced && latest?.status === 'success') {
          message.success('生成成功')
        } else if (latest?.status === 'failed') {
          message.error(latest.error_message || errMsg)
        } else if (latest?.status === 'running') {
          message.warning('连接中断，正在等待服务端结果…')
        } else {
          updateLocalNode(nodeId, { status: 'failed', error_message: errMsg })
          message.error(errMsg)
        }
      }
    } finally {
      if (runInFlightRef.current === nodeId) runInFlightRef.current = null
      const latest = canvasNodesRef.current.get(nodeId)
      if (latest?.status !== 'running') {
        setRunningNodeId((current) => (current === nodeId ? null : current))
      }
      setRunHistoryRefresh((v) => v + 1)
    }
  }

  const handleSpawnAgentImageTask = useCallback(
    async (
      task: CharacterImageTask,
      opts: { modelCode?: string; stylePresetId?: string; stylePresetName?: string },
    ) => {
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
      const defaultCode = pickDefaultModelCode(models || [])
      const modelCode =
        (opts.modelCode && models?.some((m) => m.model_code === opts.modelCode)
          ? opts.modelCode
          : defaultCode) || undefined
      if (!modelCode) {
        message.warning(nodeType === 'video' ? '暂无可用出视频模型' : '暂无可用出图模型')
        return
      }
      let pid: string
      try {
        pid = await ensurePersisted()
      } catch (e: unknown) {
        message.error(e instanceof Error ? e.message : '保存失败')
        return
      }
      const base = getSpawnPosition()
      const offset = agentImageSpawnRef.current
      agentImageSpawnRef.current += 1
      const pos = { x: base.x + offset * 48, y: base.y + offset * 36 }
      const def = nodeType === 'video' ? DEFAULT_NODE_SIZE.video : DEFAULT_NODE_SIZE.image
      const config = buildCanvasNodeConfigFromAgentTask(task, {
        modelCode,
        stylePresetId: opts.stylePresetId,
        stylePresetName: opts.stylePresetName,
        width: def.width,
        height: def.height,
      })
      const nodeTitle = characterImageTaskButtonLabel(task)
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
      const nodeId = createRes.data.node_id
      canvasNodesRef.current.set(nodeId, createRes.data)
      setNodes((nds) => [...nds, buildFlowNode(createRes.data!, nodeId)])
      setSelectedNodeId(nodeId)
      setPanelVisible(canShowEditPanel(createRes.data))
      canvasAgentBridge.notifyCanvasMutation()
      message.success(`已创建「${nodeTitle}」节点，可在画布中手动运行`)
    },
    [ensurePersisted, setNodes, userId],
  )
  canvasAgentBridge.spawnImageTaskRef.current = handleSpawnAgentImageTask
  canvasAgentBridge.ensureCanvasPersistedRef.current = ensurePersisted

  const handleUpdateConfig = async (patch: Partial<CanvasNodeConfig>) => {
    if (!selectedNodeId) return
    const current = canvasNodesRef.current.get(selectedNodeId)
    const primary = resolvePrimaryImageIndex(selectedNodeId, current, primaryImageByNode)
    const merged = mergeCanvasNodeConfig(current?.config, { ...patch, output_image_index: primary })
    updateLocalNode(selectedNodeId, { config: merged })
    const pid = activeProjectIdRef.current
    if (!pid) return
    await updateCanvasNode(pid, selectedNodeId, { config: merged })
  }

  const handleAckStale = async () => {
    if (!selectedNodeId) return
    const pid = activeProjectIdRef.current
    if (!pid) return
    const res = await ackCanvasNodeStale(pid, selectedNodeId)
    if (res.code === 'success' && res.data) {
      updateLocalNode(selectedNodeId, res.data)
    }
  }

  const handleDeleteSelected = useCallback(async () => {
    if (!selectedNodeId) return
    const pid = activeProjectIdRef.current
    if (!pid) return
    if (!confirm('确定删除该节点？')) return
    const res = await deleteCanvasNode(pid, selectedNodeId)
    if (res.code === 'success') {
      canvasNodesRef.current.delete(selectedNodeId)
      setNodes((nds) => nds.filter((n) => n.id !== selectedNodeId))
      setEdges((eds) => eds.filter((e) => e.source !== selectedNodeId && e.target !== selectedNodeId))
      setSelectedNodeId(null)
      setPanelVisible(false)
    }
  }, [selectedNodeId, setNodes, setEdges])

  const handleDeleteSelectedRef = useRef(handleDeleteSelected)
  handleDeleteSelectedRef.current = handleDeleteSelected
  const deleteSelectedEdgesRef = useRef(deleteSelectedEdges)
  deleteSelectedEdgesRef.current = deleteSelectedEdges
  const edgesRef = useRef(edges)
  edgesRef.current = edges

  useEffect(() => {
      const onKey = (e: KeyboardEvent) => {
      if (isTextEditingTarget(e.target)) return
      const mod = e.ctrlKey || e.metaKey
      if (mod && e.key.toLowerCase() === 'c') {
        if (isTextEditingTarget(e.target)) return
        if (hasTextSelection()) return
        if (isOverlayPanelTarget(e.target)) return
        if (!selectedNodeId) return
        e.preventDefault()
        copyNodeRef.current(selectedNodeId)
        return
      }
      if (mod && (e.key.toLowerCase() === 'v' || e.key.toLowerCase() === 'd')) {
        e.preventDefault()
        void pasteNodeRef.current()
        return
      }
      if (e.key === 'Delete' || e.key === 'Backspace') {
        if (isOverlayPanelTarget(e.target)) return
        const selectedEdges = edgesRef.current.filter((ed) => ed.selected)
        if (selectedEdges.length > 0) {
          e.preventDefault()
          void deleteSelectedEdgesRef.current(selectedEdges)
          return
        }
        void handleDeleteSelectedRef.current()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [selectedNodeId])

  const handleViewportChange = useCallback((vp: { x: number; y: number; zoom: number }) => {
    setViewport(vp)
  }, [])

  const handleFocusNode = useCallback(
    (nodeId: string) => {
      setSelectedNodeId(nodeId)
      setPanelVisible(true)
      setNodes((nds) => nds.map((n) => ({ ...n, selected: n.id === nodeId })))
      window.setTimeout(() => {
        fitView({ nodes: [{ id: nodeId }], padding: 0.35, duration: 280, maxZoom: 1.2 })
      }, 40)
    },
    [fitView, setNodes],
  )

  const handleRecenterWorkspace = useCallback(() => {
    if (nodes.length > 0) {
      fitView({ padding: 0.18, duration: 280, maxZoom: 1.15 })
      return
    }
    rfSetViewport({ x: 0, y: 0, zoom: 0.8 }, { duration: 280 })
  }, [nodes.length, fitView, rfSetViewport])

  const showFloatingPanel =
    panelVisible &&
    !!selectedCanvasNode &&
    selectedCanvasNode.node_type !== 'resource' &&
    !(
      selectedCanvasNode.node_type === 'text' &&
      (selectedCanvasNode.config.text_mode || 'generate') === 'manual'
    )

  const showTitleEditPanel =
    !!selectedNodeId &&
    selectedFlowNodes.length === 1 &&
    selectedCanvasNode?.node_type === 'title' &&
    draggingNodeId !== selectedNodeId

  const selectedFlowNode = useMemo(
    () => (selectedNodeId ? nodes.find((n) => n.id === selectedNodeId) : undefined),
    [nodes, selectedNodeId],
  )

  if (loading) {
    return (
      <div className="canvas-page canvas-page--standalone canvas-page--loading">
        <Spin size="large" tip="加载画布…" />
      </div>
    )
  }

  const headerProjectId = routeProjectId ?? 'new'

  return (
    <div className="canvas-page canvas-page--standalone">
      <CanvasEditorHeader
        projectId={headerProjectId}
        isDraft={isDraftRoute && !activeProjectIdRef.current}
        title={title}
        onTitleChange={setTitle}
        userId={userId}
        onOpenRunHistory={routeProjectId && routeProjectId !== 'new' ? () => setRunHistoryOpen(true) : undefined}
      />

      {routeProjectId && routeProjectId !== 'new' && (
        <CanvasRunHistoryDrawer
          open={runHistoryOpen}
          onClose={() => setRunHistoryOpen(false)}
          projectId={routeProjectId}
          refreshKey={runHistoryRefresh}
          onFocusNode={handleFocusNode}
        />
      )}

      <div
        className="canvas-workspace"
        ref={(el) => {
          if (workspaceRef.current !== el) {
            ;(workspaceRef as { current: HTMLDivElement | null }).current = el
          }
          canvasAgentBridge.setWorkspaceEl(el)
        }}
        onMouseMove={(e) => {
          lastPointerFlowPosRef.current = screenToFlowPosition({ x: e.clientX, y: e.clientY })
        }}
      >
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onPaneClick={onPaneClick}
          onDoubleClick={onCanvasDoubleClick}
          zoomOnDoubleClick={false}
          onNodesChange={onNodesChangeWrapped}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onConnectStart={onConnectStart}
          onConnectEnd={onConnectEnd}
          onSelectionChange={onSelectionChange}
          onSelectionStart={onSelectionStart}
          onSelectionEnd={onSelectionEnd}
          isValidConnection={isValidConnection}
          connectionRadius={56}
          onEdgesDelete={onEdgesDelete}
          onEdgeClick={onEdgeClick}
          onNodeClick={onNodeClick}
          onNodeDoubleClick={onNodeDoubleClick}
          onMoveStart={onMoveStart}
          nodeTypes={canvasNodeTypes}
          edgeTypes={canvasEdgeTypes}
          viewport={viewport}
          onViewportChange={handleViewportChange}
          fitView={false}
          autoPanOnNodeFocus={false}
          autoPanOnConnect={false}
          autoPanOnSelection={false}
          nodesFocusable={false}
          elevateNodesOnSelect={false}
          selectNodesOnDrag={false}
          selectionKeyCode="Space"
          selectionOnDrag
          panOnDrag
          panActivationKeyCode={null}
          preventScrolling
          multiSelectionKeyCode={['Control', 'Meta']}
          paneClickDistance={4}
          panOnScroll={false}
          minZoom={0.1}
          maxZoom={2}
          edgesFocusable
          deleteKeyCode={null}
          defaultEdgeOptions={{
            type: 'canvas',
            className: 'canvas-edge',
            selectable: true,
            focusable: true,
            deletable: true,
            interactionWidth: 28,
          }}
          proOptions={{ hideAttribution: true }}
        >
          <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#333" />
          <Controls className="canvas-controls" showInteractive={false} />
          <MiniMap className="canvas-minimap" zoomable pannable nodeColor="#444" maskColor="rgba(0,0,0,0.6)" />
        </ReactFlow>

        <NodeFloatingPanel
          nodeId={selectedNodeId}
          visible={showFloatingPanel}
          anchorWidth={selectedFlowNode?.width as number | undefined}
          anchorHeight={selectedFlowNode?.height as number | undefined}
        >
          {selectedCanvasNode && (
            <NodeInputPanel
              node={selectedCanvasNode}
              upstream={upstreamPreview}
              running={
                runningNodeId === selectedNodeId || selectedCanvasNode.status === 'running'
              }
              onRun={handleRunNode}
              onAckStale={handleAckStale}
              onUpdateConfig={handleUpdateConfig}
              onPanelDragStart={() => setPanelVisible(false)}
            />
          )}
        </NodeFloatingPanel>

        <TitleNodeEditPanel
          nodeId={selectedNodeId}
          visible={showTitleEditPanel}
          node={selectedCanvasNode?.node_type === 'title' ? selectedCanvasNode : null}
          onUpdateConfig={handleTitleNodeUpdateConfig}
          onEditContent={(id, content, options) => persistTitleContent(id, content, options)}
        />

        <div className="canvas-toolbar">
          <button
            type="button"
            className="canvas-toolbar__recenter"
            onClick={handleRecenterWorkspace}
            title="回到工作区"
            aria-label="回到工作区"
          >
            <AimOutlined />
          </button>
          <button type="button" className="canvas-toolbar__add" onClick={() => setAddModalOpen(true)} title="添加节点">
            <PlusOutlined />
          </button>
        </div>

        <CanvasSelectionToolbar
          selectedCount={selectedFlowNodes.length}
          canGroup={canGroupSelection}
          canUngroup={canUngroupSelectionFlag}
          onGroup={() => void handleGroup()}
          onUngroup={() => void handleUngroup()}
        />

      </div>

      <AddNodePickerModal
        open={addModalOpen}
        onClose={() => {
          setAddModalOpen(false)
          setSpawnFlowPos(null)
          setPendingConnect(null)
          connectDragRef.current = null
        }}
        onAddNode={(type, options) => handleAddNode(type, spawnFlowPos ?? undefined, options)}
        onUpload={(file) => handleUploadResource(file, spawnFlowPos ?? undefined)}
        onPickLibrary={() => setAssetPickerOpen(true)}
      />

      <AssetPicker
        open={assetPickerOpen}
        onClose={() => setAssetPickerOpen(false)}
        onSelect={handlePickAssets}
        category="image"
        multiple
      />
    </div>
  )
}

export default function CanvasEditor() {
  return (
    <ReactFlowProvider>
      <CanvasEditorInner />
      <CanvasAgentPanelPortal />
    </ReactFlowProvider>
  )
}
