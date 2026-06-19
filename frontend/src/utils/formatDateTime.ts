/**
 * 解析后端 UTC 时间（Mongo 存 UTC，API 带 Z 后缀）并格式化为本地时间。
 */
export function parseServerDateTime(value?: string | Date | null): Date | null {
  if (value == null || value === '') return null
  if (value instanceof Date) return Number.isNaN(value.getTime()) ? null : value
  const raw = String(value).trim()
  if (!raw) return null
  const hasTz = /[Zz]$/.test(raw) || /[+-]\d{2}:\d{2}$/.test(raw)
  const normalized = hasTz ? raw : `${raw.replace(/\.\d+$/, '')}Z`
  const date = new Date(normalized)
  return Number.isNaN(date.getTime()) ? null : date
}

export function formatServerDateTime(
  value?: string | Date | null,
  options?: Intl.DateTimeFormatOptions,
): string {
  const date = parseServerDateTime(value)
  if (!date) return '-'
  return date.toLocaleString(
    'zh-CN',
    options ?? {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    },
  )
}

/** 表格列用：省略秒，减少列宽撑破布局 */
export function formatServerDateTimeCompact(value?: string | Date | null): string {
  return formatServerDateTime(value, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
}
