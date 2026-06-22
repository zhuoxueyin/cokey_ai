import { memo, useEffect, useRef } from 'react'
import { type NodeProps } from '@xyflow/react'
import { PictureOutlined } from '@ant-design/icons'
import BaseNodeShell from '../BaseNodeShell'
import NodeResultView from '../NodeResultView'
import NodeReferenceStrip from '../NodeReferenceStrip'
import { resolveNodeDisplayStatus } from '@/utils/canvasNodeStatus'
import type { CanvasNodeData } from '@/types/canvas'
import { computeImageNodeSize, loadImageDimensions, pickOutputImageUrl } from '@/utils/canvasNodeSize'

function ImageNode({ data, selected }: NodeProps) {
  const d = data as unknown as CanvasNodeData
  const node = d.canvasNode
  const autoSizedKeyRef = useRef<string | null>(null)
  const primaryIndex = d.primaryImageIndex ?? node.config.output_image_index ?? 0

  useEffect(() => {
    if (node.config.user_resized) return
    const url = pickOutputImageUrl(node.result, primaryIndex)
    if (!url) return
    const key = `${node.result_version}:${primaryIndex}:${url}`
    if (autoSizedKeyRef.current === key) return

    let cancelled = false
    loadImageDimensions(url).then(({ width, height }) => {
      if (cancelled || !width || !height) return
      autoSizedKeyRef.current = key
      const size = computeImageNodeSize(width, height)
      d.onAutoSize?.(size.width, size.height)
    })

    return () => {
      cancelled = true
    }
  }, [node.result, node.result_version, node.config.user_resized, primaryIndex, d.onAutoSize])

  const hasResult = !!node.result?.images?.length
  const displayStatus = resolveNodeDisplayStatus(node, d.activeRunNodeId)
  const showLoading = displayStatus === 'running'
  const imageCount = node.result?.images?.length ?? 0
  const onSelectPrimary = d.onSelectPrimaryImage ?? d.onSelectOutputImage

  return (
    <BaseNodeShell
      title={node.title || '图片'}
      icon={<PictureOutlined />}
      selected={selected}
      stale={node.input_stale}
      status={displayStatus}
      minWidth={200}
      minHeight={180}
      onResizeEnd={d.onResizeEnd}
      onResizeStart={d.onResizeStart}
      onOpenPanel={d.onOpenPanel}
      onDuplicate={d.onDuplicate}
      onTitleChange={d.onTitleChange}
      referenceStrip={
        d.upstream ? <NodeReferenceStrip upstream={d.upstream} variant="node" /> : null
      }
      bodyClassName={
        showLoading
          ? 'canvas-node__body--running'
          : hasResult && !showLoading
            ? 'canvas-node__body--media'
            : undefined
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
          <div className="canvas-result canvas-result--empty">连接上游节点引入参考，或在下方输入提示词</div>
        ))}
      <NodeResultView
        result={node.result}
        status={displayStatus}
        errorMessage={node.error_message}
        fitContain={hasResult && !showLoading}
        primaryImageIndex={primaryIndex}
        onSelectPrimaryImage={imageCount > 1 ? onSelectPrimary : undefined}
      />
    </BaseNodeShell>
  )
}

export default memo(ImageNode)
