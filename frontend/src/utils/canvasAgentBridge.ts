import type { MutableRefObject } from 'react'
import type { CharacterImageTask } from '@/utils/characterImageTasks'

export type SpawnAgentTextNodeFn = (
  content: string,
  meta: { role: 'user' | 'assistant' },
) => void | Promise<void>

export type SpawnAgentImageTaskFn = (
  task: CharacterImageTask,
  opts: { modelCode?: string; stylePresetId?: string; stylePresetName?: string },
) => void | Promise<void>

export type EnsureCanvasPersistedFn = () => Promise<string>

type WorkspaceListener = () => void

type ScrollGuard = {
  pin: () => void
  restore: () => void
}

/** 画布 ↔ 创作助手桥接：避免 CanvasEditorInner 重渲染时连带刷新侧栏 */
export const canvasAgentBridge = {
  spawnTextNodeRef: { current: undefined } as MutableRefObject<SpawnAgentTextNodeFn | undefined>,
  spawnImageTaskRef: { current: undefined } as MutableRefObject<SpawnAgentImageTaskFn | undefined>,
  ensureCanvasPersistedRef: { current: undefined } as MutableRefObject<
    EnsureCanvasPersistedFn | undefined
  >,
  workspaceEl: null as HTMLDivElement | null,
  _workspaceListeners: new Set<WorkspaceListener>(),
  _scrollGuard: null as ScrollGuard | null,

  setWorkspaceEl(el: HTMLDivElement | null) {
    if (this.workspaceEl === el) return
    this.workspaceEl = el
    this._workspaceListeners.forEach((fn) => fn())
  },

  subscribeWorkspace(listener: WorkspaceListener) {
    this._workspaceListeners.add(listener)
    return () => {
      this._workspaceListeners.delete(listener)
    }
  },

  setScrollGuard(guard: ScrollGuard | null) {
    this._scrollGuard = guard
  },

  /** 画布增删节点后恢复创作助手滚动位置 */
  notifyCanvasMutation() {
    const guard = this._scrollGuard
    if (!guard) return
    guard.pin()
    requestAnimationFrame(() => {
      guard.restore()
      requestAnimationFrame(() => guard.restore())
    })
  },
}
