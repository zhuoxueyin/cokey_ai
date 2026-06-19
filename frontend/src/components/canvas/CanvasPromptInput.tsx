import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { FileTextOutlined } from '@ant-design/icons'
import type { CanvasUpstreamRef } from '@/utils/canvasUpstream'
import { editableToStored, storedToEditable } from '@/utils/canvasPromptMention'
import {
  findMentionTrigger,
  getCaretClientRect,
  insertMentionAtCursor,
  insertPlainTextAtSelection,
  rebuildEditorIfNeeded,
  serializeEditor,
  syncEditorEmptyState,
} from '@/utils/canvasPromptEditor'

interface CanvasPromptInputProps {
  /** 存储格式：含 {{@node:id}} 占位符 */
  value: string
  onChange: (stored: string) => void
  refs: CanvasUpstreamRef[]
  placeholder?: string
  className?: string
  minRows?: number
  maxRows?: number
}

function MentionThumb({ refItem }: { refItem: CanvasUpstreamRef }) {
  if (refItem.kind === 'image' && refItem.previewUrl) {
    return (
      <span className="canvas-mention-panel__thumb">
        <img src={refItem.previewUrl} alt="" />
      </span>
    )
  }
  return (
    <span className="canvas-mention-panel__thumb canvas-mention-panel__thumb--text">
      <FileTextOutlined />
    </span>
  )
}

export default function CanvasPromptInput({
  value,
  onChange,
  refs,
  placeholder,
  className,
  minRows = 1,
  maxRows = 4,
}: CanvasPromptInputProps) {
  const editorRef = useRef<HTMLDivElement>(null)
  const syncingRef = useRef(false)
  const [mentionOpen, setMentionOpen] = useState(false)
  const [mentionFilter, setMentionFilter] = useState('')
  const [activeIndex, setActiveIndex] = useState(0)
  const [caretRect, setCaretRect] = useState<DOMRect | null>(null)

  const refKey = useMemo(
    () => refs.map((r) => `${r.nodeId}:${r.mentionLabel}:${r.previewUrl || ''}`).join('|'),
    [refs],
  )

  const filteredRefs = useMemo(() => {
    const q = mentionFilter.trim().toLowerCase()
    if (!q) return refs
    return refs.filter(
      (r) =>
        r.mentionLabel.toLowerCase().includes(q) ||
        r.title.toLowerCase().includes(q) ||
        (r.previewText || '').toLowerCase().includes(q),
    )
  }, [refs, mentionFilter])

  const emitChange = useCallback(() => {
    const el = editorRef.current
    if (!el || syncingRef.current) return
    syncEditorEmptyState(el)
    const stored = editableToStored(serializeEditor(el), refs)
    syncingRef.current = true
    onChange(stored)
    syncingRef.current = false
  }, [onChange, refs])

  const refreshMention = useCallback(() => {
    const el = editorRef.current
    if (!el || refs.length === 0) {
      setMentionOpen(false)
      return
    }
    const trigger = findMentionTrigger(el)
    if (!trigger) {
      setMentionOpen(false)
      setMentionFilter('')
      setActiveIndex(0)
      return
    }
    setMentionFilter(trigger.filter)
    setMentionOpen(true)
    setCaretRect(getCaretClientRect())
  }, [refs.length])

  useEffect(() => {
    const el = editorRef.current
    if (!el || syncingRef.current) return
    const editable = storedToEditable(value, refs)
    rebuildEditorIfNeeded(el, editable, refs)
  }, [value, refKey, refs])

  useEffect(() => {
    setActiveIndex(0)
  }, [mentionFilter, mentionOpen])

  const pickMention = (ref: CanvasUpstreamRef) => {
    const el = editorRef.current
    if (!el) return
    insertMentionAtCursor(el, ref)
    setMentionOpen(false)
    setMentionFilter('')
    setActiveIndex(0)
    emitChange()
    el.focus()
  }

  const handleInput = () => {
    emitChange()
    refreshMention()
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    const mod = e.ctrlKey || e.metaKey
    if (mod && ['c', 'v', 'x', 'a'].includes(e.key.toLowerCase())) {
      e.stopPropagation()
    }
    if (mentionOpen && filteredRefs.length > 0) {
      if (e.key === 'ArrowDown') {
        e.preventDefault()
        setActiveIndex((i) => (i + 1) % filteredRefs.length)
        return
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault()
        setActiveIndex((i) => (i - 1 + filteredRefs.length) % filteredRefs.length)
        return
      }
      if (e.key === 'Enter' || e.key === 'Tab') {
        e.preventDefault()
        pickMention(filteredRefs[activeIndex])
        return
      }
    }
    if (e.key === 'Escape') {
      setMentionOpen(false)
    }
  }

  const handlePaste = (e: React.ClipboardEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    const text = e.clipboardData.getData('text/plain')
    if (!text) return
    insertPlainTextAtSelection(text)
    handleInput()
  }

  const minHeight = minRows * 22 + 8
  const maxHeight = maxRows * 22 + 8

  const dropdown =
    mentionOpen && refs.length > 0 && caretRect
      ? createPortal(
          <div
            className="canvas-mention-dropdown"
            style={{
              position: 'fixed',
              top: caretRect.bottom + 6,
              left: caretRect.left,
            }}
          >
            <div className="canvas-mention-dropdown__title">可能@的内容</div>
            {filteredRefs.length === 0 ? (
              <div className="canvas-mention-dropdown__empty">无匹配资源</div>
            ) : (
              <div className="canvas-mention-dropdown__list">
                {filteredRefs.map((ref, idx) => (
                  <button
                    key={ref.nodeId}
                    type="button"
                    className={`canvas-mention-dropdown__item${idx === activeIndex ? ' canvas-mention-dropdown__item--active' : ''}`}
                    onMouseDown={(ev) => {
                      ev.preventDefault()
                      pickMention(ref)
                    }}
                    onMouseEnter={() => setActiveIndex(idx)}
                  >
                    <MentionThumb refItem={ref} />
                    <span className="canvas-mention-dropdown__label">{ref.mentionLabel}</span>
                  </button>
                ))}
              </div>
            )}
          </div>,
          document.body,
        )
      : null

  return (
    <div className="canvas-prompt-input">
      <div
        ref={editorRef}
        className={`canvas-prompt-editor canvas-run-panel__input ${className || ''}`}
        contentEditable
        suppressContentEditableWarning
        role="textbox"
        aria-multiline="true"
        data-placeholder={placeholder || '输入 @ 引用上游文本或图片…'}
        data-empty="true"
        style={{ minHeight, maxHeight }}
        onInput={handleInput}
        onKeyDown={handleKeyDown}
        onPaste={handlePaste}
        onBlur={() => window.setTimeout(() => setMentionOpen(false), 120)}
        onFocus={refreshMention}
        onClick={refreshMention}
      />
      {dropdown}
    </div>
  )
}
