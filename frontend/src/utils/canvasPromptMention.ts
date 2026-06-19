import type { CanvasUpstreamRef } from '@/utils/canvasUpstream'

/** 与后端 app/core/canvas_prompt.py 保持一致 */
export const CANVAS_REF_TOKEN_RE = /\{\{@node:([a-zA-Z0-9_]+)\}\}/g

export function buildRefToken(nodeId: string): string {
  return `{{@node:${nodeId}}}`
}

export function storedToEditable(stored: string, refs: CanvasUpstreamRef[]): string {
  if (!stored) return ''
  const byId = new Map(refs.map((r) => [r.nodeId, r]))
  return stored.replace(CANVAS_REF_TOKEN_RE, (_m, nodeId: string) => {
    const ref = byId.get(nodeId)
    return ref ? `@${ref.mentionLabel}` : _m
  })
}

export function editableToStored(editable: string, refs: CanvasUpstreamRef[]): string {
  if (!editable) return ''
  let stored = editable
  const sorted = [...refs].sort((a, b) => b.mentionLabel.length - a.mentionLabel.length)
  for (const ref of sorted) {
    const needle = `@${ref.mentionLabel}`
    stored = stored.split(needle).join(buildRefToken(ref.nodeId))
  }
  return stored
}

export type EditableSegment =
  | { type: 'text'; value: string }
  | { type: 'mention'; ref: CanvasUpstreamRef }

/** 将可编辑字符串拆成文本段与 @ 引用段 */
export function parseEditableSegments(editable: string, refs: CanvasUpstreamRef[]): EditableSegment[] {
  if (!editable) return []
  const sorted = [...refs].sort((a, b) => b.mentionLabel.length - a.mentionLabel.length)
  const segments: EditableSegment[] = []
  let rest = editable
  while (rest.length > 0) {
    let found: { ref: CanvasUpstreamRef; index: number } | null = null
    for (const ref of sorted) {
      const needle = `@${ref.mentionLabel}`
      const idx = rest.indexOf(needle)
      if (idx !== -1 && (found === null || idx < found.index)) {
        found = { ref, index: idx }
      }
    }
    if (!found) {
      segments.push({ type: 'text', value: rest })
      break
    }
    if (found.index > 0) {
      segments.push({ type: 'text', value: rest.slice(0, found.index) })
    }
    segments.push({ type: 'mention', ref: found.ref })
    rest = rest.slice(found.index + `@${found.ref.mentionLabel}`.length)
  }
  return segments
}

export function segmentsToEditable(segments: EditableSegment[]): string {
  return segments
    .map((seg) => (seg.type === 'text' ? seg.value : `@${seg.ref.mentionLabel}`))
    .join('')
}

/** 渲染预览：将占位符替换为 @标签（只读展示） */
export function storedToPreviewParts(
  stored: string,
  refs: CanvasUpstreamRef[],
): Array<{ type: 'text' | 'mention'; value: string }> {
  if (!stored) return []
  const byId = new Map(refs.map((r) => [r.nodeId, r]))
  const parts: Array<{ type: 'text' | 'mention'; value: string }> = []
  let last = 0
  const re = new RegExp(CANVAS_REF_TOKEN_RE.source, 'g')
  let match: RegExpExecArray | null
  while ((match = re.exec(stored)) !== null) {
    if (match.index > last) {
      parts.push({ type: 'text', value: stored.slice(last, match.index) })
    }
    const ref = byId.get(match[1])
    parts.push({ type: 'mention', value: ref ? ref.mentionLabel : match[0] })
    last = match.index + match[0].length
  }
  if (last < stored.length) {
    parts.push({ type: 'text', value: stored.slice(last) })
  }
  return parts
}

export function hasPromptContent(stored: string, hasUpstreamMedia: boolean): boolean {
  if (stored.trim()) return true
  return hasUpstreamMedia
}

/** 视频节点：允许空提示词（图生视频/首帧参考），有上游媒体或空提示均可提交 */
export function hasVideoRunInput(
  prompt: string,
  upstream: Pick<CanvasUpstreamPreview, 'images' | 'videos'>,
): boolean {
  if (prompt.trim()) return true
  if (upstream.images.length > 0) return true
  if (upstream.videos.length > 0) return true
  return true
}
