function triggerDownload(href: string, filename: string) {
  const link = document.createElement('a')
  link.href = href
  link.download = filename
  link.rel = 'noopener noreferrer'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

function guessFilename(url: string): string {
  try {
    const pathname = new URL(url).pathname
    const base = pathname.split('/').pop()
    if (base && base.includes('.')) return base
  } catch {
    /* ignore */
  }
  return `aigc_${Date.now()}.png`
}

function ensureExtension(filename: string, url: string): string {
  if (/\.[a-z0-9]+$/i.test(filename)) return filename
  try {
    const ext = new URL(url).pathname.split('.').pop()
    if (ext && ext.length <= 5) return `${filename}.${ext}`
  } catch {
    /* ignore */
  }
  if (url.includes('video') || filename.includes('视频')) return `${filename}.mp4`
  return `${filename}.png`
}

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function fetchDirect(url: string): Promise<Blob> {
  const response = await fetch(url, { mode: 'cors' })
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.blob()
}

/** 下载远程文件（跨域 CDN 须先 fetch 为 Blob；外部视频走后端代理） */
export async function downloadRemoteFile(url: string, filename?: string): Promise<void> {
  const name = ensureExtension(filename || guessFilename(url), url)

  if (url.startsWith('blob:') || url.startsWith('data:')) {
    triggerDownload(url, name)
    return
  }

  let blob: Blob
  try {
    blob = await fetchDirect(url)
  } catch {
    try {
      const params = new URLSearchParams({ url, filename: name })
      const response = await fetch(`/api/download/proxy?${params}`, { headers: authHeaders() })
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      blob = await response.blob()
    } catch {
      window.open(url, '_blank', 'noopener,noreferrer')
      throw new Error('无法直接保存，已在新标签页打开，请右键另存为')
    }
  }

  const blobUrl = URL.createObjectURL(blob)
  try {
    triggerDownload(blobUrl, name)
  } finally {
    URL.revokeObjectURL(blobUrl)
  }
}
