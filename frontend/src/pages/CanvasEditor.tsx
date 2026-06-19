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
  BackgroundVariant,
  ReactFlowProvider,
  useReactFlow,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { Spin, message } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import {
  getCanvasProject,
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
import AddNodePickerModal from '@/components/canvas/AddNodePickerModal'
import NodeInputPanel from '@/components/canvas/NodeInputPanel'
import NodeFloatingPanel from '@/components/canvas/NodeFloatingPanel'
import AssetPicker from '@/components/AssetPicker'

const nodeTypes = {
  resource: ResourceNode,
  text: TextNode,
  image: ImageNode,
  video: VideoNode,
}

const DEFAULT_NODE_SIZE: Record<string, { width: number; height: number }> = {
  text: { width: 260, height: 200 },
  image: { ...IMAGE_NODE_DEFAULT },
  video: { width: 320, height: 240 },
  resource: { width: 280, height: 180 },
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
  const [spawnFlowPos, setSpawnFlowPos] = useState<{ x: number; y: number } | null>(null)
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([])
  const canvasNodesRef = useRef<Map<string, CanvasNode>>(new Map())
  /** 多图节点主图索引（运行时权威来源，避免 React Flow data 被覆盖后回退） */
  const [primaryImageByNode, setPrimaryImageByNode] = useState<Record<string, number>>({})
  const syncTimerRef = useRef<number | null>(null)
  const resizeSaveTimerRef = useRef<number | null>(null)
  const textSaveTimersRef = useRef<Map<string, number>>(new Map())
  const workspaceRef = useRef<HTMLDivElement>(null)

  const selectedCanvasNode = selectedNodeId ? canvasNodesRef.current.get(selectedNodeId) || null : null

  const upstreamPreview = useMemo(() => {
    if (!selectedNodeId) return { texts: [], images: [] }
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
        primaryImageIndex,
        onSelectPrimaryImage: (index: number) => {
          void selectOutputImageRef.current(nodeId, index)
        },
        onSelectOutputImage: (index: number) => {
          void selectOutputImageRef.current(nodeId, index)
        },
      }
    },
    [persistNodeSize, persistNodeText, primaryImageByNode],
  )

  bindNodeActionsRef.current = bindNodeActions

  const buildFlowNode = useCallback(
    (node: CanvasNode, selId?: string | null): Node => {
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
      setNodes(
        (proj.nodes || []).map((n) => {
          const canvasNode = withPrimaryImageConfig(n, primaryMap)
          const primaryImageIndex = resolvePrimaryImageIndex(n.node_id, canvasNode, primaryMap)
          const def = DEFAULT_NODE_SIZE[n.node_type] || { width: 280, height: 180 }
          const actions = bindNodeActionsRef.current(n.node_id)
          return {
            id: n.node_id,
            type: n.node_type,
            position: n.position || { x: 0, y: 0 },
            width: canvasNode.config.width ?? def.width,
            height: canvasNode.config.height ?? def.height,
            data: {
              canvasNode,
              primaryImageIndex,
              selected: n.node_id === sel,
              ...actions,
            },
            selected: n.node_id === sel,
          }
        }),
      )
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
        if (userId && !proj.user_id) {
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
    if (loading || didInitialFitRef.current || nodes.length === 0) return
    if (project?.viewport) {
      didInitialFitRef.current = true
      return
    }
    didInitialFitRef.current = true
    fitView({ padding: 0.15, duration: 0 })
  }, [loading, nodes.length, project?.viewport, fitView])

  const scheduleSync = useCallback(() => {
    if (!projectId) return
    if (syncTimerRef.current) window.clearTimeout(syncTimerRef.current)
    syncTimerRef.current = window.setTimeout(async () => {
      const viewport = getViewport()
      const nodeUpdates = nodes.map((n) => ({
        node_id: n.id,
        position: n.position,
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
    const pos = getSpawnPosition(flowPos ?? spawnFlowPos ?? undefined)
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
      setPanelVisible(true)
      setSpawnFlowPos(null)
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

  const isValidConnection = useCallback((connection: Connection) => {
    if (!connection.source || !connection.target) return false
    if (connection.source === connection.target) return false
    return true
  }, [])

  const onConnect = useCallback(
    async (connection: Connection) => {
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

  const onCanvasClick = useCallback((event: React.MouseEvent) => {
    const target = event.target as HTMLElement
    if (target.closest('.react-flow__node')) return
    if (target.closest('.canvas-node-floating-panel')) return
    if (target.closest('.canvas-toolbar')) return
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

  const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
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
      }
      onNodesChange(changes)
    },
    [onNodesChange],
  )

  const onMoveStart = useCallback(() => {
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
    setRunningNodeId(selectedNodeId)
    updateLocalNode(selectedNodeId, { status: 'running', config: { ...selectedCanvasNode?.config, ...config } })
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
      setRunningNodeId(null)
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
      const tag = (e.target as HTMLElement)?.tagName
      if (tag === 'INPUT' || tag === 'TEXTAREA') return
      const mod = e.ctrlKey || e.metaKey
      if (mod && e.key.toLowerCase() === 'c') {
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
        handleDeleteSelected()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [handleDeleteSelected, selectedNodeId])

  const handleViewportChange = useCallback((vp: { x: number; y: number; zoom: number }) => {
    setViewport(vp)
  }, [])

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
          onClick={onCanvasClick}
          onDoubleClick={onCanvasDoubleClick}
          zoomOnDoubleClick={false}
          onNodesChange={onNodesChangeWrapped}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
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
          nodesFocusable={false}
          elevateNodesOnSelect={false}
          selectNodesOnDrag={false}
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
      </div>

      <AddNodePickerModal
        open={addModalOpen}
        onClose={() => {
          setAddModalOpen(false)
          setSpawnFlowPos(null)
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
