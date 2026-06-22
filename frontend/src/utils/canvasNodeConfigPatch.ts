import type { CanvasNodeConfig } from '@/types/canvas'

/** 节点 config 局部更新；null 表示显式清除可选字段（如风格） */
export type CanvasNodeConfigPatch = {
  [K in keyof CanvasNodeConfig]?: CanvasNodeConfig[K] | null
}

/** 合并节点 config patch；仅 style_preset_id 为 null/'' 时视为显式清除（undefined 不覆盖已有风格） */
export function mergeCanvasNodeConfig(
  base: CanvasNodeConfig | undefined,
  patch: CanvasNodeConfigPatch,
): CanvasNodeConfig {
  const merged: CanvasNodeConfig = { ...(base || {}), ...patch }
  if (
    Object.prototype.hasOwnProperty.call(patch, 'style_preset_id') &&
    (patch.style_preset_id === null || patch.style_preset_id === '')
  ) {
    delete merged.style_preset_id
    delete merged.style_preset_name
  }
  if (patch.style_preset_name === null) {
    delete merged.style_preset_name
  }
  return merged
}
