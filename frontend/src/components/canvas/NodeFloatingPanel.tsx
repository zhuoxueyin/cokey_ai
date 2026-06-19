import { useEffect, useState, type ReactNode } from 'react'
import { useReactFlow, useStore, type Node } from '@xyflow/react'

interface NodeFloatingPanelProps {
  nodeId: string | null
  visible: boolean
  /** 节点当前宽度，用于面板宽度与居中对齐 */
  anchorWidth?: number
  /** 节点当前高度 */
  anchorHeight?: number
  children: ReactNode
}

const PANEL_MIN = 420
const PANEL_MAX = 720
const PANEL_PREFERRED = 640
/** 面板与节点底边的屏幕像素间距 */
const PANEL_SCREEN_GAP = 4

type PanelLayout = { x: number; y: number; w: number }

function measurePanelLayout(
  nodeId: string,
  anchorWidth?: number,
  anchorHeight?: number,
  getNode?: (id: string) => Node | undefined,
  flowToScreenPosition?: (pos: { x: number; y: number }) => { x: number; y: number },
): PanelLayout | null {
  const nodeEl = document.querySelector(`.react-flow__node[data-id="${nodeId}"]`) as HTMLElement | null
  const workspace = nodeEl?.closest('.canvas-workspace') as HTMLElement | null

  if (nodeEl && workspace) {
    const nodeRect = nodeEl.getBoundingClientRect()
    const wsRect = workspace.getBoundingClientRect()
    const nodeWidth = nodeRect.width
    const panelW = Math.min(PANEL_MAX, Math.max(PANEL_MIN, Math.max(nodeWidth, PANEL_PREFERRED)))
    return {
      x: nodeRect.left + nodeRect.width / 2 - wsRect.left,
      y: nodeRect.bottom - wsRect.top + PANEL_SCREEN_GAP,
      w: panelW,
    }
  }

  if (!getNode || !flowToScreenPosition) return null
  const node = getNode(nodeId)
  if (!node) return null
  const nodeWidth = Number(node.width ?? node.measured?.width ?? anchorWidth ?? 280)
  const nodeHeight = Number(node.height ?? node.measured?.height ?? anchorHeight ?? 200)
  const panelW = Math.min(PANEL_MAX, Math.max(PANEL_MIN, Math.max(nodeWidth, PANEL_PREFERRED)))
  const p = flowToScreenPosition({
    x: node.position.x + nodeWidth / 2,
    y: node.position.y + nodeHeight,
  })
  return { x: p.x, y: p.y + PANEL_SCREEN_GAP, w: panelW }
}

export default function NodeFloatingPanel({
  nodeId,
  visible,
  anchorWidth,
  anchorHeight,
  children,
}: NodeFloatingPanelProps) {
  const { flowToScreenPosition, getNode } = useReactFlow()
  const transform = useStore((s) => s.transform)
  const [layout, setLayout] = useState<PanelLayout | null>(null)

  useEffect(() => {
    if (!visible || !nodeId) {
      setLayout(null)
      return
    }

    const update = () => {
      const next = measurePanelLayout(
        nodeId,
        anchorWidth,
        anchorHeight,
        getNode,
        flowToScreenPosition,
      )
      if (next) setLayout(next)
    }

    update()
    const raf = requestAnimationFrame(update)
    window.addEventListener('resize', update)
    return () => {
      cancelAnimationFrame(raf)
      window.removeEventListener('resize', update)
    }
  }, [visible, nodeId, anchorWidth, anchorHeight, getNode, flowToScreenPosition, transform])

  if (!visible || !nodeId || !layout) return null

  return (
    <div
      className="canvas-node-floating-panel"
      style={{ left: layout.x, top: layout.y, width: layout.w }}
      onClick={(e) => e.stopPropagation()}
      onDoubleClick={(e) => e.stopPropagation()}
    >
      {children}
    </div>
  )
}
