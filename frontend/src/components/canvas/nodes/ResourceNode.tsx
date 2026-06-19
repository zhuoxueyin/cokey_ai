import { memo } from 'react'
import { type NodeProps } from '@xyflow/react'
import { FileImageOutlined } from '@ant-design/icons'
import BaseNodeShell from '../BaseNodeShell'
import type { CanvasNodeData } from '@/types/canvas'

function ResourceNode({ data, selected }: NodeProps) {
  const d = data as unknown as CanvasNodeData
  const node = d.canvasNode
  const url = node.config.resource_url
  const isVideo = node.config.resource_type === 'video'

  return (
    <BaseNodeShell
      title={node.title || node.config.resource_name || '资源'}
      icon={<FileImageOutlined />}
      selected={selected}
      showInput={false}
      showOutput
      minWidth={200}
      minHeight={160}
      onResizeEnd={d.onResizeEnd}
      onResizeStart={d.onResizeStart}
      onDuplicate={d.onDuplicate}
    >
      {url ? (
        isVideo ? (
          <video src={url} controls className="canvas-result__video" />
        ) : (
          <img src={url} alt="" className="canvas-result__image canvas-result__image--contain" />
        )
      ) : (
        <div className="canvas-result canvas-result--empty">未上传</div>
      )}
    </BaseNodeShell>
  )
}

export default memo(ResourceNode)
