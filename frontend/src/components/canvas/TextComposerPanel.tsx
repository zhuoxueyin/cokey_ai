import { useEffect, useState } from 'react'
import { Button, Input, Popover, Select } from 'antd'
import { ArrowUpOutlined, DownOutlined, RobotOutlined, CheckOutlined, BulbOutlined } from '@ant-design/icons'
import { getModels } from '@/api'
import { getPublishedPrompts } from '@/api/prompt'
import type { ModelItem, PromptItem } from '@/types'
import type { CanvasNodeConfig } from '@/types/canvas'
import { canvasPopoverProps } from './canvasPopover'

const { TextArea } = Input

interface TextComposerPanelProps {
  config: CanvasNodeConfig
  running?: boolean
  onRun: (config: CanvasNodeConfig) => void
  onUpdateConfig: (patch: Partial<CanvasNodeConfig>) => void
}

export default function TextComposerPanel({ config, running, onRun, onUpdateConfig }: TextComposerPanelProps) {
  const [models, setModels] = useState<ModelItem[]>([])
  const [promptList, setPromptList] = useState<PromptItem[]>([])
  const [prompt, setPrompt] = useState(config.prompt || '')
  const [modelCode, setModelCode] = useState(config.model_code)
  const [presetOpen, setPresetOpen] = useState(false)

  useEffect(() => {
    getModels('text').then((res) => {
      if (res.code === 'success' && res.data?.length) {
        setModels(res.data)
        if (!modelCode) {
          const def = res.data.find((m) => m.is_default) || res.data[0]
          setModelCode(def.model_code)
          onUpdateConfig({ model_code: def.model_code })
        }
      }
    })
    getPublishedPrompts().then((res) => {
      if (res.code === 'success' && res.data) {
        setPromptList(res.data.filter((p) => p.category === 'text'))
      }
    })
  }, [])

  useEffect(() => {
    setPrompt(config.prompt || '')
    setModelCode(config.model_code)
  }, [config.prompt, config.model_code])

  const currentModel = models.find((m) => m.model_code === modelCode)

  const modelPanel = (
    <div className="canvas-model-panel">
      {models.map((m) => (
        <div
          key={m.model_code}
          className={`canvas-model-panel__item ${modelCode === m.model_code ? 'canvas-model-panel__item--active' : ''}`}
          onClick={() => {
            setModelCode(m.model_code)
            onUpdateConfig({ model_code: m.model_code })
          }}
        >
          <RobotOutlined />
          <span>{m.model_name}</span>
          {modelCode === m.model_code && <CheckOutlined />}
        </div>
      ))}
    </div>
  )

  const presetPanel = (
    <div className="canvas-model-panel">
      {promptList.length === 0 ? (
        <div className="canvas-model-panel__empty">暂无常用提示词</div>
      ) : (
        promptList.map((p) => (
          <div
            key={p._id}
            className="canvas-model-panel__item"
            onClick={() => {
              setPrompt(p.content)
              onUpdateConfig({ prompt: p.content })
              setPresetOpen(false)
            }}
          >
            <span>{p.name}</span>
          </div>
        ))
      )}
    </div>
  )

  const handleSubmit = () => {
    onRun({ ...config, prompt, model_code: modelCode, text_mode: 'generate' })
  }

  return (
    <div className="canvas-text-composer canvas-text-composer--generate">
      <TextArea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        onBlur={() => onUpdateConfig({ prompt })}
        placeholder="请描述你的需求，用AI生成文案"
        autoSize={{ minRows: 1, maxRows: 4 }}
        className="canvas-run-panel__input canvas-run-panel__input--large"
      />
      <div className="canvas-text-composer__footer canvas-composer-footer--single-row">
        <div className="canvas-text-composer__footer-left">
          <Popover {...canvasPopoverProps} content={modelPanel} title="选择模型" trigger="click" placement="topLeft">
            <button type="button" className="canvas-text-composer__pill">
              <span>{currentModel?.model_name || '选择模型'}</span>
              <DownOutlined />
            </button>
          </Popover>
          {promptList.length > 0 && (
            <Popover
              {...canvasPopoverProps}
              content={presetPanel}
              title="常用提示词"
              trigger="click"
              placement="topLeft"
              open={presetOpen}
              onOpenChange={setPresetOpen}
            >
              <button type="button" className="canvas-text-composer__pill canvas-text-composer__pill--ghost">
                <BulbOutlined />
                <span>常用提示词</span>
              </button>
            </Popover>
          )}
        </div>
        <Button
          type="primary"
          shape="circle"
          icon={<ArrowUpOutlined />}
          loading={running}
          onClick={handleSubmit}
          className="canvas-text-composer__submit-circle"
        />
      </div>
    </div>
  )
}
