import { useEffect, useRef, useState } from 'react'

interface InlineEditableTitleProps {
  title: string
  className?: string
  editable?: boolean
  onTitleChange?: (title: string) => void
}

export default function InlineEditableTitle({
  title,
  className = 'canvas-node__title',
  editable = true,
  onTitleChange,
}: InlineEditableTitleProps) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(title)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    setDraft(title)
  }, [title])

  useEffect(() => {
    if (editing) inputRef.current?.focus()
  }, [editing])

  const commit = () => {
    setEditing(false)
    const next = draft.trim()
    if (!next) {
      setDraft(title)
      return
    }
    if (next !== title) onTitleChange?.(next)
    else setDraft(title)
  }

  if (!editable || !onTitleChange) {
    return <span className={className}>{title}</span>
  }

  if (editing) {
    return (
      <input
        ref={inputRef}
        className={`${className} canvas-node__title-input nodrag nopan`}
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={commit}
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            e.preventDefault()
            commit()
          }
          if (e.key === 'Escape') {
            setDraft(title)
            setEditing(false)
          }
        }}
        onClick={(e) => e.stopPropagation()}
        onDoubleClick={(e) => e.stopPropagation()}
        onMouseDown={(e) => e.stopPropagation()}
      />
    )
  }

  return (
    <span
      className={`${className} canvas-node__title--editable`}
      title="双击重命名"
      onDoubleClick={(e) => {
        e.stopPropagation()
        setEditing(true)
      }}
    >
      {title}
    </span>
  )
}
