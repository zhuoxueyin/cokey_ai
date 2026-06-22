import { Handle, NodeResizeControl, Position } from '@xyflow/react'
import { FormOutlined, CopyOutlined } from '@ant-design/icons'
import { Tooltip } from 'antd'
import type { ReactNode } from 'react'
import InlineEditableTitle from './InlineEditableTitle'

interface BaseNodeShellProps {
  title: string
  icon?: ReactNode
  selected?: boolean
  stale?: boolean
  status?: string
  children: ReactNode
  showInput?: boolean
  showOutput?: boolean
  minWidth?: number
  minHeight?: number
  resizable?: boolean
  onResizeEnd?: (width: number, height: number) => void
  onResizeStart?: () => void
  headerExtra?: ReactNode
  bodyClassName?: string
  /** 顶部上游引用小方块（文本/图片/视频节点） */
  referenceStrip?: ReactNode
  /** 点击打开底部编辑面板（图片/视频/文本生成节点） */
  onOpenPanel?: () => void
  /** 复制节点 */
  onDuplicate?: () => void
  /** 双击 header 重命名 */
  onTitleChange?: (title: string) => void
}

export default function BaseNodeShell({
  title,
  icon,
  selected,
  stale,
  status,
  children,
  showInput = true,
  showOutput = true,
  minWidth = 200,
  minHeight = 120,
  resizable = true,
  onResizeEnd,
  onResizeStart,
  headerExtra,
  bodyClassName,
  referenceStrip,
  onOpenPanel,
  onDuplicate,
  onTitleChange,
}: BaseNodeShellProps) {
  return (
    <div
      className={`canvas-node ${selected ? 'canvas-node--selected' : ''} ${stale ? 'canvas-node--stale' : ''}`}
    >
      {showInput && (
        <Handle type="target" position={Position.Left} id="input" className="canvas-handle canvas-handle--input">
          <span className="canvas-handle__dot" aria-hidden />
        </Handle>
      )}
      <div className="canvas-node__header">
        {icon && <span className="canvas-node__icon">{icon}</span>}
        <InlineEditableTitle title={title} onTitleChange={onTitleChange} />
        {headerExtra}
        {onOpenPanel && selected && (
          <Tooltip title="编辑任务">
            <button
              type="button"
              className="canvas-node__edit-btn nodrag nopan"
              onClick={(e) => {
                e.stopPropagation()
                onOpenPanel()
              }}
            >
              <FormOutlined />
            </button>
          </Tooltip>
        )}
        {onDuplicate && selected && (
          <Tooltip title="复制节点">
            <button
              type="button"
              className="canvas-node__edit-btn nodrag nopan"
              onClick={(e) => {
                e.stopPropagation()
                onDuplicate()
              }}
            >
              <CopyOutlined />
            </button>
          </Tooltip>
        )}
        {status === 'running' && <span className="canvas-node__badge canvas-node__badge--running">运行中</span>}
        {stale && <span className="canvas-node__badge canvas-node__badge--stale">输入已变化</span>}
      </div>
      {referenceStrip}
      <div className={`canvas-node__body${bodyClassName ? ` ${bodyClassName}` : ''}`}>{children}</div>
      {showOutput && (
        <Handle type="source" position={Position.Right} id="output" className="canvas-handle canvas-handle--output">
          <span className="canvas-handle__dot" aria-hidden />
        </Handle>
      )}
      {resizable && (
        <NodeResizeControl
          position="bottom-right"
          minWidth={minWidth}
          minHeight={minHeight}
          onResizeStart={onResizeStart}
          onResizeEnd={(_, { width, height }) => onResizeEnd?.(width, height)}
          className={`canvas-node__resize-handle nodrag nopan${selected ? '' : ' canvas-node__resize-handle--hidden'}`}
        />
      )}
    </div>
  )
}
