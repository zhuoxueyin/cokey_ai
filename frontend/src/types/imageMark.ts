export type ImageMarkTool = 'brush' | 'ellipse' | 'rect' | 'eraser' | 'text'

export type ImageMarkLayerType = 'path' | 'ellipse' | 'rect' | 'text' | 'eraser'

/** 标记图层，坐标均为相对原图宽高的 0~1 归一化值 */
export interface ImageMarkLayer {
  id: string
  type: ImageMarkLayerType
  color: string
  strokeWidth: number
  points?: { x: number; y: number }[]
  cx?: number
  cy?: number
  rx?: number
  ry?: number
  x?: number
  y?: number
  w?: number
  h?: number
  text?: string
  fontSize?: number
}

export const MARK_COLOR_PRESETS = ['#ff4d4f', '#fa8c16', '#fadb14', '#52c41a', '#1677ff', '#722ed1', '#ffffff']

export const DEFAULT_MARK_COLOR = '#ff4d4f'
export const DEFAULT_MARK_STROKE = 4
