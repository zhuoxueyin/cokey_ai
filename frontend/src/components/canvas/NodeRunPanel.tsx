import { useEffect, useState } from 'react'
import { Button, Input, Select, Alert, message } from 'antd'
import { ArrowUpOutlined, WarningOutlined } from '@ant-design/icons'
import { getModels } from '@/api'
import type { ModelItem } from '@/types'
import type { CanvasNode, CanvasNodeConfig } from '@/types/canvas'

interface NodeRunPanelProps {
  node: CanvasNode | null
  running?: boolean
  onRun: (config: CanvasNodeConfig) => void
  onAckStale: () => void
  onUpdateConfig: (config: Partial<CanvasNodeConfig>) => void
}

const categoryMap: Record<string, string> = {
  text: 'text',
  image: 'image',
  video: 'video',
}

export default function NodeRunPanel({ node, running, onRun, onAckStale, onUpdateConfig }: NodeRunPanelProps) {
  const [models, setModels] = useState<ModelItem[]>([])
  const [prompt, setPrompt] = useState('')
  const [modelCode, setModelCode] = useState<string | undefined>()

  useEffect(() => {
    if (!node || node.node_type === 'resource') return
    const category = categoryMap[node.node_type]
    getModels(category).then((res) => {
      if (res.code === 'success' && res.data) {
        setModels(res.data)
        const current = node.config.model_code
        const def = res.data.find((m) => m.model_code === current) || res.data.find((m) => m.is_default) || res.data[0]
        setModelCode(def?.model_code)
      }
    })
    setPrompt(node.config.prompt || '')
    setModelCode(node.config.model_code)
  }, [node?.node_id, node?.node_type])

  if (!node || node.node_type === 'resource') {
    return (
      <div className="canvas-run-panel canvas-run-panel--empty">
        <span>选择节点后在底部配置并运行</span>
      </div>
    )
  }

  const placeholders: Record<string, string> = {
    text: '写下你想生成的文本内容…',
    image: '描述你想要生成的画面，上游节点结果将作为参考输入…',
    video: '描述你想要生成的视频内容，@引用已通过连线传入…',
  }

  const handleRun = () => {
    if (!modelCode) {
      message.warning('请选择模型')
      return
    }
    onRun({ prompt, model_code: modelCode, params: node.config.params || {} })
  }

  const handlePromptBlur = () => {
    if (prompt !== (node.config.prompt || '')) {
      onUpdateConfig({ prompt })
    }
  }

  const handleModelChange = (code: string) => {
    setModelCode(code)
    onUpdateConfig({ model_code: code })
  }

  return (
    <div className="canvas-run-panel">
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
      <Input.TextArea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        onBlur={handlePromptBlur}
        placeholder={placeholders[node.node_type]}
        autoSize={{ minRows: 2, maxRows: 5 }}
        className="canvas-run-panel__input"
      />
      <div className="canvas-run-panel__toolbar">
        <Select
          value={modelCode}
          onChange={handleModelChange}
          options={models.map((m) => ({ value: m.model_code, label: m.model_name }))}
          placeholder="选择模型"
          style={{ minWidth: 180 }}
          size="small"
        />
        <div className="canvas-run-panel__actions">
          <Button
            type="primary"
            shape="circle"
            icon={<ArrowUpOutlined />}
            loading={running || node.status === 'running'}
            onClick={handleRun}
            className="canvas-run-panel__submit"
          />
        </div>
      </div>
    </div>
  )
}
