import type { ModelItem } from '@/types'

/** 与模型管理一致：默认模型优先，再按 sort_order 降序 */
export function sortModelsByAdminOrder(models: ModelItem[]): ModelItem[] {
  return [...models].sort((a, b) => {
    const defaultDelta = Number(b.is_default) - Number(a.is_default)
    if (defaultDelta !== 0) return defaultDelta
    const sortDelta = (b.sort_order ?? 0) - (a.sort_order ?? 0)
    if (sortDelta !== 0) return sortDelta
    return (a.model_name || a.model_code).localeCompare(b.model_name || b.model_code, 'zh-CN')
  })
}

export function pickDefaultModel(models: ModelItem[]): ModelItem | undefined {
  const sorted = sortModelsByAdminOrder(models)
  return sorted.find((m) => m.is_default) || sorted[0]
}

export function pickDefaultModelCode(models: ModelItem[]): string | undefined {
  return pickDefaultModel(models)?.model_code
}
