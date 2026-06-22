import { useEffect, useRef, useState } from 'react'
import { Select, Tooltip } from 'antd'
import {
  ArrowUpOutlined,
  BgColorsOutlined,
  CheckOutlined,
  TagOutlined,
} from '@ant-design/icons'
import type { ModelItem } from '@/types'
import type { DramaStylePreset } from '@/types/drama'
import type { DramaAgentMode, DramaAgentRef } from '@/types/dramaAgent'
import { AGENT_MODE_PLACEHOLDERS, AGENT_MODE_SHORTCUTS } from '@/types/dramaAgent'
import AssetPicker from '@/components/AssetPicker'
import StylePickerGrid from '@/components/drama/StylePickerGrid'
import { sortModelsByAdminOrder } from '@/utils/modelOrder'
import { mergeAgentRefs } from '@/utils/dramaAgentRefs'
import DramaAgentRefStrip from './DramaAgentRefStrip'

export interface DramaAgentComposerProps {
  variant?: 'landing' | 'compact'
  agentMode: DramaAgentMode
  onAgentModeChange: (mode: DramaAgentMode) => void
  modelCode?: string
  onModelCodeChange: (code: string) => void
  models: ModelItem[]
  stylePresetId?: string
  onStylePresetChange: (id?: string) => void
  styles: DramaStylePreset[]
  refs: DramaAgentRef[]
  onRefsChange: (refs: DramaAgentRef[]) => void
  loading?: boolean
  onSend: (message: string, refs: DramaAgentRef[]) => void
  /** 对话已开始后锁定创作类型，不可切换 */
  modeLocked?: boolean
  /** 已选定风格后全对话锁定，仅可在风格面板更换或取消 */
  styleLocked?: boolean
  /** 画布内创作助手：可引用当前画布节点图片 */
  canvasProjectId?: string
}

