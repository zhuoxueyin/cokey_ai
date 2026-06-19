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
import { PlusOutlined } from '@ant-design/icons'
import {
  getCanvasProject,
  updateCanvasProject,
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
import type { CanvasNode, CanvasNodeConfig, CanvasNodeType, CanvasProject } from '@/types/canvas'
import type { AssetItem } from '@/types'
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
  IMAGE_NODE_DEFAULT,
  computeImageNodeSize,
  loadImageDimensions,
  pickOutputImageUrl,
} from '@/utils/canvasNodeSize'
import ResourceNode from '@/components/canvas/nodes/ResourceNode'
import TextNode from '@/components/canvas/nodes/TextNode'
import ImageNode from '@/components/canvas/nodes/ImageNode'
import VideoNode from '@/components/canvas/nodes/VideoNode'
import CanvasEditorHeader from '@/components/canvas/CanvasEditorHeader'
import CanvasRunHistoryDrawer from '@/components/canvas/CanvasRunHistoryDrawer'
import AddNodePickerModal from '@/components/canvas/AddNodePickerModal'
import NodeInputPanel from '@/components/canvas/NodeInputPanel'
import NodeFloatingPanel from '@/components/canvas/NodeFloatingPanel'
import AssetPicker from '@/components/AssetPicker'
import GroupNode from '@/components/canvas/nodes/GroupNode'
import CanvasSelectionToolbar from '@/components/canvas/CanvasSelectionToolbar'
import {
  canUngroupSelection,
  computeGroupBounds,
  isGroupableFlowNode,
  nextGroupTitle,
  sortCanvasNodesForFlow,
} from '@/utils/canvasGroup'

const nodeTypes = {
  resource: ResourceNode,
  text: TextNode,
  image: ImageNode,
  video: VideoNode,
  group: GroupNode,
}

const DEFAULT_NODE_SIZE: Record<string, { width: number; height: number }> = {
  text: { width: 260, height: 200 },
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
    type: 'default',
    className: 'canvas-edge',
  }
}

function canShowEditPanel(node: CanvasNode): boolean {
  return (
    node.node_type !== 'resource' &&
    node.node_type !== 'group' &&
    !(node.node_type === 'text' && (node.config.text_mode || 'generate') === 'manual')
  )
}

