import type { CanvasUpstreamRef } from '@/utils/canvasUpstream'
import { parseEditableSegments, storedToEditable } from '@/utils/canvasPromptMention'

const CHIP_CLASS = 'canvas-mention-chip'

export function createMentionChip(ref: CanvasUpstreamRef): HTMLSpanElement {
  const chip = document.createElement('span')
  chip.className = CHIP_CLASS
  chip.contentEditable = 'false'
  chip.dataset.nodeId = ref.nodeId
  chip.dataset.mentionLabel = ref.mentionLabel

  const thumb = document.createElement('span')
  thumb.className = `canvas-mention-chip__thumb${ref.kind === 'text' ? ' canvas-mention-chip__thumb--text' : ''}`
  if (ref.kind === 'image' && ref.previewUrl) {
    const img = document.createElement('img')
    img.src = ref.previewUrl
    img.alt = ''
    thumb.appendChild(img)
  }

  const label = document.createElement('span')
  label.className = 'canvas-mention-chip__label'
  label.textContent = ref.mentionLabel

  chip.append(thumb, label)
  return chip
}

export function serializeEditor(editor: HTMLElement): string {
  let out = ''
  editor.childNodes.forEach((node) => {
    if (node.nodeType === Node.TEXT_NODE) {
      out += node.textContent || ''
      return
    }
    if (node instanceof HTMLElement && node.classList.contains(CHIP_CLASS)) {
      out += `@${node.dataset.mentionLabel || ''}`
      return
    }
    if (node.nodeType === Node.ELEMENT_NODE) {
      out += serializeEditor(node as HTMLElement)
    }
  })
  return out
}

export function renderEditableToEditor(
  editor: HTMLElement,
  editable: string,
  refs: CanvasUpstreamRef[],
): void {
  editor.innerHTML = ''
  const segments = parseEditableSegments(editable, refs)
  if (segments.length === 0) {
    editor.dataset.empty = 'true'
    return
  }
  editor.dataset.empty = 'false'
  for (const seg of segments) {
    if (seg.type === 'text') {
      editor.appendChild(document.createTextNode(seg.value))
    } else {
      editor.appendChild(createMentionChip(seg.ref))
    }
  }
}

export function syncEditorEmptyState(editor: HTMLElement): void {
  const text = serializeEditor(editor).replace(/\u200b/g, '').trim()
  editor.dataset.empty = text.length === 0 ? 'true' : 'false'
}

export function rebuildEditorIfNeeded(
  editor: HTMLElement,
  editable: string,
  refs: CanvasUpstreamRef[],
): boolean {
  const current = serializeEditor(editor)
  if (current === editable) return false
  renderEditableToEditor(editor, editable, refs)
  syncEditorEmptyState(editor)
  return true
}

export function getSelectionEditableOffset(editor: HTMLElement): number {
  const sel = window.getSelection()
  if (!sel || sel.rangeCount === 0) return serializeEditor(editor).length
  const { focusNode, focusOffset } = sel
  if (!focusNode) return 0

  let offset = 0
  let found = false

  const walk = (node: Node): void => {
    if (found) return
    if (node === focusNode) {
      if (node.nodeType === Node.TEXT_NODE) {
        offset += focusOffset
      } else if (node instanceof HTMLElement && node.classList.contains(CHIP_CLASS)) {
        offset += `@${node.dataset.mentionLabel || ''}`.length
      } else {
        offset += focusOffset
      }
      found = true
      return
    }
    if (node.nodeType === Node.TEXT_NODE) {
      offset += node.textContent?.length || 0
      return
    }
    if (node instanceof HTMLElement && node.classList.contains(CHIP_CLASS)) {
      offset += `@${node.dataset.mentionLabel || ''}`.length
      return
    }
    node.childNodes.forEach(walk)
  }

  editor.childNodes.forEach(walk)
  return offset
}

