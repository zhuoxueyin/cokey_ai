/** 是否处于文本编辑态（应让浏览器/组件处理复制粘贴等快捷键） */
export function isTextEditingTarget(target: EventTarget | null): boolean {
  if (!target || !(target instanceof HTMLElement)) return false
  const el = target as HTMLElement
  const tag = el.tagName
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return true
  if (el.isContentEditable) return true
  return Boolean(el.closest('[contenteditable="true"]'))
}

/** 当前是否有用户选中的文本（应用原生复制） */
export function hasTextSelection(): boolean {
  const sel = window.getSelection()
  return Boolean(sel && sel.type === 'Range' && sel.toString().length > 0)
}

/** 是否位于 Drawer / Modal 等浮层内（不应劫持画布快捷键） */
export function isOverlayPanelTarget(target: EventTarget | null): boolean {
  if (!target || !(target instanceof HTMLElement)) return false
  return Boolean(
    target.closest('.ant-drawer, .ant-modal, .ant-modal-root, .canvas-run-history-drawer, .canvas-run-detail-modal, .canvas-resource-mark-editor'),
  )
}
