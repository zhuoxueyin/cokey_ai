import { memo } from 'react'
import { type NodeProps } from '@xyflow/react'
import { VideoCameraOutlined } from '@ant-design/icons'
import BaseNodeShell from '../BaseNodeShell'
import NodeResultView from '../NodeResultView'
import NodeReferenceStrip from '../NodeReferenceStrip'
import { resolveNodeDisplayStatus } from '@/utils/canvasNodeStatus'
import type { CanvasNodeData } from '@/types/canvas'

function VideoNode({ data, selected }: NodeProps) {
  const d = data as unknown as CanvasNodeData
  const node = d.canvasNode
  const hasResult = !!node.result?.videos?.length
  const displayStatus = resolveNodeDisplayStatus(node, d.activeRunNodeId)
  const showLoading = displayStatus === 'running'

  return (
    <BaseNodeShell
      title={node.title || '视频'}
      icon={<VideoCameraOutlined />}
      selected={selected}
      stale={node.input_stale}
      status={displayStatus}
      minWidth={240}
      minHeight={200}
      onResizeEnd={d.onResizeEnd}
      onResizeStart={d.onResizeStart}
      onOpenPanel={d.onOpenPanel}
      onDuplicate={d.onDuplicate}
      onTitleChange={d.onTitleChange}
      referenceStrip={
        d.upstream ? <NodeReferenceStrip upstream={d.upstream} variant="node" /> : null
      }
      bodyClassName={
        showLoading ? 'canvas-node__body--running' : hasResult ? 'canvas-node__body--media' : undefined
      }
    >
      {!hasResult && !showLoading &&
        (node.config.prompt || node.config.style_preset_name ? (
          <div className="canvas-node__prompt-preview">
            {node.config.style_preset_name && (
              <div className="canvas-node__style-tag">风格：{node.config.style_preset_name}</div>
            )}
            {node.config.prompt || '（仅风格参考，无额外描述）'}
          </div>
        ) : (
          <div className="canvas-result canvas-result--empty">在底部面板输入提示词</div>
        ))}
      <NodeResultView
        result={node.result}
        status={displayStatus}
        errorMessage={node.error_message}
        fitContain={hasResult}
      />
    </BaseNodeShell>
  )
}

export default memo(VideoNode)