export default function DramaAgentComposer({
  variant = 'landing',
  agentMode,
  onAgentModeChange,
  modelCode,
  onModelCodeChange,
  models,
  stylePresetId,
  onStylePresetChange,
  styles,
  refs,
  onRefsChange,
  loading,
  onSend,
  modeLocked = false,
  styleLocked = false,
  canvasProjectId,
}: DramaAgentComposerProps) {
  const [text, setText] = useState('')
  const [assetOpen, setAssetOpen] = useState(false)
  const [styleOpen, setStyleOpen] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const selectedStyle = styles.find((s) => s.style_id === stylePresetId)
  const inputPlaceholder = AGENT_MODE_PLACEHOLDERS[agentMode]

  useEffect(() => {
    if (variant === 'landing' && textareaRef.current) {
      textareaRef.current.focus()
    }
  }, [variant])

  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    const cap = variant === 'compact' ? 120 : 200
    el.style.height = `${Math.min(el.scrollHeight, cap)}px`
  }, [text, variant])

  const handleSend = () => {
    const msg = text.trim()
    if (!msg || loading) return
    const outgoingRefs = refs
    onRefsChange([])
    onSend(msg, outgoingRefs)
    setText('')
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === '@') {
      setAssetOpen(true)
    }
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleModeSelect = (mode: DramaAgentMode) => {
    if (modeLocked && mode !== agentMode) return
    onAgentModeChange(mode)
  }

  const modeShortcuts = (
    <div
      className={`drama-agent-composer__shortcuts${
        variant === 'compact' ? ' drama-agent-composer__shortcuts--compact' : ''
      }${modeLocked ? ' drama-agent-composer__shortcuts--locked' : ''}`}
    >
      {AGENT_MODE_SHORTCUTS.map((s) => {
        const active = agentMode === s.mode
        const disabled = modeLocked && !active
        return (
          <button
            key={s.mode}
            type="button"
            disabled={disabled}
            aria-pressed={active}
            title={disabled ? '对话已开始，创作类型已锁定' : s.label}
            className={`drama-agent-composer__shortcut${
              active ? ' drama-agent-composer__shortcut--active' : ''
            }${disabled ? ' drama-agent-composer__shortcut--disabled' : ''}`}
            style={active ? ({ '--mode-accent': s.gradient } as React.CSSProperties) : undefined}
            onClick={() => handleModeSelect(s.mode)}
          >
            <span className="drama-agent-composer__shortcut-icon" style={{ background: s.gradient }}>
              {s.icon}
            </span>
            <span>{s.label}</span>
            {active && <CheckOutlined className="drama-agent-composer__shortcut-check" />}
          </button>
        )
      })}
    </div>
  )

  const modelPicker = (
    <Select
      value={modelCode}
      onChange={onModelCodeChange}
      style={{ minWidth: 160 }}
      size="small"
      placeholder="选择模型"
      popupClassName="drama-agent-model-dropdown"
      getPopupContainer={(triggerNode) => triggerNode.parentElement ?? document.body}
      options={sortModelsByAdminOrder(models).map((m) => ({
        value: m.model_code,
        label: m.model_name || m.model_code,
      }))}
    />
  )

  return (
    <div className={`drama-agent-composer drama-agent-composer--${variant}`}>
      {variant === 'landing' && (
        <h1 className="drama-agent-composer__headline">有什么新的故事灵感？</h1>
      )}

      {variant === 'compact' && !modeLocked && modeShortcuts}

      <div className="drama-agent-composer__box">
        {refs.length > 0 && (
          <DramaAgentRefStrip
            refs={refs}
            className="drama-agent-composer__ref-row"
            onRemove={(ref) => onRefsChange(refs.filter((x) => x !== ref))}
          />
        )}

        <textarea
          ref={textareaRef}
          className="drama-agent-composer__input"
          placeholder={inputPlaceholder}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={variant === 'landing' ? 3 : 2}
        />

        <div className="drama-agent-composer__toolbar">
          <div className="drama-agent-composer__tools-left">
            <Tooltip title="@ 引用资源">
              <button
                type="button"
                className="drama-agent-composer__icon-btn"
                onClick={() => setAssetOpen(true)}
              >
                <TagOutlined />
              </button>
            </Tooltip>
            <Tooltip
              title={
                selectedStyle
                  ? styleLocked
                    ? `风格已锁定：${selectedStyle.name}（点击可更换或取消绑定）`
                    : `风格：${selectedStyle.name}`
                  : styleLocked
                    ? '选择视觉风格（选定后全对话锁定）'
                    : '选择视觉风格'
              }
            >
              <button
                type="button"
                className={`drama-agent-composer__icon-btn${
                  stylePresetId ? ' drama-agent-composer__icon-btn--active' : ''
                }`}
                onClick={() => setStyleOpen(true)}
              >
                <BgColorsOutlined />
              </button>
            </Tooltip>
            {selectedStyle && (
              <span className="drama-agent-composer__style-label">{selectedStyle.name}</span>
            )}
          </div>

          <div className="drama-agent-composer__tools-center">{modelPicker}</div>

          <div className="drama-agent-composer__tools-right">
            <button
              type="button"
              className="drama-agent-composer__send"
              disabled={!text.trim() || loading}
              onClick={handleSend}
            >
              <ArrowUpOutlined />
            </button>
          </div>
        </div>
      </div>

      {variant === 'landing' && !modeLocked && modeShortcuts}

      <StylePickerGrid
        open={styleOpen}
        onClose={() => setStyleOpen(false)}
        styles={styles}
        value={stylePresetId}
        onChange={onStylePresetChange}
      />

      <AssetPicker
        open={assetOpen}
        onClose={() => setAssetOpen(false)}
        multiple
        category="image"
        canvasProjectId={canvasProjectId}
        zIndex={3000}
        onSelectRefs={(picked) => {
          onRefsChange(mergeAgentRefs(refs, picked))
          setAssetOpen(false)
        }}
      />
    </div>
  )
}