export function setSelectionEditableOffset(editor: HTMLElement, target: number): void {
  const sel = window.getSelection()
  if (!sel) return

  let remaining = Math.max(0, target)
  let placed = false

  const placeAt = (node: Node, offset: number) => {
    const range = document.createRange()
    range.setStart(node, offset)
    range.collapse(true)
    sel.removeAllRanges()
    sel.addRange(range)
    placed = true
  }

  const walk = (node: Node): void => {
    if (placed) return
    if (node.nodeType === Node.TEXT_NODE) {
      const len = node.textContent?.length || 0
      if (remaining <= len) {
        placeAt(node, remaining)
        return
      }
      remaining -= len
      return
    }
    if (node instanceof HTMLElement && node.classList.contains(CHIP_CLASS)) {
      const len = `@${node.dataset.mentionLabel || ''}`.length
      if (remaining <= len) {
        if (remaining === 0) {
          placeAt(node.parentNode || editor, Array.from(node.parentNode?.childNodes || []).indexOf(node))
        } else {
          const next = node.nextSibling
          if (next) placeAt(next, 0)
          else placeAt(editor, editor.childNodes.length)
        }
        return
      }
      remaining -= len
      return
    }
    node.childNodes.forEach(walk)
  }

  editor.childNodes.forEach(walk)
  if (!placed) {
    placeAt(editor, editor.childNodes.length)
  }
}

export function getCaretClientRect(): DOMRect | null {
  const sel = window.getSelection()
  if (!sel || sel.rangeCount === 0) return null
  const range = sel.getRangeAt(0).cloneRange()
  range.collapse(true)
  const rects = range.getClientRects()
  if (rects.length > 0) return rects[0]

  const marker = document.createElement('span')
  marker.textContent = '\u200b'
  range.insertNode(marker)
  const rect = marker.getBoundingClientRect()
  marker.remove()
  return rect
}

export interface MentionTrigger {
  start: number
  end: number
  filter: string
}

export function findMentionTrigger(editor: HTMLElement): MentionTrigger | null {
  const offset = getSelectionEditableOffset(editor)
  const editable = serializeEditor(editor)
  const before = editable.slice(0, offset)
  const atIdx = before.lastIndexOf('@')
  if (atIdx === -1) return null
  const filter = before.slice(atIdx + 1)
  if (/[\s\n]/.test(filter)) return null
  return { start: atIdx, end: offset, filter }
}

export function removeMentionTrigger(editor: HTMLElement): boolean {
  const trigger = findMentionTrigger(editor)
  if (!trigger) return false
  setSelectionEditableOffset(editor, trigger.start)
  const sel = window.getSelection()
  if (!sel || sel.rangeCount === 0) return false
  const range = sel.getRangeAt(0)
  setSelectionEditableOffset(editor, trigger.end)
  const endRange = sel.getRangeAt(0)
  range.setEnd(endRange.endContainer, endRange.endOffset)
  range.deleteContents()
  sel.removeAllRanges()
  sel.addRange(range)
  return true
}

export function insertMentionAtCursor(editor: HTMLElement, ref: CanvasUpstreamRef): void {
  removeMentionTrigger(editor)
  const sel = window.getSelection()
  if (!sel || sel.rangeCount === 0) return
  const range = sel.getRangeAt(0)
  const chip = createMentionChip(ref)
  range.insertNode(chip)
  range.setStartAfter(chip)
  range.collapse(true)
  sel.removeAllRanges()
  sel.addRange(range)
  editor.dataset.empty = 'false'
}

export function insertPlainTextAtSelection(text: string): void {
  const sel = window.getSelection()
  if (!sel || sel.rangeCount === 0) return
  const range = sel.getRangeAt(0)
  range.deleteContents()
  const node = document.createTextNode(text)
  range.insertNode(node)
  range.setStartAfter(node)
  range.collapse(true)
  sel.removeAllRanges()
  sel.addRange(range)
}

export function editableFromStored(stored: string, refs: CanvasUpstreamRef[]): string {
  return storedToEditable(stored, refs)
}
