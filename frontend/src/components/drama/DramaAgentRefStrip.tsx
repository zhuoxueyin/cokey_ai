import { Tooltip } from 'antd'
import { CloseOutlined, PictureOutlined } from '@ant-design/icons'
import type { DramaAgentRef } from '@/types/dramaAgent'

interface DramaAgentRefStripProps {
  refs: DramaAgentRef[]
  /** 传入则显示删除按钮（输入框引用区） */
  onRemove?: (ref: DramaAgentRef) => void
  size?: 'sm' | 'md'
  className?: string
}

export default function DramaAgentRefStrip({
  refs,
  onRemove,
  size = 'md',
  className,
}: DramaAgentRefStripProps) {
  if (!refs.length) return null

  return (
    <div
      className={`drama-agent-ref-strip drama-agent-ref-strip--${size}${className ? ` ${className}` : ''}`}
    >
      {refs.map((ref, index) => {
        const key = ref.id || ref.url || `ref-${index}`
        const url = ref.url?.trim()
        const tooltipTitle = url ? (
          <img src={url} alt="" className="drama-agent-ref-strip__tooltip-img" />
        ) : (
          ref.name || '引用资源'
        )

        return (
          <Tooltip
            key={key}
            title={tooltipTitle}
            placement="top"
            overlayClassName="drama-agent-ref-tooltip"
          >
            <div className="drama-agent-ref-strip__item">
              {url ? (
                <img src={url} alt="" className="drama-agent-ref-strip__img" />
              ) : (
                <span className="drama-agent-ref-strip__placeholder">
                  <PictureOutlined />
                </span>
              )}
              {onRemove && (
                <button
                  type="button"
                  className="drama-agent-ref-strip__remove"
                  aria-label="移除引用"
                  onClick={() => onRemove(ref)}
                >
                  <CloseOutlined />
                </button>
              )}
            </div>
          </Tooltip>
        )
      })}
    </div>
  )
}
