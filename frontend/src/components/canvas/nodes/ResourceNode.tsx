import { memo, useState } from 'react'
import { type NodeProps } from '@xyflow/react'
import { FileImageOutlined } from '@ant-design/icons'
import { message } from 'antd'
import BaseNodeShell from '../BaseNodeShell'
import ResourceImageToolbox from '../ResourceImageToolbox'
import ResourceImageMarkEditor from '../ResourceImageMarkEditor'
import { uploadImage } from '@/api'
import type { CanvasNodeData } from '@/types/canvas'
import type { ImageMarkLayer, ImageMarkTool } from '@/types/imageMark'

function ResourceNode({ data, selected }: NodeProps) {
  const d = data as unknown as CanvasNodeData
  const node = d.canvasNode
  const url = node.config.resource_url
  const isVideo = node.config.resource_type === 'video'
  const [marking, setMarking] = useState(false)
  const [markInitialTool, setMarkInitialTool] = useState<ImageMarkTool>('brush')

  const openMarkEditor = (tool: ImageMarkTool = 'brush') => {
    setMarkInitialTool(tool)
    setMarking(true)
  }

  const handleSaveMark = async (layers: ImageMarkLayer[], blob: Blob) => {
    const file = new File([blob], `marked-${Date.now()}.png`, { type: 'image/png' })
    const res = await uploadImage(file)
    if (res.code !== 'success' || !res.data?.url) {
      throw new Error(res.message || '上传失败')
    }
    await d.onUpdateConfig?.({
      resource_url: res.data.url,
      mark_layers: layers,
      mark_source_url: node.config.mark_source_url || url,
    })
    setMarking(false)
    message.success('标记已保存')
  }

  const showToolbox = selected && !isVideo && !!url && !marking

  return (
    <BaseNodeShell
      title={node.title || node.config.resource_name || '资源'}
      icon={<FileImageOutlined />}
      selected={selected}
      showInput={false}
      showOutput
      minWidth={240}
      minHeight={220}
      onResizeEnd={d.onResizeEnd}
      onResizeStart={d.onResizeStart}
      onDuplicate={d.onDuplicate}
      bodyClassName="canvas-node__body--media canvas-node__body--resource"
    >
      {url ? (
        isVideo ? (
          <video src={url} controls className="canvas-result__video nodrag nopan" />
        ) : marking ? (
          <ResourceImageMarkEditor
            imageUrl={node.config.mark_source_url || url}
            initialLayers={node.config.mark_layers}
            initialTool={markInitialTool}
            onCancel={() => setMarking(false)}
            onSave={handleSaveMark}
          />
        ) : (
          <div className="canvas-resource-media">
            {showToolbox && (
              <div className="canvas-resource-toolbox-wrap">
                <ResourceImageToolbox
                  imageUrl={url}
                  imageName={node.config.resource_name || node.title}
                  onMark={openMarkEditor}
                />
              </div>
            )}
            <img src={url} alt="" className="canvas-result__image canvas-result__image--contain" draggable={false} />
          </div>
        )
      ) : (
        <div className="canvas-result canvas-result--empty">未上传</div>
      )}
    </BaseNodeShell>
  )
}

export default memo(ResourceNode)
