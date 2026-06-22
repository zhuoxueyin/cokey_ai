import { memo } from 'react'
import { NodeResizer, type NodeProps } from '@xyflow/react'
import { GroupOutlined } from '@ant-design/icons'
import InlineEditableTitle from '../InlineEditableTitle'

type GroupNodeData = {
  label?: string
  onTitleChange?: (title: string) => void
}

function GroupNode({ data, selected }: NodeProps) {
  const d = data as GroupNodeData | undefined
  const label = d?.label || '分组'
  return (
    <div className={`canvas-group-node${selected ? ' canvas-group-node--selected' : ''}`}>
      <div className="canvas-group-node__header nodrag">
        <GroupOutlined />
        <InlineEditableTitle
          title={label}
          className="canvas-group-node__title"
          onTitleChange={d?.onTitleChange}
        />
      </div>
      <NodeResizer
        minWidth={160}
        minHeight={120}
        isVisible={Boolean(selected)}
        lineClassName="canvas-group-node__resize-line"
        handleClassName="canvas-group-node__resize-handle"
      />
    </div>
  )
}

export default memo(GroupNode)
