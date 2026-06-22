/** 从 axios / 业务 reject 对象中提取可读错误文案 */
export function extractApiErrorMessage(error: unknown, fallback = '请求失败'): string {
  if (!error || typeof error !== 'object') return fallback
  const o = error as Record<string, unknown>
  if (typeof o.message === 'string' && o.message.trim()) return o.message
  const resp = o.response as Record<string, unknown> | undefined
  const data = resp?.data as Record<string, unknown> | undefined
  if (data && typeof data.message === 'string' && data.message.trim()) return data.message
  if (typeof o.detail === 'string' && o.detail.trim()) return o.detail
  return fallback
}
