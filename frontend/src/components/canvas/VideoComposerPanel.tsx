import { useEffect, useMemo, useRef, useState } from 'react'
import { Button, Input, Popover, Segmented, Slider } from 'antd'
import { ArrowUpOutlined, DownOutlined, RobotOutlined, CheckOutlined } from '@ant-design/icons'
import { getModels } from '@/api'
import type { ModelItem } from '@/types'
import type { CanvasNodeConfig } from '@/types/canvas'
import type { CanvasUpstreamPreview } from '@/utils/canvasUpstream'
import type { AspectRatioKey } from '@/constants/imageSizeSpec'
import NodeReferenceStrip from './NodeReferenceStrip'
import { canvasPopoverProps } from './canvasPopover'

const { TextArea } = Input

type VideoQuality = '480p' | '720p'

interface VideoPanelState {
  prompt: string
  ratio: AspectRatioKey | 'auto'
  duration: number
  quality: VideoQuality
  audio: boolean
}

const RATIO_OPTIONS: { key: AspectRatioKey | 'auto'; label: string; w?: number; h?: number }[] = [
  { key: 'auto', label: '智能' },
  { key: '16:9', label: '16:9', w: 16, h: 9 },
  { key: '4:3', label: '4:3', w: 4, h: 3 },
  { key: '1:1', label: '1:1', w: 1, h: 1 },
  { key: '3:4', label: '3:4', w: 3, h: 4 },
  { key: '9:16', label: '9:16', w: 9, h: 16 },
  { key: '21:9', label: '21:9', w: 21, h: 9 },
]

function defaultState(): VideoPanelState {
  return {
    prompt: '',
    ratio: 'auto',
    duration: 5,
    quality: '720p',
    audio: false,
  }
}

function stateFromConfig(config: CanvasNodeConfig): VideoPanelState {
  const params = config.params || {}
  const state = defaultState()
  state.prompt = config.prompt || ''
  if (params.ratio === 'auto' || typeof params.ratio === 'string') {
    state.ratio = (params.ratio as AspectRatioKey | 'auto') || 'auto'
  }
  if (typeof params.duration === 'number') state.duration = params.duration
  if (params.video_quality === '480p' || params.video_quality === '720p') {
    state.quality = params.video_quality
  }
  if (typeof params.audio === 'boolean') state.audio = params.audio
  return state
}

function buildPersistParams(state: VideoPanelState): Record<string, unknown> {
  return {
    ratio: state.ratio !== 'auto' ? state.ratio : '16:9',
    duration: state.duration,
    video_quality: state.quality,
    audio: state.audio,
  }
}

const RatioIcon = ({ w, h }: { w: number; h: number }) => {
  const box = 28
  const padding = 3
  let iw: number
  let ih: number
  if (w >= h) {
    iw = box - padding * 2
    ih = Math.round((iw * h) / w)
  } else {
    ih = box - padding * 2
    iw = Math.round((ih * w) / h)
  }
  iw = Math.max(iw, 6)
  ih = Math.max(ih, 6)
  return (
    <div className="canvas-ratio-icon">
      <div className="canvas-ratio-icon__inner" style={{ width: iw, height: ih }} />
    </div>
  )
}

interface VideoComposerPanelProps {
  nodeId: string
  configRevision?: string
  config: CanvasNodeConfig
  running?: boolean
  upstream: CanvasUpstreamPreview
  onRun: (config: CanvasNodeConfig) => void
  onUpdateConfig: (patch: Partial<CanvasNodeConfig>) => void
}

