import { create } from 'zustand'
import type { ModelItem, TaskItem, TaskResult } from '@/types'

interface GenerationState {
  activeCategory: 'text' | 'image' | 'video'
  currentModel: ModelItem | null
  params: Record<string, any>
  sessionId: string | null
  tasks: TaskItem[]
  isGenerating: boolean
  currentTask: Partial<TaskItem> | null
}

interface GenerationActions {
  setCategory: (category: 'text' | 'image' | 'video') => void
  setModel: (model: ModelItem) => void
  setParams: (params: Record<string, any>) => void
  updateParam: (key: string, value: any) => void
  setSessionId: (id: string) => void
  setTasks: (tasks: TaskItem[]) => void
  addTask: (task: TaskItem) => void
  updateTask: (taskId: string, updates: Partial<TaskItem>) => void
  setIsGenerating: (val: boolean) => void
  setCurrentTask: (task: Partial<TaskItem> | null) => void
  resetParams: () => void
}

export const useGenerationStore = create<GenerationState & GenerationActions>((set, get) => ({
  activeCategory: 'text',
  currentModel: null,
  params: {},
  sessionId: null,
  tasks: [],
  isGenerating: false,
  currentTask: null,

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
  setTasks: (tasks) => set({ tasks }),
  addTask: (task) => set((state) => ({ tasks: [...state.tasks, task] })),
  updateTask: (taskId, updates) =>
    set((state) => ({
      tasks: state.tasks.map((t) => (t.task_id === taskId ? { ...t, ...updates } : t)),
    })),
  setIsGenerating: (val) => set({ isGenerating: val }),
  setCurrentTask: (task) => set({ currentTask: task }),
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
}))
