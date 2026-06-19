/**
 * curl 命令解析工具
 * 支持：-X/--request, -H/--header, -d/--data/--data-raw, -F/--form, URL 自动识别
 * 不识别：API KEY（用户手动填写）
 */

export interface ParsedCurl {
  method: string
  url: string
  base_url: string
  endpoint: string
  headers: Record<string, string>
  body_type: 'json' | 'form' | 'multipart' | 'raw'
  body_fields: BodyField[]
}

export interface BodyField {
  name: string
  value: string
  /** default: 固定值 | dynamic: 由前端传入 | image: 图片文件/URL */
  type: 'default' | 'dynamic' | 'image'
}

/**
 * 将 curl body_fields 转换为 body_params（新格式：source 与配置分离）
 */
export function bodyFieldsToBodyParams(fields: BodyField[]): {
  key: string
  source: string
  literal?: string
  param?: string
  description?: string
}[] {
  return fields.map((f) => {
    if (f.type === 'default') {
      return {
        key: f.name,
        source: 'literal',
        literal: f.value,
        description: 'curl 示例固定值',
      }
    }
    if (f.type === 'image') {
      return {
        key: f.name,
        source: 'image_urls',
        param: f.name || 'images',
        description: '图片 URL 列表',
      }
    }
    if (f.name === 'messages') {
      return { key: f.name, source: 'chat_messages', description: '自动组装 prompt+images' }
    }
    return {
      key: f.name,
      source: 'task_param',
      param: f.name,
      description: '任务参数字段',
    }
  })
}

/**
 * 从 curl headers 中提取 content_type 和自定义 headers
 *
 * 规则:
 *   - Content-Type / content-type -> 返回作为 content_type
 *   - Authorization: Bearer xxx -> 跳过（API KEY 由用户手动填写，不自动识别）
 *   - 其他 header -> 返回为自定义 headers
 */
export function extractContentTypeAndHeaders(headers: Record<string, string>): { content_type: string; custom_headers: Record<string, string> } {
  let content_type = 'application/json'
  const custom_headers: Record<string, string> = {}

  for (const [k, v] of Object.entries(headers)) {
    const keyLower = k.toLowerCase()
    if (keyLower === 'content-type') {
      content_type = v.split(';')[0].trim() || 'application/json'
    } else if (keyLower === 'authorization') {
      // 跳过：API KEY 不自动识别，由用户手动填写
      continue
    } else {
      custom_headers[k] = v
    }
  }

  return { content_type, custom_headers }
}

/**
 * 解析 curl 命令
 */
export function parseCurl(curlText: string): ParsedCurl {
  const tokens = tokenize(curlText)
  let method = 'POST'
  let url = ''
  const headers: Record<string, string> = {}
  const formFields: BodyField[] = []
  let bodyText = ''

  let i = 0
  while (i < tokens.length) {
    const tok = tokens[i]
    if (tok === 'curl') { i++ ; continue }

    if (tok === '-X' || tok === '--request') {
      method = (tokens[i + 1] || 'GET').toUpperCase()
      i += 2
    } else if (tok === '-H' || tok === '--header') {
      const headerStr = tokens[i + 1] || ''
      const idx = headerStr.indexOf(':')
      if (idx > 0) {
        headers[headerStr.substring(0, idx).trim()] = headerStr.substring(idx + 1).trim()
      }
      i += 2
    } else if (tok === '-d' || tok === '--data' || tok === '--data-raw' || tok === '--data-binary' || tok === '--data-ascii') {
      bodyText += tokens[i + 1] || ''
      i += 2
    } else if (tok === '--data-urlencode') {
      bodyText += tokens[i + 1] || ''
      i += 2
    } else if (tok === '-F' || tok === '--form') {
      const formVal = tokens[i + 1] || ''
      const eqIdx = formVal.indexOf('=')
      if (eqIdx > 0) {
        const name = formVal.substring(0, eqIdx).trim()
        const val = formVal.substring(eqIdx + 1).trim()
        if (val.startsWith('@')) {
          formFields.push({ name, value: val.substring(1), type: 'image' })
        } else {
          formFields.push({ name, value: val, type: 'default' })
        }
      }
      i += 2
    } else if (tok && (tok.startsWith('http') || tok.startsWith('"http') || tok.startsWith("'http"))) {
      let u = tok
      if ((u.startsWith('"') && u.endsWith('"')) || (u.startsWith("'") && u.endsWith("'"))) {
        u = u.slice(1, -1)
      }
      url = u
      i++
    } else {
      i++
    }
  }

  const { base_url, endpoint } = splitBaseUrlAndPath(url)

  // 推断 body 类型
  let body_type: ParsedCurl['body_type'] = 'json'
  const ctHeader = Object.keys(headers).find(k => k.toLowerCase() === 'content-type')
  const contentType = ctHeader ? headers[ctHeader].toLowerCase() : ''

  if (formFields.length > 0) {
    body_type = contentType.includes('multipart') ? 'multipart' : 'form'
  } else if (bodyText) {
    if (contentType.includes('json') || bodyText.trim().startsWith('{')) body_type = 'json'
    else body_type = 'raw'
  }

  // 解析 JSON body 为字段
  if (body_type === 'json' && bodyText && formFields.length === 0) {
    try {
      const json = JSON.parse(bodyText)
      if (json && typeof json === 'object') {
        for (const [k, v] of Object.entries(json)) {
          formFields.push({
            name: k, value: typeof v === 'string' ? v : JSON.stringify(v), type: 'default' })
        }
      }
    } catch {}
  }

  return { method, url, base_url, endpoint, headers, body_type, body_fields: formFields }
}

