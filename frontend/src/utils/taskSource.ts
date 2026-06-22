/** 任务来源：底层共用 tasks 集合，展示层按来源隔离 */

export type TaskSource = 'workspace' | 'canvas'

export interface TaskCanvasMeta {
  canvas_project_id?: string | null
  canvas_node_id?: string | null
  canvas_node_title?: string | null
  canvas_node_type?: string | null
}

/** 是否为无限画布节点 run 产生的任务 */
export function isCanvasTask(task: TaskCanvasMeta | null | undefined): boolean {
  const pid = task?.canvas_project_id
  return typeof pid === 'string' && pid.length > 0
}

/** 创作工作台信息流：仅保留非画布任务 */
export function filterWorkspaceTasks<T extends TaskCanvasMeta>(tasks: T[]): T[] {
  return tasks.filter((t) => !isCanvasTask(t))
}
