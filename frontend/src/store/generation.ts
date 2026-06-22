import { create } from 'zustand'
import type { ModelItem, TaskItem, TaskResult } from '@/types'
import { filterWorkspaceTasks, isCanvasTask } from '@/utils/taskSource'

// 服务端任务管理 - 不再使用localStorage

interface GenerationState {
  activeCategory: 'text' | 'image' | 'video'
  currentModel: ModelItem | null
  params: Record<string, any>
  sessionId: string | null
  userId: string | null  // 当前用户ID
  defaultCanvasProjectId: string | null  // 创作工作台固定画布
  tasks: TaskItem[]
  isGenerating: boolean
  currentTask: Partial<TaskItem> | null
  availableModels: ModelItem[]
}

interface GenerationActions {
  setCategory: (category: 'text' | 'image' | 'video') => void
  setModel: (model: ModelItem) => void
  setParams: (params: Record<string, any>) => void
  updateParam: (key: string, value: any) => void
  setSessionId: (id: string) => void
  setUserId: (id: string | null) => void
  setDefaultCanvasProjectId: (id: string | null) => void
  setTasks: (tasks: TaskItem[]) => void
  addTask: (task: TaskItem) => void
  updateTask: (taskId: string, updates: Partial<TaskItem>) => void
  setIsGenerating: (val: boolean) => void
  setCurrentTask: (task: Partial<TaskItem> | null) => void
  setAvailableModels: (models: ModelItem[]) => void
  resetParams: () => void
  clearTasks: () => void
  setParamsWithCategory: (category: 'text' | 'image' | 'video', params: Record<string, any>, modelCode?: string) => void
}

export const useGenerationStore = create<GenerationState & GenerationActions>((set, get) => ({
  activeCategory: 'text',
  currentModel: null,
  params: {},
  sessionId: null,
  userId: 'default_user',  // 默认用户ID，后续可从登录状态获取
  defaultCanvasProjectId: null,
  tasks: [],  // 任务从服务端获取
  isGenerating: false,
  currentTask: null,
  availableModels: [],

  setCategory: (category) => {
    set({ activeCategory: category, params: {}, currentModel: null })
  },
  setModel: (model) => {
    const defaults: Record<string, any> = {}
    if (model.param_schema?.fields) {
      model.param_schema.fields.forEach((f) => {
        if (f.default !== undefined) {
          defaults[f.name] = f.default
        }
      })
    }
    set({ currentModel: model, params: defaults })
  },
  setParams: (params) => set({ params }),
  updateParam: (key, value) => set((state) => ({ params: { ...state.params, [key]: value } })),
  setSessionId: (id) => set({ sessionId: id }),
  setUserId: (id) => set({ userId: id }),
  setDefaultCanvasProjectId: (id) => set({ defaultCanvasProjectId: id }),
  setTasks: (tasks) => set({ tasks: filterWorkspaceTasks(tasks) }),
  addTask: (task) => {
    if (isCanvasTask(task)) return
    // 新任务添加到数组末尾，符合聊天对话习惯（最新的在底部）
    set((state) => ({ tasks: [...state.tasks, task] }))
  },
  updateTask: (taskId, updates) => {
    set((state) => ({
      tasks: state.tasks.map((t) => (t.task_id === taskId ? { ...t, ...updates } : t))
    }))
  },
  setIsGenerating: (val) => set({ isGenerating: val }),
  setCurrentTask: (task) => set({ currentTask: task }),
  setAvailableModels: (models) => set({ availableModels: models }),
  resetParams: () => {
    const model = get().currentModel
    const defaults: Record<string, any> = {}
    if (model?.param_schema?.fields) {
      model.param_schema.fields.forEach((f) => {
        if (f.default !== undefined) {
          defaults[f.name] = f.default
        }
      })
    }
    set({ params: defaults })
  },
  clearTasks: () => set({ tasks: [] }),
  setParamsWithCategory: (category, params, modelCode) => {
    const state = get()
    let model: ModelItem | null = null
    if (modelCode) {
      model = state.availableModels.find(m => m.model_code === modelCode) || null
    }
    if (!model) {
      model = state.availableModels.find(m => m.category === category && m.is_default) || null
    }
    set({ activeCategory: category, params, currentModel: model })
  },
}))

// 验证 processing 状态的任务实际状态
export const validateProcessingTasks = async (tasks: TaskItem[]): Promise<TaskItem[]> => {
  const workspaceTasks = filterWorkspaceTasks(tasks)
  const processingTasks = workspaceTasks.filter(t => t.status === 'processing' || t.status === 'pending')
  if (processingTasks.length === 0) {
    return workspaceTasks
  }

  try {
    const { getTaskStatus } = await import('@/api')
    const updatedTasks = [...workspaceTasks]

    for (const task of processingTasks) {
      if (task.task_id && !task.task_id.startsWith('task_local_')) {
        try {
          const res = await getTaskStatus(task.task_id)
          if (res.code === 'success' && res.data) {
            const index = updatedTasks.findIndex(t => t.task_id === task.task_id)
            if (index !== -1) {
              updatedTasks[index] = {
                ...updatedTasks[index],
                status: res.data.status,
                result: res.data.result,
                error_message: res.data.error_message,
                duration_ms: res.data.duration_ms,
              }
            }
          }
        } catch (e) {
          console.error(`验证任务状态失败 ${task.task_id}:`, e)
        }
      }
    }
    return updatedTasks
  } catch (e) {
    console.error('验证处理中任务状态失败:', e)
    return workspaceTasks
  }
}

// 从后端同步任务（确保与任务管理页面一致）
export const syncTasksFromBackend = async (userId?: string, sessionId?: string): Promise<TaskItem[]> => {
  try {
    const { listTasks } = await import('@/api')
    const res = await listTasks({
      page: 1,
      page_size: 100,
      session_id: sessionId,
      user_id: userId,
      source: 'workspace',
    })
    if (res.code === 'success' && res.data && res.data.data) {
      return filterWorkspaceTasks(res.data.data as TaskItem[])
    }
    return []
  } catch (e) {
    console.error('从后端同步任务失败:', e)
    return []
  }
}

// 创建会话
export const createSession = async (category: string, userId?: string): Promise<string | null> => {
  try {
    const { createSession } = await import('@/api')
    const res = await createSession({ category, user_id: userId })
    if (res.code === 'success' && res.data) {
      return res.data.session_id
    }
    return null
  } catch (e) {
    console.error('创建会话失败:', e)
    return null
  }
}

// 更新会话上下文
export const updateSessionContext = async (sessionId: string, context: Record<string, any>): Promise<boolean> => {
  try {
    const { updateSessionContext } = await import('@/api')
    const res = await updateSessionContext(sessionId, context)
    return res.code === 'success'
  } catch (e) {
    console.error('更新会话上下文失败:', e)
    return false
  }
}
