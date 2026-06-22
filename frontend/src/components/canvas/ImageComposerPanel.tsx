import { useEffect, useRef, useMemo, useState } from 'react'
import { Button, Popover, Segmented, message } from 'antd'
import {
  ArrowUpOutlined,
  BulbOutlined,
  CheckOutlined,
  DownOutlined,
  RobotOutlined,
} from '@ant-design/icons'
import { getModels } from '@/api'
import { getPublishedPrompts } from '@/api/prompt'
import type { ModelItem, PromptItem } from '@/types'
import type { CanvasNodeConfig } from '@/types/canvas'
import type { CanvasUpstreamPreview } from '@/utils/canvasUpstream'
import UpstreamInputChips from './UpstreamInputChips'
import CanvasPromptInput from './CanvasPromptInput'
import CanvasStylePicker from './CanvasStylePicker'
import { hasPromptContent } from '@/utils/canvasPromptMention'
import {
  type AspectRatioKey,
  type ImageClarity,
  buildImageSizeParams,
  clampSizeSelection,
  CLARITY_HINTS,
  CLARITY_LABELS,
  findPresetBySize,
  getClaritiesForRatio,
  getRatiosForClarity,
  resolveImageSizeSpec,
  resolveOfficialSize,
  toRatioOptions,
} from '@/constants/imageSizeSpec'
import { canvasPopoverProps } from './canvasPopover'
import { useCanvasModelCode } from './useCanvasModelCode'

type ImageQuality = 'auto' | 'low' | 'medium' | 'high'
type ImageBackground = 'auto' | 'transparent' | 'opaque'

interface ImagePanelState {
  prompt: string
  ratio: AspectRatioKey | 'auto'
  clarity: ImageClarity
  quality: ImageQuality
  background: ImageBackground
  count: 1 | 2 | 3 | 4
  stylePresetId?: string
  stylePresetName?: string
}

const defaultPanelState = (): ImagePanelState => ({
  prompt: '',
  ratio: '1:1',
  clarity: '1k',
  quality: 'auto',
  background: 'auto',
  count: 1,
})

function stateFromConfig(config: CanvasNodeConfig, model?: ModelItem | null): ImagePanelState {
  const params = config.params || {}
  const state = defaultPanelState()
  state.prompt = config.prompt || ''

  if (params.size && typeof params.size === 'string') {
    const spec = resolveImageSizeSpec(model)
    const found = findPresetBySize(spec, params.size)
    if (found) {
      state.ratio = found.aspectRatio
      state.clarity = found.clarity
    }
  }
  if (params.resolution === '1k' || params.resolution === '2k' || params.resolution === '4k') {
    state.clarity = params.resolution
  }
  if (params.aspect_ratio && typeof params.aspect_ratio === 'string') {
    state.ratio = params.aspect_ratio as AspectRatioKey
  }
  if (params.quality === 'low' || params.quality === 'medium' || params.quality === 'high') {
    state.quality = params.quality
  }
  if (params.background === 'transparent' || params.background === 'opaque') {
    state.background = params.background
  }
  if (typeof params.n === 'number' && params.n >= 1 && params.n <= 4) {
    state.count = params.n as 1 | 2 | 3 | 4
  }
  state.stylePresetId = config.style_preset_id
  state.stylePresetName = config.style_preset_name

  return state
}

