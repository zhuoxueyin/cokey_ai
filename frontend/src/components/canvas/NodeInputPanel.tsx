import { Alert, Button } from 'antd'
import { WarningOutlined } from '@ant-design/icons'
import type { CanvasNode, CanvasNodeConfig } from '@/types/canvas'
import type { CanvasUpstreamPreview } from '@/utils/canvasUpstream'
import TextComposerPanel from './TextComposerPanel'
import ImageComposerPanel from './ImageComposerPanel'
import VideoComposerPanel from './VideoComposerPanel'

interface NodeInputPanelProps {
  node: CanvasNode
  upstream: CanvasUpstreamPreview
  running?: boolean
  onRun: (config: CanvasNodeConfig) => void
  onAckStale: () => void
  onUpdateConfig: (patch: Partial<CanvasNodeConfig>) => void
  onPanelDragStart?: () => void
}

export default function NodeInputPanel({
  node,
  upstream,
  running,
  onRun,
  onAckStale,
  onUpdateConfig,
  onPanelDragStart,
}: NodeInputPanelProps) {
  const textMode = node.config.text_mode || 'generate'

  const handlePanelMouseDown = (e: React.MouseEvent) => {
    const target = e.target as HTMLElement
    if (
      target.closest(
        'button, textarea, input, select, a, [contenteditable="true"], .canvas-prompt-editor, .canvas-prompt-input, .ant-select, .ant-segmented, .ant-input, .ant-input-affix-wrapper, .ant-popover',
      )
    ) {
      return
    }
    const startX = e.clientX
    const startY = e.clientY
    const onMove = (ev: MouseEvent) => {
      if (Math.abs(ev.clientX - startX) + Math.abs(ev.clientY - startY) > 6) {
        onPanelDragStart?.()
        document.removeEventListener('mousemove', onMove)
        document.removeEventListener('mouseup', onUp)
      }
    }
    const onUp = () => {
      document.removeEventListener('mousemove', onMove)
      document.removeEventListener('mouseup', onUp)
    }
    document.addEventListener('mousemove', onMove)
    document.addEventListener('mouseup', onUp)
  }

  if (node.node_type === 'resource') return null

  return (
    <div className="canvas-run-panel canvas-run-panel--floating" onMouseDown={handlePanelMouseDown}>
      {node.input_stale && (
        <Alert
          type="warning"
          showIcon
          icon={<WarningOutlined />}
          message="上游节点结果已更新，当前输入可能已过期"
          action={
            <Button size="small" onClick={onAckStale}>
              知道了
            </Button>
          }
          className="canvas-run-panel__stale"
        />
      )}

      {node.node_type === 'text' && textMode === 'generate' && (
        <TextComposerPanel
          config={node.config}
          upstreamRefs={upstream.refs}
          running={running}
          onRun={onRun}
          onUpdateConfig={onUpdateConfig}
        />
      )}

      {node.node_type === 'image' && (
        <ImageComposerPanel
          nodeId={node.node_id}
          configRevision={node.updated_at}
          config={node.config}
          running={running}
          upstream={upstream}
          onRun={onRun}
          onUpdateConfig={onUpdateConfig}
        />
      )}

      {node.node_type === 'video' && (
        <VideoComposerPanel
          nodeId={node.node_id}
          configRevision={node.updated_at}
          config={node.config}
          running={running}
          upstream={upstream}
          onRun={onRun}
          onUpdateConfig={onUpdateConfig}
        />
      )}
    </div>
  )
}
