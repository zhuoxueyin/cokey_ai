import { memo } from 'react'
import { NodeResizer, type NodeProps } from '@xyflow/react'
import { GroupOutlined } from '@ant-design/icons'

type GroupNodeData = { label?: string }

function GroupNode({ data, selected }: NodeProps) {
  const label = (data as GroupNodeData | undefined)?.label
  return (
    <div className={`canvas-group-node${selected ? ' canvas-group-node--selected' : ''}`}>
      <div className="canvas-group-node__header nodrag">
        <GroupOutlined />
        <span>{label || '分组'}</span>
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
