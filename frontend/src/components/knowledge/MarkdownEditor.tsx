import { useMemo } from 'react'
import MDEditor from '@uiw/react-md-editor'
import '@uiw/react-md-editor/markdown-editor.css'
import '@uiw/react-markdown-preview/markdown.css'
import { useSiteTheme } from '@/hooks/useSiteTheme'

interface MarkdownEditorProps {
  value?: string
  onChange?: (value: string) => void
  height?: number
  preview?: 'live' | 'edit' | 'preview'
  readOnly?: boolean
}

export default function MarkdownEditor({
  value = '',
  onChange,
  height = 420,
  preview = 'live',
  readOnly = false,
}: MarkdownEditorProps) {
  const { effective } = useSiteTheme()
  const colorMode = useMemo(() => (effective === 'dark' ? 'dark' : 'light'), [effective])

  return (
    <div className="markdown-editor-wrap" data-color-mode={colorMode}>
      <MDEditor
        value={value}
        onChange={(v) => onChange?.(v ?? '')}
        height={height}
        preview={preview}
        visibleDragbar={!readOnly}
        hideToolbar={readOnly}
        textareaProps={{ readOnly, spellCheck: false }}
      />
    </div>
  )
}
