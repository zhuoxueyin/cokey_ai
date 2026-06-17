/** 与 backend/app/core/cdn.py 保持一致的 CDN 域名白名单 */

export const KNOWN_CDN_PREFIXES = [
  'https://cdn.jsdmirror.com/',
  'https://cdn.jsdelivr.net/',
  'https://fastly.jsdelivr.net/',
  'https://ghproxy.net/',
  'https://raw.githubusercontent.com/',
]

const MAX_CDN_URL_LENGTH = 2048

export function isCdnUrl(url: string | null | undefined): boolean {
  if (!url || typeof url !== 'string') return false
  if (url.startsWith('data:') || url.startsWith('blob:')) return false
  return KNOWN_CDN_PREFIXES.some((prefix) => url.startsWith(prefix))
}

export function rejectNonCdnUrl(url: string | null | undefined, label = '图片'): string {
  if (!url || typeof url !== 'string') {
    throw new Error(`${label}地址无效，请先上传`)
  }
  if (url.startsWith('data:') || url.startsWith('blob:')) {
    throw new Error(`${label}须使用已上传的 CDN 地址，不支持本地或 Base64`)
  }
  if (!isCdnUrl(url)) {
    throw new Error(`${label}须使用已上传的 CDN 地址`)
  }
  if (url.length > MAX_CDN_URL_LENGTH) {
    throw new Error(`${label}地址异常，请重新上传`)
  }
  return url
}

/** 与 backend 默认配置一致，用于从 file_path 还原 CDN */
const DEFAULT_GH_REPO = 'zhuoxueyin/cokey_ai'
const DEFAULT_GH_BRANCH = 'main'

export function buildCdnUrlsFromFilePath(filePath: string, repo = DEFAULT_GH_REPO, branch = DEFAULT_GH_BRANCH): string[] {
  const path = `${repo}@${branch}/${filePath}`
  return [
    `https://cdn.jsdmirror.com/gh/${path}`,
    `https://fastly.jsdelivr.net/gh/${path}`,
    `https://cdn.jsdelivr.net/gh/${path}`,
    `https://ghproxy.net/https://raw.githubusercontent.com/${repo}/${branch}/${filePath}`,
    `https://raw.githubusercontent.com/${repo}/${branch}/${filePath}`,
  ]
}

/** 从上传/资源响应中选取主 CDN URL */
export function pickCdnUrl(
  data: { url?: string; cdn_urls?: string[]; file_path?: string; resolved_cdn_url?: string },
  label = '图片',
): string {
  if (data.resolved_cdn_url && isCdnUrl(data.resolved_cdn_url)) {
    return data.resolved_cdn_url
  }
  const fromList = data.cdn_urls?.find(isCdnUrl)
  if (fromList) return fromList
  if (data.url && isCdnUrl(data.url)) return data.url
  if (data.file_path) {
    const built = buildCdnUrlsFromFilePath(data.file_path).find(isCdnUrl)
    if (built) return built
  }
  const candidate = fromList ?? data.url
  return rejectNonCdnUrl(candidate, label)
}

export type ImageRef = {
  cdn_url: string
  file_name?: string
}

/** 兼容旧字段 url，统一转为 cdn_url */
export function normalizeImageRef(img: string | { url?: string; cdn_url?: string; file_name?: string }): ImageRef | null {
  const raw = typeof img === 'string' ? img : (img.cdn_url ?? img.url)
  if (!raw) return null
  try {
    return { cdn_url: rejectNonCdnUrl(raw), file_name: typeof img === 'object' ? img.file_name : undefined }
  } catch {
    return null
  }
}

/** 提交生图/视频时：提取并校验 CDN URL 字符串数组 */
export function extractCdnUrls(
  images: Array<string | { url?: string; cdn_url?: string; file_name?: string }>,
  label = '参考图',
): string[] {
  const urls: string[] = []
  for (const img of images) {
    const ref = normalizeImageRef(img)
    if (!ref) {
      throw new Error(`${label}须为已上传的 CDN 地址，请移除无效项后重新上传`)
    }
    urls.push(ref.cdn_url)
  }
  return urls
}

/** 资源库条目是否可用于生图 */
export function isAssetCdnReady(asset: {
  url?: string
  cdn_urls?: string[]
  file_path?: string
  resolved_cdn_url?: string
  cdn_ready?: boolean
}): boolean {
  if (asset.cdn_ready === true && asset.resolved_cdn_url) return true
  if (asset.cdn_ready === false) return false
  try {
    pickCdnUrl(asset)
    return true
  } catch {
    return false
  }
}
