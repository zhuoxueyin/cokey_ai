import { useEffect, useState } from 'react'
import { NodeResizeControl, type NodeProps } from '@xyflow/react'
import type { CanvasNodeData } from '@/types/canvas'
import { buildTitleRenderKey, resolveTitleContent, titleTextStyle } from '@/utils/titleNodeStyles'

function TitleNode({ data, selected }: NodeProps) {
  const d = data as unknown as CanvasNodeData & { titleRenderKey?: string }
  const node = d.canvasNode
  const config = node.config
  const renderKey = d.titleRenderKey ?? buildTitleRenderKey(config)
  const remoteContent = resolveTitleContent(config)
  const [content, setContent] = useState(remoteContent)
  const [textStyle, setTextStyle] = useState(() => titleTextStyle(config))

  useEffect(() => {
    setContent(resolveTitleContent(config))
    setTextStyle(titleTextStyle(config))
  }, [node.node_id, renderKey])

  const lines = content.split('\n')

  return (
    <div className={`canvas-title-node${selected ? ' canvas-title-node--selected' : ''}`}>
      <div className="canvas-title-node__display" style={textStyle}>
        {lines.map((line, index) => (
          <div key={index} className="canvas-title-node__line">
            {line || '\u00A0'}
          </div>
        ))}
      </div>
      {selected && (
        <NodeResizeControl
          position="bottom-right"
          minWidth={160}
          minHeight={48}
          onResizeStart={d.onResizeStart}
          onResizeEnd={(_, { width, height }) => d.onResizeEnd?.(width, height)}
          className="canvas-node__resize-handle nodrag nopan canvas-title-node__resize"
        />
      )}
    </div>
  )
}

export default TitleNode