function buildPersistParams(state: ImagePanelState, model: ModelItem): Record<string, unknown> {
  const spec = resolveImageSizeSpec(model)
  const { ratio, clarity } = clampSizeSelection(
    spec,
    state.ratio === 'auto' ? '1:1' : state.ratio,
    state.clarity,
  )
  const params: Record<string, unknown> = {
    ...buildImageSizeParams(spec, ratio, clarity),
    n: state.count,
  }
  if (state.quality !== 'auto') params.quality = state.quality
  if (state.background !== 'auto') params.background = state.background
  return params
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

interface ImageComposerPanelProps {
  nodeId: string
  configRevision?: string
  config: CanvasNodeConfig
  running?: boolean
  upstream: CanvasUpstreamPreview
  onRun: (config: CanvasNodeConfig) => void
  onUpdateConfig: (patch: Partial<CanvasNodeConfig>) => void
}

export default function ImageComposerPanel({
  nodeId,
  configRevision,
  config,
  running,
  upstream,
  onRun,
  onUpdateConfig,
}: ImageComposerPanelProps) {
  const persistTimerRef = useRef<number | null>(null)
  const stateRef = useRef<ImagePanelState>(defaultPanelState())
  const outputImageIndexRef = useRef(config.output_image_index)
  outputImageIndexRef.current = config.output_image_index
  const [models, setModels] = useState<ModelItem[]>([])
  const [promptList, setPromptList] = useState<PromptItem[]>([])
  const { modelCode, setModelCode, modelCodeRef } = useCanvasModelCode(
    config.model_code,
    nodeId,
    configRevision,
  )
  const currentModelRef = useRef<ModelItem | undefined>(undefined)
  const [state, setState] = useState<ImagePanelState>(() => defaultPanelState())
  const [presetOpen, setPresetOpen] = useState(false)
  const [configOpen, setConfigOpen] = useState(false)

  const currentModel = models.find((m) => m.model_code === modelCode) || models[0]
  currentModelRef.current = currentModel
  const imageSizeSpec = resolveImageSizeSpec(currentModel)

  useEffect(() => {
    getModels('image').then((res) => {
      if (res.code === 'success' && res.data?.length) {
        setModels(res.data)
        const def =
          res.data.find((m) => m.model_code === config.model_code) ||
          res.data.find((m) => m.model_code === modelCodeRef.current) ||
          res.data.find((m) => m.is_default) ||
          res.data[0]
        if (def && !modelCodeRef.current) {
          setModelCode(def.model_code)
        }
      }
    })
    getPublishedPrompts().then((res) => {
      if (res.code === 'success' && res.data) {
        setPromptList(res.data.filter((p) => p.category === 'image'))
      }
    })
  }, [])

  useEffect(() => {
    const next = stateFromConfig(config, currentModelRef.current)
    const local = stateRef.current
    if (local.stylePresetId && !next.stylePresetId) {
      next.stylePresetId = local.stylePresetId
      next.stylePresetName = local.stylePresetName
    }
    setState(next)
    stateRef.current = next
  }, [nodeId, configRevision, config.style_preset_id, config.style_preset_name, config.prompt])

  const buildConfigFromState = (next: ImagePanelState, code?: string): Partial<CanvasNodeConfig> => {
    const resolvedCode = code ?? modelCodeRef.current
    const model = models.find((m) => m.model_code === resolvedCode) || currentModelRef.current
    const patch: Partial<CanvasNodeConfig> = {
      prompt: next.prompt,
      model_code: resolvedCode,
      output_image_index: outputImageIndexRef.current,
    }
    if (next.stylePresetId) {
      patch.style_preset_id = next.stylePresetId
      if (next.stylePresetName) patch.style_preset_name = next.stylePresetName
    }
    if (model) {
      patch.params = buildPersistParams(next, model)
    }
    return patch
  }

  const persistNow = (next: ImagePanelState, code?: string) => {
    void onUpdateConfig(buildConfigFromState(next, code))
  }

  const schedulePersist = (next: ImagePanelState, code?: string) => {
    stateRef.current = next
    if (persistTimerRef.current) window.clearTimeout(persistTimerRef.current)
    persistTimerRef.current = window.setTimeout(() => {
      persistNow(next, code)
    }, 400)
  }

  useEffect(
    () => () => {
      if (persistTimerRef.current) {
        window.clearTimeout(persistTimerRef.current)
      }
      persistNow(stateRef.current, modelCodeRef.current)
    },
    [],
  )

  useEffect(() => {
    if (!currentModel) return
    const local = stateRef.current
    if (local.stylePresetId && !config.style_preset_id) {
      void onUpdateConfig({
        style_preset_id: local.stylePresetId,
        style_preset_name: local.stylePresetName,
      })
    }
  }, [currentModel?.model_code, config.style_preset_id])

  useEffect(() => {
    if (!currentModel) return
    setState((prev) => {
      const { ratio, clarity } = clampSizeSelection(
        imageSizeSpec,
        prev.ratio === 'auto' ? '1:1' : prev.ratio,
        prev.clarity,
      )
      if (ratio === prev.ratio && clarity === prev.clarity) return prev
      return { ...prev, ratio, clarity }
    })
  }, [currentModel?.model_code, imageSizeSpec.specId])

  const patchState = (patch: Partial<ImagePanelState> | ((prev: ImagePanelState) => Partial<ImagePanelState>)) => {
    setState((prev) => {
      const patchVal = typeof patch === 'function' ? patch(prev) : patch
      const next = { ...prev, ...patchVal }
      schedulePersist(next)
      return next
    })
  }

  const handleStyleChange = (styleId?: string, styleName?: string) => {
    if (persistTimerRef.current) window.clearTimeout(persistTimerRef.current)
    setState((prev) => {
      const next = { ...prev, stylePresetId: styleId, stylePresetName: styleName }
      stateRef.current = next
      if (styleId) {
        void onUpdateConfig({ style_preset_id: styleId, style_preset_name: styleName })
      } else {
        void onUpdateConfig({ style_preset_id: null, style_preset_name: null })
      }
      return next
    })
  }

  const activeRatioKey: AspectRatioKey =
    state.ratio === 'auto' ? toRatioOptions(imageSizeSpec, state.clarity)[0]?.key ?? '1:1' : state.ratio
  const ratioOptions = toRatioOptions(imageSizeSpec, state.clarity)
  const clarityOptions = getClaritiesForRatio(imageSizeSpec, activeRatioKey)
  const currentSize = resolveOfficialSize(imageSizeSpec, activeRatioKey, state.clarity).size

  const configSummary = useMemo(() => {
    const q =
      state.quality === 'auto'
        ? '自动'
        : state.quality === 'low'
          ? '低'
          : state.quality === 'medium'
            ? '中'
            : '高'
    return `${currentSize} | ${q} | ${state.count}张`
  }, [currentSize, state.quality, state.count])

  const handleSubmit = () => {
    if (!modelCode || !currentModel) {
      message.warning('请先选择模型')
      return
    }
    if (!hasPromptContent(state.prompt, upstream.images.length > 0) && !state.stylePresetId) {
      message.warning('请输入描述、@ 引用上游、连接参考图或选择风格')
      return
    }
    onRun({
      ...config,
      prompt: state.prompt.trim(),
      model_code: modelCode,
      params: buildPersistParams(state, currentModel),
      style_preset_id: state.stylePresetId,
      style_preset_name: state.stylePresetName,
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
            setState((prev) => {
              schedulePersist(prev, m.model_code)
              return prev
            })
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
              patchState({ prompt: p.content })
              setPresetOpen(false)
            }}
          >
            <span>{p.name}</span>
          </div>
        ))
      )}
    </div>
  )

  const imageConfigPanel = (
    <div className="canvas-image-config">
      <div className="canvas-image-config__hint">{imageSizeSpec.label} 官方尺寸</div>
      <div className="canvas-image-config__section">
        <div className="canvas-image-config__title">
          清晰度 <span>{currentSize}</span>
        </div>
        <Segmented
          block
          size="small"
          value={state.clarity}
          onChange={(v) => {
            const clarity = v as ImageClarity
            const ratios = getRatiosForClarity(imageSizeSpec, clarity)
            const nextRatio = ratios.includes(state.ratio as AspectRatioKey) ? state.ratio : ratios[0]
            patchState({ clarity, ratio: nextRatio as AspectRatioKey })
          }}
          options={clarityOptions.map((c) => ({
            label: `${CLARITY_LABELS[c]}`,
            value: c,
          }))}
        />
        <div className="canvas-image-config__subhint">{CLARITY_HINTS[state.clarity]}</div>
      </div>
      <div className="canvas-image-config__section">
        <div className="canvas-image-config__title">图片比例</div>
        <div className="canvas-image-config__ratio-grid">
          {ratioOptions.map((opt) => (
            <button
              key={opt.key}
              type="button"
              className={`canvas-image-config__ratio ${state.ratio === opt.key ? 'canvas-image-config__ratio--active' : ''}`}
              onClick={() => {
                const clarities = getClaritiesForRatio(imageSizeSpec, opt.key)
                const nextClarity = clarities.includes(state.clarity) ? state.clarity : clarities[0]
                patchState({ ratio: opt.key, clarity: nextClarity })
              }}
            >
              <RatioIcon w={opt.w} h={opt.h} />
              <span>{opt.label}</span>
            </button>
          ))}
        </div>
      </div>
      <div className="canvas-image-config__section">
        <div className="canvas-image-config__title">图像质量</div>
        <Segmented
          block
          size="small"
          value={state.quality}
          onChange={(v) => patchState({ quality: v as ImageQuality })}
          options={[
            { label: '自动', value: 'auto' },
            { label: '低', value: 'low' },
            { label: '标准', value: 'medium' },
            { label: '高', value: 'high' },
          ]}
        />
      </div>
      <div className="canvas-image-config__section">
        <div className="canvas-image-config__title">背景模式</div>
        <Segmented
          block
          size="small"
          value={state.background}
          onChange={(v) => patchState({ background: v as ImageBackground })}
          options={[
            { label: '自动', value: 'auto' },
            { label: '透明', value: 'transparent' },
            { label: '不透明', value: 'opaque' },
          ]}
        />
      </div>
      <div className="canvas-image-config__section">
        <div className="canvas-image-config__title">生成张数</div>
        <Segmented
          block
          size="small"
          value={state.count}
          onChange={(v) => patchState({ count: Number(v) as 1 | 2 | 3 | 4 })}
          options={[1, 2, 3, 4].map((n) => ({ label: `${n} 张`, value: n }))}
        />
      </div>
    </div>
  )

  return (
    <div className="canvas-image-composer">
      <UpstreamInputChips upstream={upstream} />

      <CanvasPromptInput
        value={state.prompt}
        onChange={(prompt) => patchState({ prompt })}
        refs={upstream.refs}
        placeholder="描述画面；输入 @ 引用上游文本或图片"
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
            content={imageConfigPanel}
            title="图片配置"
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
                <span>常用</span>
              </button>
            </Popover>
          )}
          <CanvasStylePicker
            stylePresetId={state.stylePresetId}
            stylePresetName={state.stylePresetName}
            onChange={handleStyleChange}
          />
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
