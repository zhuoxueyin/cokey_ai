import type { Node } from '@xyflow/react'
import type { CanvasNode } from '@/types/canvas'

export const GROUP_PADDING = 28

export function sortCanvasNodesForFlow(nodes: CanvasNode[]): CanvasNode[] {
  const groups = nodes.filter((n) => n.node_type === 'group')
  const rest = nodes.filter((n) => n.node_type !== 'group')
  return [...groups, ...rest]
}

export function isGroupableFlowNode(node: Node): boolean {
  if (node.type === 'group') return false
  if (node.parentId) return false
  return true
}

export function computeGroupBounds(selected: Node[]): { x: number; y: number; width: number; height: number } {
  let minX = Infinity
  let minY = Infinity
  let maxX = -Infinity
  let maxY = -Infinity
  for (const n of selected) {
    const w = Number(n.width ?? n.measured?.width ?? 280)
    const h = Number(n.height ?? n.measured?.height ?? 200)
    minX = Math.min(minX, n.position.x)
    minY = Math.min(minY, n.position.y)
    maxX = Math.max(maxX, n.position.x + w)
    maxY = Math.max(maxY, n.position.y + h)
  }
  return {
    x: minX - GROUP_PADDING,
    y: minY - GROUP_PADDING,
    width: Math.max(160, maxX - minX + GROUP_PADDING * 2),
    height: Math.max(120, maxY - minY + GROUP_PADDING * 2),
  }
}

/** 选中项是否可解组（单选分组框，或多选同属一组的子节点） */
export function canUngroupSelection(selected: Node[]): boolean {
  if (selected.length === 0) return false
  if (selected.length === 1 && selected[0].type === 'group') return true
  const parentIds = new Set(selected.map((n) => n.parentId).filter(Boolean))
  return parentIds.size === 1 && selected.every((n) => n.parentId && n.type !== 'group')
}

export function nextGroupTitle(existing: CanvasNode[]): string {
  const used = existing.filter((n) => n.node_type === 'group').length
  return used === 0 ? '分组' : `分组 ${used + 1}`
}