/**
 * 把 URL 拆分成 base_url + endpoint
 *
 * 核心规则：按 API 版本号（v1, v2, v1beta 等）切分
 *   - base_url = protocol + host + 路径中到版本号段（包含版本号），结尾无斜杠
 *   - endpoint = 版本号之后的路径，开头无斜杠（后端 join_url 会自动拼接）
 *
 * 示例（主流 OpenAI 兼容格式）：
 *   https://api.openai.com/v1/chat/completions
 *   -> base_url: https://api.openai.com/v1,  endpoint: chat/completions
 *
 *   https://api.weelink.ai/v1/images/edits
 *   -> base_url: https://api.weelink.ai/v1,   endpoint: images/edits
 *
 *   https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks
 *   -> base_url: https://ark.cn-beijing.volces.com/api/v3,  endpoint: contents/generations/tasks
 *
 * 回退规则（无版本号时）：
 *   - base_url = protocol + host（不包含任何路径）
 *   - endpoint = 完整 pathname，开头无斜杠
 */
function splitBaseUrlAndPath(fullUrl: string): { base_url: string; endpoint: string } {
  if (!fullUrl) return { base_url: '', endpoint: '' }
  try {
    const u = new URL(fullUrl)
    const base = `${u.protocol}//${u.host}`
    const parts = u.pathname.split('/').filter(Boolean)

    if (parts.length === 0) {
      return { base_url: base, endpoint: '' }
    }

    // 在路径段中寻找版本号（v1, v2, v1beta, v3alpha, v3.1 等）
    // 取最后一个匹配的版本号段作为切分点（支持 /api/v1/chat 这种嵌套）
    const versionRegex = /^v\d+(\.[\da-z]+)*([a-z]*\d*)*$/i
    let versionIdx = -1
    for (let i = parts.length - 1; i >= 0; i--) {
      if (versionRegex.test(parts[i])) {
        versionIdx = i
        break
      }
    }

    if (versionIdx >= 0) {
      // 找到版本号：base_url = 协议+主机+路径到版本号（含）；endpoint = 版本号之后，无斜杠
      const basePath = parts.slice(0, versionIdx + 1).join('/')
      const endpointParts = parts.slice(versionIdx + 1)
      return {
        base_url: `${base}/${basePath}`,
        endpoint: endpointParts.length > 0 ? endpointParts.join('/') : '',
      }
    }

    // 无版本号：base_url = 协议+主机（纯域名），endpoint = 完整路径，无斜杠
    return {
      base_url: base,
      endpoint: parts.join('/'),
    }
  } catch {
    return { base_url: fullUrl, endpoint: '' }
  }
}

/**
 * 将 curl 文本按空格分词，支持单/双引号和反斜杠转义
 */
function tokenize(text: string): string[] {
  if (!text) return []
  // 先把 \ 换行（多行 curl）替换为空格，再处理
  const normalized = text.replace(/\\\n/g, ' ').replace(/\\\r\n/g, ' ')
  const tokens: string[] = []
  let i = 0
  while (i < normalized.length) {
    while (i < normalized.length && /\s/.test(normalized[i])) i++
    if (i >= normalized.length) break
    const ch = normalized[i]

    if (ch === '"') {
      let j = i + 1, buf = ''
      while (j < normalized.length && normalized[j] !== '"') {
        if (normalized[j] === '\\' && j + 1 < normalized.length) {
          buf += normalized[j + 1]
          j += 2
        } else {
          buf += normalized[j]
          j++
        }
      }
      tokens.push(buf)
      i = j + 1
    } else if (ch === "'") {
      let j = i + 1, buf = ''
      while (j < normalized.length && normalized[j] !== "'") {
        buf += normalized[j]
        j++
      }
      tokens.push(buf)
      i = j + 1
    } else {
      let j = i
      while (j < normalized.length && !/\s/.test(normalized[j])) j++
      tokens.push(normalized.substring(i, j))
      i = j
    }
  }
  return tokens.filter(t => t.length > 0)
}