export default function VideoComposerPanel({
  nodeId,
  configRevision,
  config,
  running,
  upstream,
  onRun,
  onUpdateConfig,
}: VideoComposerPanelProps) {
  const persistTimerRef = useRef<number | null>(null)
  const [models, setModels] = useState<ModelItem[]>([])
  const [modelCode, setModelCode] = useState(config.model_code)
  const [state, setState] = useState<VideoPanelState>(() => defaultState())
  const [configOpen, setConfigOpen] = useState(false)

  useEffect(() => {
    getModels('video').then((res) => {
      if (res.code === 'success' && res.data?.length) {
        setModels(res.data)
        const def =
          res.data.find((m) => m.model_code === config.model_code) ||
          res.data.find((m) => m.is_default) ||
          res.data[0]
        if (def && !modelCode) setModelCode(def.model_code)
      }
    })
  }, [])

  useEffect(() => {
    setModelCode(config.model_code)
    setState(stateFromConfig(config))
  }, [nodeId, configRevision, config.model_code, config.prompt])

  const currentModel = models.find((m) => m.model_code === modelCode) || models[0]

  const schedulePersist = (next: VideoPanelState, code = modelCode) => {
    if (persistTimerRef.current) window.clearTimeout(persistTimerRef.current)
    persistTimerRef.current = window.setTimeout(() => {
      onUpdateConfig({
        prompt: next.prompt,
        model_code: code,
        params: buildPersistParams(next),
      })
    }, 400)
  }

  useEffect(
    () => () => {
      if (persistTimerRef.current) window.clearTimeout(persistTimerRef.current)
    },
    [],
  )

  const patchState = (patch: Partial<VideoPanelState>) => {
    setState((prev) => {
      const next = { ...prev, ...patch }
      schedulePersist(next)
      return next
    })
  }

  const configSummary = useMemo(() => {
    const ratioLabel = state.ratio === 'auto' ? '智能' : state.ratio
    const audioLabel = state.audio ? '有配音' : '无配音'
    return `${ratioLabel} | ${state.quality} | ${state.duration}s | ${audioLabel}`
  }, [state.ratio, state.quality, state.duration, state.audio])

  const handleSubmit = () => {
    if (!modelCode) return
    onRun({
      ...config,
      prompt: state.prompt.trim(),
      model_code: modelCode,
      params: buildPersistParams(state),
    })
  }

  const modelPanel = (
    <div className="canvas-model-panel">
      {models.map((m) => (
        <div
          key={m.model_code}
          className={`canvas-model-panel__item ${modelCode === m.model_code ? 'canvas-model-panel__item--active' : ''}`}
          onClick={() => {
            setModelCode(m.model_code)
            schedulePersist(state, m.model_code)
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

  const videoConfigPanel = (
    <div className="canvas-video-config">
      <div className="canvas-video-config__section">
        <div className="canvas-video-config__title">视频比例</div>
        <div className="canvas-video-config__ratio-grid">
          {RATIO_OPTIONS.map((opt) => (
            <button
              key={opt.key}
              type="button"
              className={`canvas-video-config__ratio ${state.ratio === opt.key ? 'canvas-video-config__ratio--active' : ''}`}
              onClick={() => patchState({ ratio: opt.key })}
            >
              {opt.key === 'auto' ? (
                <span className="canvas-video-config__auto">智</span>
              ) : (
                <RatioIcon w={opt.w!} h={opt.h!} />
              )}
              <span>{opt.label}</span>
            </button>
          ))}
        </div>
      </div>
      <div className="canvas-video-config__section">
        <div className="canvas-video-config__title">视频质量</div>
        <Segmented
          block
          size="small"
          value={state.quality}
          onChange={(v) => patchState({ quality: v as VideoQuality })}
          options={[
            { label: '480P', value: '480p' },
            { label: '720P', value: '720p' },
          ]}
        />
      </div>
      <div className="canvas-video-config__section">
        <div className="canvas-video-config__title">视频时长：{state.duration} 秒</div>
        <Slider
          min={1}
          max={15}
          step={1}
          value={state.duration}
          onChange={(v) => patchState({ duration: v })}
        />
      </div>
      <div className="canvas-video-config__section">
        <div className="canvas-video-config__title">同时生成声音</div>
        <Segmented
          block
          size="small"
          value={state.audio}
          onChange={(v) => patchState({ audio: v as boolean })}
          options={[
            { label: '无配音', value: false },
            { label: '有配音', value: true },
          ]}
        />
      </div>
    </div>
  )

  return (
    <div className="canvas-video-composer">
      <NodeReferenceStrip upstream={upstream} variant="panel" />

      <TextArea
        value={state.prompt}
        onChange={(e) => patchState({ prompt: e.target.value })}
        placeholder="描述你想要生成的视频内容…"
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
          <Popover
            {...canvasPopoverProps}
            content={videoConfigPanel}
            title="视频配置"
            trigger="click"
            placement="topLeft"
            open={configOpen}
            onOpenChange={setConfigOpen}
          >
            <button type="button" className="canvas-text-composer__pill canvas-text-composer__pill--ghost">
              <span>{configSummary}</span>
              <DownOutlined />
            </button>
          </Popover>
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
