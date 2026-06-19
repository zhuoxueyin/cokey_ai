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

function listQueryUserId(userId?: string | null): string | undefined {
  if (!userId || userId === 'default_user') return undefined
  return userId
}

/** 拉取项目列表（含未绑定 user_id 与 default_user 历史项目；自动翻页） */
export async function fetchCanvasProjects(userId?: string | null, pageSize = 100): Promise<CanvasProject[]> {
  const queryUserId = listQueryUserId(userId)
  const all: CanvasProject[] = []
  let page = 1
  let totalPages = 1

  while (page <= totalPages) {
    const res = await listCanvasProjects({
      user_id: queryUserId,
      page,
      page_size: pageSize,
    })
    if (res.code !== 'success') break
    const batch = Array.isArray(res.data) ? res.data : []
    all.push(...batch)
    totalPages = Math.max(1, res.total_pages ?? 1)
    page += 1
  }

  return all
}
