import { memo, useEffect, useState } from 'react'
import { type NodeProps } from '@xyflow/react'
import { FileTextOutlined } from '@ant-design/icons'
import BaseNodeShell from '../BaseNodeShell'
import NodeReferenceStrip from '../NodeReferenceStrip'
import type { CanvasNodeData } from '@/types/canvas'

function TextNode({ data, selected }: NodeProps) {
  const d = data as unknown as CanvasNodeData
  const node = d.canvasNode
  const textMode = node.config.text_mode || 'generate'
  const remoteText =
    textMode === 'manual'
      ? node.config.content ?? node.result?.text ?? ''
      : node.result?.text ?? ''

  const [text, setText] = useState(remoteText)

  useEffect(() => {
    setText(remoteText)
  }, [node.node_id, remoteText])

  const placeholder =
    textMode === 'manual'
      ? '在此直接输入文本…'
      : '生成结果将显示在此\n点击下方面板描述需求并运行'

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const next = e.target.value
    setText(next)
    d.onEditText?.(next)
  }

  return (
    <BaseNodeShell
      title={node.title || '文本'}
      icon={<FileTextOutlined />}
      selected={selected}
      stale={node.input_stale}
      status={node.status}
      minWidth={200}
      minHeight={160}
      onResizeEnd={d.onResizeEnd}
      onResizeStart={d.onResizeStart}
      onOpenPanel={d.onOpenPanel}
      onDuplicate={d.onDuplicate}
      referenceStrip={
        d.upstream ? <NodeReferenceStrip upstream={d.upstream} variant="node" /> : null
      }
      bodyClassName="canvas-node__body--text"
    >
      {node.status === 'running' && (
        <div className="canvas-result canvas-result--loading canvas-node__text-status">生成中…</div>
      )}
      {node.status === 'failed' && (
        <div className="canvas-result canvas-result--error canvas-node__text-status">
          {node.error_message || '生成失败'}
        </div>
      )}
      <textarea
        className="canvas-node__text-editor nodrag nopan nowheel"
        value={text}
        onChange={handleChange}
        placeholder={placeholder}
        disabled={node.status === 'running'}
        onMouseDown={(e) => e.stopPropagation()}
        onPointerDown={(e) => e.stopPropagation()}
        onDoubleClick={(e) => e.stopPropagation()}
      />
    </BaseNodeShell>
  )
}

export default memo(TextNode)
