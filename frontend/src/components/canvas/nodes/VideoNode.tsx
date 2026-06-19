import { memo } from 'react'
import { type NodeProps } from '@xyflow/react'
import { VideoCameraOutlined } from '@ant-design/icons'
import BaseNodeShell from '../BaseNodeShell'
import NodeResultView from '../NodeResultView'
import NodeReferenceStrip from '../NodeReferenceStrip'
import type { CanvasNodeData } from '@/types/canvas'

function VideoNode({ data, selected }: NodeProps) {
  const d = data as unknown as CanvasNodeData
  const node = d.canvasNode
  const hasResult = !!node.result?.videos?.length

  return (
    <BaseNodeShell
      title={node.title || '视频'}
      icon={<VideoCameraOutlined />}
      selected={selected}
      stale={node.input_stale}
      status={node.status}
      minWidth={240}
      minHeight={200}
      onResizeEnd={d.onResizeEnd}
      onResizeStart={d.onResizeStart}
      onOpenPanel={d.onOpenPanel}
      onDuplicate={d.onDuplicate}
      referenceStrip={
        d.upstream ? <NodeReferenceStrip upstream={d.upstream} variant="node" /> : null
      }
      bodyClassName={hasResult ? 'canvas-node__body--media' : undefined}
    >
      {!hasResult &&
        (node.config.prompt ? (
          <div className="canvas-node__prompt-preview">{node.config.prompt}</div>
        ) : (
          <div className="canvas-result canvas-result--empty">在底部面板输入提示词</div>
        ))}
      <NodeResultView
        result={node.result}
        status={node.status}
        errorMessage={node.error_message}
        fitContain={hasResult}
      />
    </BaseNodeShell>
  )
}

export default memo(VideoNode)