function CanvasEditorInner() {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()
  const { userId } = useGenerationStore()
  const { getViewport, screenToFlowPosition, fitView, setViewport: rfSetViewport } = useReactFlow()
  const didInitialFitRef = useRef(false)
  const viewportInitializedRef = useRef(false)
  const [viewport, setViewport] = useState({ x: 0, y: 0, zoom: 0.8 })

  const [project, setProject] = useState<CanvasProject | null>(null)
  const [loading, setLoading] = useState(true)
  const [title, setTitle] = useState('')
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)
  const [panelVisible, setPanelVisible] = useState(false)
  const [runningNodeId, setRunningNodeId] = useState<string | null>(null)
  const [addModalOpen, setAddModalOpen] = useState(false)
  const [assetPickerOpen, setAssetPickerOpen] = useState(false)
  const [runHistoryOpen, setRunHistoryOpen] = useState(false)
  const [runHistoryRefresh, setRunHistoryRefresh] = useState(0)
  const [spawnFlowPos, setSpawnFlowPos] = useState<{ x: number; y: number } | null>(null)
  const [pendingConnect, setPendingConnect] = useState<{ sourceNodeId: string; flowPos: { x: number; y: number } } | null>(null)
  const connectDragRef = useRef<{ sourceNodeId: string } | null>(null)
  /** 框选进行中：避免 onSelectionChange 触发面板/重渲染打断框选 */
  const isSelectingRef = useRef(false)
  /** 框选刚结束：避免 mouseup 触发 pane click 清空选区 */
  const justFinishedSelectionRef = useRef(false)
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
  const workspaceRef = useRef<HTMLDivElement>(null)

  const selectedCanvasNode = selectedNodeId ? canvasNodesRef.current.get(selectedNodeId) || null : null

  const upstreamPreview = useMemo(() => {
    if (!selectedNodeId) return { texts: [], images: [], refs: [] }
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
        if (!projectId) return
        try {
          await updateCanvasNode(projectId, nodeId, { config })
        } catch {
          message.error('节点尺寸保存失败')
        }
      }, 300)
    },
    [projectId, setNodes],
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
          if (!projectId) return
          try {
            await updateCanvasNode(projectId, nodeId, { config, result })
          } catch {
            message.error('文本保存失败')
          }
        }, 400),
      )
    },
    [projectId, setNodes],
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
        onOpenPanel: supportsPanel
          ? () => {
              setSelectedNodeId(nodeId)
              setPanelVisible(true)
            }
          : undefined,
        onDuplicate: () => {
          copyNodeRef.current(nodeId)
        },
        onUpdateConfig: async (patch: Partial<CanvasNodeConfig>) => {
          if (!projectId) return
          const current = canvasNodesRef.current.get(nodeId)
          const merged = { ...(current?.config || {}), ...patch }
          updateLocalNode(nodeId, { config: merged })
          await updateCanvasNode(projectId, nodeId, { config: merged })
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
    [persistNodeSize, persistNodeText, primaryImageByNode, runningNodeId],
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
          data: { label: node.title },
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
          ...actions,
        },
        selected: node.node_id === selId,
      }
    },
    [primaryImageByNode],
  )

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
      const sel = keepSelection ?? selectedNodeId
      const sorted = sortCanvasNodesForFlow(proj.nodes || [])
      setNodes(sorted.map((n) => buildFlowNode(n, sel)))
      setEdges((proj.edges || []).map(toFlowEdge))
      setProject(proj)
      setTitle(proj.title)
    },
    [selectedNodeId, setNodes, setEdges],
  )

  const loadProject = useCallback(async () => {
    if (!projectId) return
    setLoading(true)
    try {
      const res = await getCanvasProject(projectId)
      if (res.code === 'success' && res.data) {
        let proj = res.data
        if (userId && userId !== 'default_user' && (!proj.user_id || proj.user_id === 'default_user')) {
          try {
            const claim = await updateCanvasProject(projectId, { user_id: userId })
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
        navigate('/canvas')
      }
    } catch {
      message.error('加载项目失败')
      navigate('/canvas')
    } finally {
      setLoading(false)
    }
  }, [projectId, navigate, refreshFromProject, userId])

  useEffect(() => {
    loadProject()
    return () => {
      if (resizeSaveTimerRef.current) window.clearTimeout(resizeSaveTimerRef.current)
      textSaveTimersRef.current.forEach((timer) => window.clearTimeout(timer))
      textSaveTimersRef.current.clear()
    }
  }, [loadProject])

  useEffect(() => {
    const preventSpaceScroll = (e: KeyboardEvent) => {
      if (e.code !== 'Space' && e.key !== ' ') return
      if (isTextEditingTarget(e.target)) return
      e.preventDefault()
    }
    window.addEventListener('keydown', preventSpaceScroll)
    return () => window.removeEventListener('keydown', preventSpaceScroll)
  }, [])

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
    if (!projectId) return
    if (syncTimerRef.current) window.clearTimeout(syncTimerRef.current)
    syncTimerRef.current = window.setTimeout(async () => {
      const viewport = getViewport()
      const nodeUpdates = nodes.map((n) => ({
        node_id: n.id,
        position: n.position,
        parent_id: n.parentId ?? null,
      }))
      try {
        await syncCanvasProject(projectId, {
          viewport: { x: viewport.x, y: viewport.y, zoom: viewport.zoom },
          nodes: nodeUpdates,
        })
      } catch {
        /* 静默 */
      }
    }, 800)
  }, [projectId, nodes, getViewport])

  const upstreamSyncKey = useMemo(() => {
    let key = edges.map((e) => e.id).join(',')
    canvasNodesRef.current.forEach((n) => {
      const primary = resolvePrimaryImageIndex(n.node_id, n, primaryImageByNode)
      key += `|${n.node_id}:${n.result_version}:${n.status}:${primary}`
    })
    return key
  }, [edges, primaryImageByNode])

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
  }, [projectId])

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
      setNodes((nds) =>
        nds.map((n) =>
          n.id === nodeId
            ? {
                ...n,
                width: updated.config.width ?? n.width,
                height: updated.config.height ?? n.height,
                data: {
                  canvasNode: updated,
                  primaryImageIndex,
                  selected: n.id === selectedNodeId,
                  upstream: collectUpstreamPreview(nodeId, edges, canvasNodesRef.current),
                  ...actions,
                },
              }
            : n,
        ),
      )
    },
    [selectedNodeId, setNodes, edges, primaryImageByNode],
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
    if (!projectId) return
    try {
      const res = await updateCanvasNode(projectId, nodeId, { config })
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

  const mountPastedNode = (node: CanvasNode, sourceNodeId: string) => {
    canvasNodesRef.current.set(node.node_id, node)
    if (node.node_type === 'image') {
      const src = canvasNodesRef.current.get(sourceNodeId)
      const primary = resolvePrimaryImageIndex(sourceNodeId, src, primaryImageByNode)
      setPrimaryImageByNode((prev) => ({ ...prev, [node.node_id]: primary }))
    }
    setNodes((nds) => [...nds, buildFlowNode(node, node.node_id)])
    setSelectedNodeId(node.node_id)
    setPanelVisible(canShowEditPanel(node))
  }

  copyNodeRef.current = (nodeId: string) => {
    if (!projectId) return
    nodeClipboardRef.current = { projectId, sourceNodeId: nodeId, pasteCount: 0 }
    message.success('已复制，Ctrl+V 粘贴')
  }

  pasteNodeRef.current = async (flowPos?: { x: number; y: number }) => {
    if (!projectId) return
    const clip = nodeClipboardRef.current
    if (!clip || clip.projectId !== projectId) {
      message.info('请先复制节点')
      return
    }
    const source = canvasNodesRef.current.get(clip.sourceNodeId)
    if (!source) {
      nodeClipboardRef.current = null
      message.warning('原节点已不存在，请重新复制')
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
      const res = await duplicateCanvasNode(projectId, clip.sourceNodeId, { position })
      if (res.code === 'success' && res.data) {
        mountPastedNode(res.data, clip.sourceNodeId)
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
    if (!projectId) return
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
        : { prompt: '', params: {}, width: def.width, height: def.height }
    const res = await createCanvasNode(projectId, { node_type: type, position: pos, config })
    if (res.code === 'success' && res.data) {
      canvasNodesRef.current.set(res.data.node_id, res.data)
      setNodes((nds) => [...nds, buildFlowNode(res.data!, res.data!.node_id)])
      setSelectedNodeId(res.data.node_id)
      setPanelVisible(canShowEditPanel(res.data))
      setSpawnFlowPos(null)
      setPendingConnect(null)
      if (connectSource) {
        await linkNewNode(res.data.node_id, connectSource)
      }
    } else {
      message.error(res.message || '添加失败')
    }
  }

  const handleUploadResource = async (file: File, flowPos?: { x: number; y: number }) => {
    if (!projectId) return
    const pos = getSpawnPosition(flowPos ?? spawnFlowPos ?? undefined)
    const res = await uploadCanvasResource(projectId, file, { x: pos.x, y: pos.y })
    if (res.code === 'success' && res.data) {
      canvasNodesRef.current.set(res.data.node_id, res.data)
      setNodes((nds) => [...nds, buildFlowNode(res.data!, res.data!.node_id)])
      setSelectedNodeId(res.data.node_id)
      setPanelVisible(false)
      setSpawnFlowPos(null)
      message.success('资源已上传')
    } else {
      message.error(res.message || '上传失败')
    }
  }

  const handlePickAssets = async (assets: AssetItem[]) => {
    if (!projectId || assets.length === 0) return
    const pos = getSpawnPosition(spawnFlowPos ?? undefined)
    for (let i = 0; i < assets.length; i++) {
      const asset = assets[i]
      const url = pickCdnUrl(asset)
      const isVideo = asset.category === 'video'
      const res = await createCanvasNode(projectId, {
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
  }

  const linkNewNode = useCallback(
    async (targetNodeId: string, sourceNodeId: string) => {
      if (!projectId) return false
      const res = await createCanvasEdge(projectId, {
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
              type: 'default',
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
    [projectId, setEdges],
  )

  const selectedFlowNodes = useMemo(() => nodes.filter((n) => n.selected), [nodes])
  const groupableSelected = useMemo(
    () => selectedFlowNodes.filter(isGroupableFlowNode),
    [selectedFlowNodes],
  )
  const canGroupSelection = groupableSelected.length >= 2
  const canUngroupSelectionFlag = canUngroupSelection(selectedFlowNodes)

  const handleGroup = useCallback(async () => {
    if (!projectId || groupableSelected.length < 2) return
    const bounds = computeGroupBounds(groupableSelected)
    const groupTitle = nextGroupTitle(Array.from(canvasNodesRef.current.values()))
    const groupRes = await createCanvasNode(projectId, {
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
      const rel = { x: n.position.x - bounds.x, y: n.position.y - bounds.y }
      const upd = await updateCanvasNode(projectId, n.id, { position: rel, parent_id: groupId })
      if (upd.code === 'success' && upd.data) {
        canvasNodesRef.current.set(n.id, upd.data)
      }
    }
    rebuildFlowNodes(groupId)
    setSelectedNodeId(groupId)
    setPanelVisible(false)
    message.success('已创建分组')
  }, [projectId, groupableSelected, rebuildFlowNodes])

  const handleUngroup = useCallback(async () => {
    if (!projectId || !canUngroupSelectionFlag) return
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
      const upd = await updateCanvasNode(projectId, child.id, { position: abs, parent_id: null })
      if (upd.code === 'success' && upd.data) {
        canvasNodesRef.current.set(child.id, upd.data)
      } else {
        const existing = canvasNodesRef.current.get(child.id)
        if (existing) {
          canvasNodesRef.current.set(child.id, { ...existing, parent_id: null, position: abs })
        }
      }
    }
    const del = await deleteCanvasNode(projectId, groupId)
    if (del.code !== 'success') {
      message.error(del.message || '解组失败')
      return
    }
    canvasNodesRef.current.delete(groupId)
    rebuildFlowNodes(children[0]?.id ?? null)
    setSelectedNodeId(children[0]?.id ?? null)
    message.success('已解组')
  }, [projectId, canUngroupSelectionFlag, selectedFlowNodes, nodes, rebuildFlowNodes])

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
      if (!drag || !projectId) return
      if (state.isValid && state.toNode) return

      const touch = 'changedTouches' in event ? event.changedTouches[0] : null
      const clientX = touch?.clientX ?? ('clientX' in event ? event.clientX : 0)
      const clientY = touch?.clientY ?? ('clientY' in event ? event.clientY : 0)
      const flowPos = screenToFlowPosition({ x: clientX, y: clientY })
      setPendingConnect({ sourceNodeId: drag.sourceNodeId, flowPos })
      setAddModalOpen(true)
    },
    [projectId, screenToFlowPosition],
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
    isSelectingRef.current = true
    justFinishedSelectionRef.current = false
    pendingSelectionRef.current = []
    setPanelVisible(false)
  }, [])

  const onSelectionEnd = useCallback(() => {
    isSelectingRef.current = false
    justFinishedSelectionRef.current = true
    applySelectionUI(pendingSelectionRef.current)
    window.setTimeout(() => {
      justFinishedSelectionRef.current = false
    }, 120)
  }, [applySelectionUI])

  const onSelectionChange = useCallback(({ nodes: selNodes }: { nodes: Node[] }) => {
    if (isSelectingRef.current) {
      pendingSelectionRef.current = selNodes
      return
    }
    applySelectionUI(selNodes)
  }, [applySelectionUI])

  const onConnect = useCallback(
    async (connection: Connection) => {
      connectDragRef.current = null
      setPendingConnect(null)
      if (!projectId || !connection.source || !connection.target) return
      const normalized: Connection = {
        ...connection,
        sourceHandle: connection.sourceHandle ?? 'output',
        targetHandle: connection.targetHandle ?? 'input',
      }
      const res = await createCanvasEdge(projectId, {
        source_node_id: normalized.source!,
        target_node_id: normalized.target!,
      })
      if (res.code === 'success' && res.data) {
        setEdges((eds) =>
          addEdge(
            {
              ...normalized,
              id: res.data!.edge_id,
              type: 'default',
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
    [projectId, setEdges, loadProject],
  )

  const onEdgesDelete = useCallback(
    async (deleted: Edge[]) => {
      if (!projectId) return
      for (const edge of deleted) {
        await deleteCanvasEdge(projectId, edge.id)
      }
    },
    [projectId],
  )

  const onPaneClick = useCallback((event: React.MouseEvent) => {
    if (isSelectingRef.current || justFinishedSelectionRef.current) return
    const target = event.target as HTMLElement
    if (target.closest('.react-flow__node')) return
    if (target.closest('.react-flow__selection')) return
    if (target.closest('.canvas-node-floating-panel')) return
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
          projectId
        ) {
          const cn = canvasNodesRef.current.get(ch.id)
          if (cn?.node_type === 'group') {
            const width = Math.round(ch.dimensions.width)
            const height = Math.round(ch.dimensions.height)
            const config = { ...cn.config, width, height }
            updateLocalNode(ch.id, { config })
            void updateCanvasNode(projectId, ch.id, { config })
          }
        }
      }
      onNodesChange(changes)
    },
    [onNodesChange, projectId, updateLocalNode],
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

  const handleRunNode = async (config: CanvasNodeConfig) => {
    if (!projectId || !selectedNodeId) return
    if (runInFlightRef.current === selectedNodeId) return
    runInFlightRef.current = selectedNodeId
    setRunningNodeId(selectedNodeId)
    updateLocalNode(selectedNodeId, {
      status: 'running',
      error_message: undefined,
      config: { ...selectedCanvasNode?.config, ...config },
    })
    try {
      const res = await runCanvasNode(projectId, selectedNodeId, {
        user_id: userId || undefined,
        config_override: config,
      })
      if (res.code === 'success' && res.data?.node) {
        await applyRunSuccessNode(selectedNodeId, res.data.node)
        message.success('生成成功')
      } else {
        updateLocalNode(selectedNodeId, { status: 'failed', error_message: res.message })
        message.error(res.message || '生成失败')
      }
    } catch (e: any) {
      updateLocalNode(selectedNodeId, { status: 'failed', error_message: e.message })
      message.error(e.message || '生成失败')
    } finally {
      runInFlightRef.current = null
      setRunningNodeId(null)
      setRunHistoryRefresh((v) => v + 1)
    }
  }

  const handleUpdateConfig = async (patch: Partial<CanvasNodeConfig>) => {
    if (!projectId || !selectedNodeId) return
    const primary = resolvePrimaryImageIndex(selectedNodeId, selectedCanvasNode || undefined, primaryImageByNode)
    const merged = { ...(selectedCanvasNode?.config || {}), ...patch, output_image_index: primary }
    updateLocalNode(selectedNodeId, { config: merged })
    await updateCanvasNode(projectId, selectedNodeId, { config: merged })
  }

  const handleAckStale = async () => {
    if (!projectId || !selectedNodeId) return
    const res = await ackCanvasNodeStale(projectId, selectedNodeId)
    if (res.code === 'success' && res.data) {
      updateLocalNode(selectedNodeId, res.data)
    }
  }

  const handleDeleteSelected = useCallback(async () => {
    if (!projectId || !selectedNodeId) return
    if (!confirm('确定删除该节点？')) return
    const res = await deleteCanvasNode(projectId, selectedNodeId)
    if (res.code === 'success') {
      canvasNodesRef.current.delete(selectedNodeId)
      setNodes((nds) => nds.filter((n) => n.id !== selectedNodeId))
      setEdges((eds) => eds.filter((e) => e.source !== selectedNodeId && e.target !== selectedNodeId))
      setSelectedNodeId(null)
      setPanelVisible(false)
    }
  }, [projectId, selectedNodeId, setNodes, setEdges])

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
        handleDeleteSelected()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [handleDeleteSelected, selectedNodeId])

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

  const showFloatingPanel =
    panelVisible &&
    !!selectedCanvasNode &&
    selectedCanvasNode.node_type !== 'resource' &&
    !(
      selectedCanvasNode.node_type === 'text' &&
      (selectedCanvasNode.config.text_mode || 'generate') === 'manual'
    )

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

  return (
    <div className="canvas-page canvas-page--standalone">
      <CanvasEditorHeader
        projectId={projectId!}
        title={title}
        onTitleChange={setTitle}
        userId={userId}
        onOpenRunHistory={() => setRunHistoryOpen(true)}
      />

      <CanvasRunHistoryDrawer
        open={runHistoryOpen}
        onClose={() => setRunHistoryOpen(false)}
        projectId={projectId!}
        refreshKey={runHistoryRefresh}
        onFocusNode={handleFocusNode}
      />

      <div
        className="canvas-workspace"
        ref={workspaceRef}
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
          onNodeClick={onNodeClick}
          onNodeDoubleClick={onNodeDoubleClick}
          onMoveStart={onMoveStart}
          nodeTypes={nodeTypes}
          viewport={viewport}
          onViewportChange={handleViewportChange}
          fitView={false}
          autoPanOnNodeFocus={false}
          autoPanOnConnect={false}
          autoPanOnSelection={false}
          nodesFocusable={false}
          elevateNodesOnSelect={false}
          selectNodesOnDrag={false}
          selectionOnDrag={false}
          panOnDrag
          panActivationKeyCode={null}
          selectionKeyCode="Space"
          multiSelectionKeyCode={['Control', 'Meta']}
          paneClickDistance={4}
          panOnScroll={false}
          minZoom={0.1}
          maxZoom={2}
          deleteKeyCode={null}
          defaultEdgeOptions={{ type: 'default', className: 'canvas-edge' }}
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
              running={runningNodeId === selectedNodeId}
              onRun={handleRunNode}
              onAckStale={handleAckStale}
              onUpdateConfig={handleUpdateConfig}
              onPanelDragStart={() => setPanelVisible(false)}
            />
          )}
        </NodeFloatingPanel>

        <div className="canvas-toolbar">
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
    </ReactFlowProvider>
  )
}
