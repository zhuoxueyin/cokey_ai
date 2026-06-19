import type { CanvasProject } from '@/types/canvas'
import { listCanvasProjects } from '@/api/canvas'

/** 画布项目详情页路径 */
export function canvasProjectPath(projectId: string) {
  return `/canvas/${projectId}`
}

/** 新标签页打开画布项目（保留当前主页/列表页） */
export function openCanvasProject(projectId: string) {
  window.open(canvasProjectPath(projectId), '_blank', 'noopener,noreferrer')
}

/** Link 组件用于新开标签页的属性 */
export const canvasProjectLinkProps = {
  target: '_blank' as const,
  rel: 'noopener noreferrer',
}

/** 拉取项目列表（含未绑定 user_id 的历史项目） */
export async function fetchCanvasProjects(userId?: string | null, pageSize = 50): Promise<CanvasProject[]> {
  const res = await listCanvasProjects({ user_id: userId || undefined, page_size: pageSize })
  if (res.code !== 'success') return []
  return Array.isArray(res.data) ? res.data : []
}
