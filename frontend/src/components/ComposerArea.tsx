import { useState, useEffect, useRef, useMemo } from 'react'
import { Card, Button, Input, message, Upload, Modal, Tabs, Empty, Image, Tag, Popover, Segmented, Slider, Select } from 'antd'
import {
  ThunderboltOutlined,
  PictureOutlined,
  VideoCameraOutlined,
  RobotOutlined,
  SettingOutlined,
  CheckOutlined,
  CloseOutlined,
  AudioOutlined,
  UploadOutlined,
  PlusOutlined,
  DownOutlined,
  CheckSquareOutlined,
  HistoryOutlined,
  CloudOutlined,
  FileTextOutlined,
} from '@ant-design/icons'
import { useGenerationStore } from '@/store/generation'
import { generate, uploadAsset, listAssets } from '@/api'
import { listPrompts, getPublishedPrompts } from '@/api/prompt'
import type { AssetItem, ModelItem, PromptItem } from '@/types'
import {
  type ImageRef,
  extractCdnUrls,
  isAssetCdnReady,
  normalizeImageRef,
  pickCdnUrl,
} from '@/utils/cdnUrl'

const { TextArea } = Input
const { Dragger } = Upload

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

const RatioIcon = ({ w, h }: { w: number; h: number }) => {
  const box = 32
  const padding = 4
  let iw: number
  let ih: number
  if (w >= h) {
    iw = box - padding * 2
    ih = Math.round((iw * h) / w)
  } else {
    ih = box - padding * 2
    iw = Math.round((ih * w) / h)
  }
  iw = Math.max(iw, 8)
  ih = Math.max(ih, 8)
  return (
    <div
      style={{
        width: box,
        height: box,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <div
        style={{
          width: iw,
          height: ih,
          borderRadius: 3,
          border: '1.5px solid #999',
        }}
      />
    </div>
  )
}

// ==================== 类型特定状态接口 ====================
interface CategoryState {
  prompt: string
  ratio: AspectRatioKey | 'auto'
  clarity: ImageClarity
  quality: 'auto' | 'low' | 'medium' | 'high'
  background: 'auto' | 'transparent' | 'opaque'
  count: 1 | 2 | 3 | 4
  videoDuration: number
  videoQuality: '480p' | '720p'
  videoAudio: boolean
  uploadImages: ImageRef[]
  uploadVideos: { url: string; file_name?: string }[]
  uploadAudios: { url: string; file_name?: string }[]
}

const createDefaultState = (): CategoryState => ({
  prompt: '',
  ratio: 'auto',
  clarity: '1k',
  quality: 'auto',
  background: 'auto',
  count: 1,
  videoDuration: 5,
  videoQuality: '720p',
  videoAudio: false,
  uploadImages: [],
  uploadVideos: [],
  uploadAudios: [],
})

export default function ComposerArea() {
  const { activeCategory, currentModel } = useGenerationStore()
  const setParamsWithCategory = useGenerationStore((s) => (s as any).setParamsWithCategory)

  const imageSizeSpec = resolveImageSizeSpec(currentModel)

  // 需求2: 不同类型之间隔离数据
  const [categoryStates, setCategoryStates] = useState<Record<string, CategoryState>>({
    text: createDefaultState(),
    image: createDefaultState(),
    video: createDefaultState(),
  })

  // 当前激活分类的状态
  const currentState = categoryStates[activeCategory] || createDefaultState()

  const ratioOptionsForClarity = toRatioOptions(imageSizeSpec, currentState.clarity)
  const activeRatioKey: AspectRatioKey =
    currentState.ratio === 'auto'
      ? ratioOptionsForClarity[0]?.key ?? '1:1'
      : currentState.ratio
  const clarityOptionsForRatio = getClaritiesForRatio(imageSizeSpec, activeRatioKey)

  const videoConfigLabel = useMemo(() => {
    const ratioLabel = currentState.ratio === 'auto' ? '智能比例' : currentState.ratio
    const qualityLabel = currentState.videoQuality
    const durationLabel = `${currentState.videoDuration}s`
    const audioLabel = currentState.videoAudio ? '有配音' : '无配音'
    return `${ratioLabel} | ${qualityLabel} | ${durationLabel} | ${audioLabel}`
  }, [
    currentState.ratio,
    currentState.videoQuality,
    currentState.videoDuration,
    currentState.videoAudio,
  ])

  // 切换模型时，将比例/清晰度收敛到该模型官方支持项
  useEffect(() => {
    if (activeCategory !== 'image' || !currentModel) return
    const spec = resolveImageSizeSpec(currentModel)
    setCategoryStates((prev) => {
      const state = prev.image
      const { ratio, clarity } = clampSizeSelection(spec, state.ratio, state.clarity)
      if (ratio === state.ratio && clarity === state.clarity) return prev
      return { ...prev, image: { ...state, ratio, clarity } }
    })
  }, [currentModel?.model_code, activeCategory])

  const [pickerOpen, setPickerOpen] = useState(false)
  const [configOpen, setConfigOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  // 资源库相关
  const [assetList, setAssetList] = useState<AssetItem[]>([])
  const [assetLoading, setAssetLoading] = useState(false)
  const [selectedAssets, setSelectedAssets] = useState<Set<string>>(new Set())
  const [pickerActiveTab, setPickerActiveTab] = useState<'upload' | 'library'>('upload')
  const [pickerCategory, setPickerCategory] = useState<'image' | 'video' | 'audio'>('image')

  // 提示词相关
  const [promptList, setPromptList] = useState<PromptItem[]>([])
  const [promptLoading, setPromptLoading] = useState(false)

  const availableModels = (useGenerationStore((s) => (s as any).availableModels) as ModelItem[]) || []

  // 用于追踪是否是"再次编辑"触发的参数回填
  const isRefillingRef = useRef(false)
  const lastParamsRef = useRef<string>('')

  // 需求1: 监听 store 中的 params 变化（用于"再次编辑"功能）
  const params = useGenerationStore((s) => (s as any).params)
  const paramsCategory = useGenerationStore((s) => s.activeCategory)
  
  useEffect(() => {
    const paramsStr = JSON.stringify(params)
    if (paramsStr === lastParamsRef.current) return
    lastParamsRef.current = paramsStr

    if (isRefillingRef.current) {
      isRefillingRef.current = false
      return
    }

    if (params && Object.keys(params).length > 0) {
      // 需求1: 自动切换到对应的分类
      const targetCategory = paramsCategory as 'text' | 'image' | 'video'
      
      setCategoryStates((prev) => {
        const newState = { ...prev }
        const state = { ...newState[targetCategory] || createDefaultState() }

        if (params.prompt !== undefined) {
          state.prompt = params.prompt
        }
        
        // 标记是否已从 size 解析出比例
        let ratioFromSize = false
        
        if (params.size !== undefined && params.size.includes('x')) {
          const spec = resolveImageSizeSpec(currentModel)
          const found = findPresetBySize(spec, params.size)
          if (found) {
            state.ratio = found.aspectRatio
            state.clarity = found.clarity
            ratioFromSize = true
          } else {
            const [w, h] = params.size.split('x').map(Number)
            if (w && h) {
              const gcd = (a: number, b: number): number => (b === 0 ? a : gcd(b, a % b))
              const divisor = gcd(w, h)
              const inferredRatio = `${Math.round(w / divisor)}:${Math.round(h / divisor)}` as AspectRatioKey
              const ratios = toRatioOptions(spec)
              if (ratios.some((r) => r.key === inferredRatio)) {
                state.ratio = inferredRatio
                const clarities = getClaritiesForRatio(spec, inferredRatio)
                state.clarity = clarities[0] || '1k'
                ratioFromSize = true
              }
            }
          }
        }
        if (params.aspect_ratio && !ratioFromSize) {
          const ar = params.aspect_ratio as AspectRatioKey
          if (toRatioOptions(imageSizeSpec).some((r) => r.key === ar)) {
            state.ratio = ar
            ratioFromSize = true
          }
        }
        if (params.resolution && ['1k', '2k', '4k'].includes(params.resolution)) {
          state.clarity = params.resolution as ImageClarity
        }
        if (params.quality !== undefined) {
          const q = params.quality as 'auto' | 'low' | 'medium' | 'high'
          if (['auto', 'low', 'medium', 'high'].includes(q)) {
            state.quality = q
          }
        }
        if (params.background !== undefined) {
          const bg = params.background as 'auto' | 'transparent' | 'opaque'
          if (['auto', 'transparent', 'opaque'].includes(bg)) {
            state.background = bg
          }
        }
        if (params.n !== undefined) {
          state.count = Math.min(4, Math.max(1, Number(params.n))) as 1 | 2 | 3 | 4
        }
        if (params.images !== undefined && Array.isArray(params.images)) {
          state.uploadImages = params.images
            .map((img: any) => normalizeImageRef(img))
            .filter((ref): ref is ImageRef => ref !== null)
        }
        if (params.videos !== undefined && Array.isArray(params.videos)) {
          state.uploadVideos = params.videos.map((video: any) => ({ 
            url: typeof video === 'string' ? video : (video.url || ''), 
            file_name: typeof video === 'object' ? video.file_name : undefined 
          }))
        }
        if (params.audios !== undefined && Array.isArray(params.audios)) {
          state.uploadAudios = params.audios.map((audio: any) => ({ 
            url: typeof audio === 'string' ? audio : (audio.url || ''), 
            file_name: typeof audio === 'object' ? audio.file_name : undefined 
          }))
        }
        // 只有在没有从 size 解析出比例的情况下，才使用 params.ratio
        if (params.ratio !== undefined && !ratioFromSize) {
          state.ratio = params.ratio as AspectRatioKey | 'auto'
        }
        if (params.duration !== undefined) {
          state.videoDuration = Number(params.duration)
        }
        if (params.video_quality !== undefined) {
          state.videoQuality = params.video_quality as '480p' | '720p'
        }
        if (params.audio !== undefined) {
          state.videoAudio = params.audio
        }

        newState[targetCategory] = state
        return newState
      })
    }
  }, [params, paramsCategory])

  // 更新当前分类的状态
  const updateCurrentState = (updates: Partial<CategoryState>) => {
    setCategoryStates((prev) => ({
      ...prev,
      [activeCategory]: { ...prev[activeCategory], ...updates },
    }))
  }

  const handleLoadAssets = async (category: 'image' | 'video' | 'audio') => {
    setAssetLoading(true)
    try {
      const res = await listAssets({ page: 1, page_size: 48, category })
      if (res.code === 'success' && res.data) {
        setAssetList(res.data.items || [])
      }
    } catch (e) {
      console.error(e)
    } finally {
      setAssetLoading(false)
    }
  }

  // 加载提示词列表（只加载已发布的）
  const handleLoadPrompts = async () => {
    setPromptLoading(true)
    try {
      const res = await getPublishedPrompts()
      if (res.code === 'success' && res.data) {
        setPromptList(res.data || [])
      }
    } catch (e) {
      console.error(e)
    } finally {
      setPromptLoading(false)
    }
  }

  // 选择提示词
  const handleSelectPrompt = (prompt: PromptItem) => {
    updateCurrentState({ prompt: prompt.content })
    message.success(`已应用提示词: ${prompt.name}`)
  }

  // 需求1: 打开选择器时自动选择对应类型
  const openPicker = (defaultTab?: 'image' | 'video' | 'audio') => {
    const targetType = defaultTab || (activeCategory === 'video' ? 'image' : 'image')
    setPickerCategory(targetType)
    setSelectedAssets(new Set())
    setPickerActiveTab('upload')
    handleLoadAssets(targetType)
    setPickerOpen(true)
  }

  const handleFileUpload = async (file: File, type: 'image' | 'video' | 'audio') => {
    try {
      const res = await uploadAsset(file, { category: type, source_type: 'upload' })
      if (res.code === 'success' && res.data) {
        const data = res.data as AssetItem
        if (type === 'image') {
          let cdnUrl: string
          try {
            cdnUrl = pickCdnUrl(data)
          } catch {
            message.error('上传成功但未获得有效 CDN 地址，请检查存储配置')
            return
          }
          updateCurrentState({
            uploadImages: [...currentState.uploadImages, { cdn_url: cdnUrl, file_name: data.file_name }],
          })
        } else if (type === 'video') {
          updateCurrentState({
            uploadVideos: [...currentState.uploadVideos, { url: data.url, file_name: data.file_name }],
          })
        } else if (type === 'audio') {
          updateCurrentState({
            uploadAudios: [...currentState.uploadAudios, { url: data.url, file_name: data.file_name }],
          })
        }
        message.success('上传成功')
      } else {
        message.error('上传失败')
      }
    } catch (e) {
      message.error('上传失败')
    }
    return false
  }

  const handleRemoveFile = (idx: number, type: 'image' | 'video' | 'audio') => {
    if (type === 'image') {
      updateCurrentState({
        uploadImages: currentState.uploadImages.filter((_, i) => i !== idx),
      })
    } else if (type === 'video') {
      updateCurrentState({
        uploadVideos: currentState.uploadVideos.filter((_, i) => i !== idx),
      })
    } else if (type === 'audio') {
      updateCurrentState({
        uploadAudios: currentState.uploadAudios.filter((_, i) => i !== idx),
      })
    }
  }

  const toggleAsset = (id: string) => {
    if (pickerCategory === 'image') {
      const asset = assetList.find((a) => a.id === id)
      if (asset && !isAssetCdnReady(asset)) {
        message.warning('该图片无法用于生图（非 CDN 地址，请重新上传）')
        return
      }
    }
    const next = new Set(selectedAssets)
    if (next.has(id)) next.delete(id)
    else next.add(id)
    setSelectedAssets(next)
  }

  const confirmPicker = () => {
    // 本地上传 Tab：文件已在 handleFileUpload 中写入 state，确定仅关闭弹窗
    if (pickerActiveTab === 'upload') {
      if (pickerCategory === 'image' && currentState.uploadImages.length === 0) {
        message.warning('请先上传图片')
        return
      }
      if (pickerCategory === 'video' && currentState.uploadVideos.length === 0) {
        message.warning('请先上传视频')
        return
      }
      if (pickerCategory === 'audio' && currentState.uploadAudios.length === 0) {
        message.warning('请先上传音频')
        return
      }
      setPickerOpen(false)
      setSelectedAssets(new Set())
      return
    }

    const selectedItems = assetList.filter((a) => selectedAssets.has(a.id))

    if (pickerCategory === 'image') {
      if (selectedItems.length === 0) {
        message.warning('请从资源库选择图片')
        return
      }
      const validItems: ImageRef[] = []
      const skipped: string[] = []
      for (const a of selectedItems) {
        if (!isAssetCdnReady(a)) {
          skipped.push(a.file_name || a.id)
          continue
        }
        try {
          validItems.push({ cdn_url: pickCdnUrl(a), file_name: a.file_name })
        } catch {
          skipped.push(a.file_name || a.id)
        }
      }
      if (validItems.length === 0) {
        message.error('所选图片均无法用于生图（旧版生成图含 Base64 数据，请重新上传或使用带 CDN 标记的图片）')
        return
      }
      if (skipped.length > 0) {
        message.warning(`已跳过 ${skipped.length} 张不可用图片（非 CDN 地址）`)
      }
      updateCurrentState({ uploadImages: [...currentState.uploadImages, ...validItems] })
      message.success(`已添加 ${validItems.length} 张图片`)
    } else if (pickerCategory === 'video') {
      if (selectedItems.length === 0) {
        message.warning('请从资源库选择视频')
        return
      }
      const newVideos = [
        ...currentState.uploadVideos,
        ...selectedItems.map((a) => ({ url: a.url, file_name: a.file_name })),
      ]
      updateCurrentState({ uploadVideos: newVideos })
      if (selectedAssets.size > 0) {
        message.success(`已添加 ${selectedAssets.size} 个视频`)
      }
    } else if (pickerCategory === 'audio') {
      if (selectedItems.length === 0) {
        message.warning('请从资源库选择音频')
        return
      }
      const newAudios = [
        ...currentState.uploadAudios,
        ...selectedItems.map((a) => ({ url: a.url, file_name: a.file_name })),
      ]
      updateCurrentState({ uploadAudios: newAudios })
      if (selectedAssets.size > 0) {
        message.success(`已添加 ${selectedAssets.size} 个音频`)
      }
    }
    setPickerOpen(false)
    setSelectedAssets(new Set())
  }

  const handleSelectCategory = (cat: 'image' | 'video' | 'text') => {
    const store = useGenerationStore.getState()
    store.setCategory(cat)
  }

  const handleSelectModel = (model: ModelItem) => {
    const store = useGenerationStore.getState()
    store.setModel(model)
  }

  const handleSubmit = async () => {
    if (!currentModel) {
      message.warning('请先选择模型')
      return
    }
    if (!currentState.prompt.trim() && activeCategory !== 'text') {
      message.warning('请输入描述内容')
      return
    }

    setSubmitting(true)

    const finalParams: Record<string, any> = { prompt: currentState.prompt.trim() }

    try {
      if (currentState.uploadImages.length > 0) {
        finalParams.images = extractCdnUrls(currentState.uploadImages)
      }
    } catch (e: any) {
      setSubmitting(false)
      message.error(e?.message || '参考图须为已上传的 CDN 地址')
      return
    }

    if (activeCategory === 'image') {
      const spec = resolveImageSizeSpec(currentModel)
      const { ratio, clarity } = clampSizeSelection(
        spec,
        currentState.ratio,
        currentState.clarity,
      )
      Object.assign(finalParams, buildImageSizeParams(spec, ratio, clarity))
      if (currentState.quality !== 'auto') finalParams.quality = currentState.quality
      if (currentState.background !== 'auto') finalParams.background = currentState.background
      finalParams.n = currentState.count
    } else if (activeCategory === 'video') {
      finalParams.ratio = currentState.ratio !== 'auto' ? currentState.ratio : '16:9'
      finalParams.duration = currentState.videoDuration
      finalParams.video_quality = currentState.videoQuality
      finalParams.audio = currentState.videoAudio
      finalParams.watermark = false
      if (currentState.uploadImages.length > 0) {
        finalParams.images = extractCdnUrls(currentState.uploadImages)
      }
      if (currentState.uploadVideos.length > 0) {
        finalParams.videos = currentState.uploadVideos
      }
      if (currentState.uploadAudios.length > 0) {
        finalParams.audios = currentState.uploadAudios
      }
    }

    const store = useGenerationStore.getState()

    const tempTaskId = `task_local_${Date.now()}`
    const tempTask: any = {
      id: tempTaskId,
      task_id: tempTaskId,
      session_id: store.sessionId,
      model_code: currentModel.model_code,
      category: activeCategory,
      status: 'processing',
      params: finalParams,
      params_summary: currentState.prompt.trim().substring(0, 60),
      created_at: new Date().toISOString(),
    }
    // 新任务添加到数组末尾，符合聊天对话习惯（最新的在底部）
    store.setTasks([...store.tasks, tempTask])

    try {
      const res = await generate({
        model_code: currentModel.model_code,
        category: activeCategory,
        session_id: store.sessionId ?? undefined,
        user_id: store.userId ?? undefined,
        params: finalParams,
      })

      if (res.code === 'success' && res.data) {
        const s = useGenerationStore.getState()
        // 更新 sessionId（如果还没有的话）
        if (!s.sessionId && (res.data as any).session_id) {
          s.setSessionId((res.data as any).session_id)
        }
        const updated = s.tasks.map((t: any) =>
          t.task_id === tempTaskId
            ? {
                ...t,
                task_id: (res.data as any).task_id || tempTaskId,
                session_id: (res.data as any).session_id || t.session_id,
                status: 'success',
                result: (res.data as any).result || {
                  type: (res.data as any).type,
                  images: (res.data as any).images,
                  text: (res.data as any).text,
                  videos: (res.data as any).videos,
                },
                duration_ms: (res.data as any).duration_ms,
              }
            : t,
        )
        s.setTasks(updated)
        updateCurrentState({ prompt: '' })
        message.success('生成成功')
      } else {
        const s = useGenerationStore.getState()
        const updated = s.tasks.map((t: any) =>
          t.task_id === tempTaskId ? { ...t, status: 'failed', error_message: res.message || '生成失败' } : t,
        )
        s.setTasks(updated)
        message.error(res.message || '生成失败')
      }
    } catch (e: any) {
      const s = useGenerationStore.getState()
      const updated = s.tasks.map((t: any) =>
        t.task_id === tempTaskId ? { ...t, status: 'failed', error_message: e.message || '生成失败' } : t,
      )
      s.setTasks(updated)
      message.error(e.message || '生成失败')
    } finally {
      setSubmitting(false)
    }
  }

  const iconMap: Record<string, any> = {
    image: <PictureOutlined />,
    video: <VideoCameraOutlined />,
    text: <SettingOutlined />,
  }
  const labelMap: Record<string, string> = {
    image: '图片生成',
    video: '视频生成',
    text: '文本生成',
  }

  const currentSizePreset =
    activeCategory === 'image'
      ? resolveOfficialSize(imageSizeSpec, activeRatioKey, currentState.clarity)
      : null
  const currentSize = currentSizePreset?.size ?? '—'

  const sizeButtonStyle = (selected: boolean): React.CSSProperties => ({
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
    height: 72,
    borderRadius: 10,
    background: selected ? '#e6f4ff' : '#fafafa',
    border: selected ? '1.5px solid #1677ff' : '1px solid #f0f0f0',
    color: selected ? '#1677ff' : '#333',
    fontSize: 12,
    cursor: 'pointer',
    padding: 4,
  })

  const modelPanel = (
    <div style={{ minWidth: 240 }}>
      {availableModels.length === 0 ? (
        <div style={{ padding: 16, fontSize: 13, color: '#999', textAlign: 'center' }}>暂无可用模型</div>
      ) : (
        availableModels.map((m) => (
          <div
            key={m.model_code}
            onClick={() => handleSelectModel(m)}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '8px 12px',
              cursor: 'pointer',
              borderRadius: 6,
              background: currentModel?.model_code === m.model_code ? '#e6f4ff' : 'transparent',
            }}
          >
            <div>
              <div style={{ fontSize: 13, fontWeight: 500 }}>{m.model_name}</div>
              <div style={{ fontSize: 11, color: '#999' }}>{m.description || m.model_code}</div>
            </div>
            {currentModel?.model_code === m.model_code && <CheckOutlined style={{ color: '#1677ff', fontSize: 12 }} />}
          </div>
        ))
      )}
    </div>
  )

  const imageConfigPanel = (
    <div style={{ width: 480, padding: 8 }}>
      <div style={{ fontSize: 11, color: '#999', marginBottom: 12 }}>
        {imageSizeSpec.label} 官方尺寸 · 仅显示当前模型支持的组合
      </div>
      {/* 尺寸比例 */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 8 }}>
          尺寸比例
          <span style={{ fontSize: 11, color: '#999', fontWeight: 400, marginLeft: 8 }}>
            {currentSize}
          </span>
        </div>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(5, 1fr)',
            gap: 8,
          }}
        >
          {ratioOptionsForClarity.map((opt) => {
            const selected = currentState.ratio === opt.key
            return (
              <div
                key={opt.key}
                onClick={() => {
                  const clarities = getClaritiesForRatio(imageSizeSpec, opt.key)
                  const nextClarity = clarities.includes(currentState.clarity)
                    ? currentState.clarity
                    : clarities[0]
                  updateCurrentState({ ratio: opt.key, clarity: nextClarity })
                }}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 4,
                  height: 60,
                  borderRadius: 8,
                  background: selected ? '#e6f4ff' : '#fafafa',
                  border: selected ? '1.5px solid #1677ff' : '1px solid #f0f0f0',
                  color: selected ? '#1677ff' : '#333',
                  fontSize: 11,
                  cursor: 'pointer',
                  padding: 4,
                }}
              >
                <RatioIcon w={opt.w} h={opt.h} />
                <span>{opt.label}</span>
              </div>
            )
          })}
        </div>
      </div>

      {/* 清晰度 */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 8 }}>清晰度</div>
        <Segmented
          block
          value={currentState.clarity}
          onChange={(v) => {
            const clarity = v as ImageClarity
            const ratios = getRatiosForClarity(imageSizeSpec, clarity)
            const nextRatio = ratios.includes(currentState.ratio as AspectRatioKey)
              ? currentState.ratio
              : ratios[0]
            updateCurrentState({ clarity, ratio: nextRatio as AspectRatioKey })
          }}
          options={clarityOptionsForRatio.map((c) => ({
            label: CLARITY_LABELS[c],
            value: c,
          }))}
        />
      </div>

      {/* 质量 */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 8 }}>质量</div>
        <Segmented
          block
          value={currentState.quality}
          onChange={(v) => updateCurrentState({ quality: v as 'auto' | 'low' | 'medium' | 'high' })}
          options={[
            { label: '自动', value: 'auto' },
            { label: '低', value: 'low' },
            { label: '中', value: 'medium' },
            { label: '高', value: 'high' },
          ]}
        />
      </div>

      {/* 张数 */}
      <div>
        <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 8 }}>生成张数</div>
        <Segmented
          block
          value={currentState.count}
          onChange={(v) => updateCurrentState({ count: v as 1 | 2 | 3 | 4 })}
          options={[
            { label: '1张', value: 1 },
            { label: '2张', value: 2 },
            { label: '3张', value: 3 },
            { label: '4张', value: 4 },
          ]}
        />
      </div>
    </div>
  )

  const configPanel = (
    <div style={{ width: 520, padding: 4 }}>
      {activeCategory === 'video' ? (
        <>
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 8 }}>视频比例</div>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(7, 1fr)',
                gap: 8,
              }}
            >
              {[
                { key: 'auto', label: '智能', icon: 'auto' },
                { key: '16:9', label: '16:9', w: 16, h: 9 },
                { key: '4:3', label: '4:3', w: 4, h: 3 },
                { key: '1:1', label: '1:1', w: 1, h: 1 },
                { key: '3:4', label: '3:4', w: 3, h: 4 },
                { key: '9:16', label: '9:16', w: 9, h: 16 },
                { key: '21:9', label: '21:9', w: 21, h: 9 },
              ].map((opt) => {
                const selected = currentState.ratio === opt.key
                return (
                  <div
                    key={opt.key}
                    onClick={() => updateCurrentState({ ratio: opt.key as AspectRatioKey | 'auto' })}
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: 4,
                      height: 64,
                      borderRadius: 8,
                      background: selected ? '#e6f4ff' : '#fafafa',
                      border: selected ? '1.5px solid #1677ff' : '1px solid #f0f0f0',
                      color: selected ? '#1677ff' : '#333',
                      fontSize: 11,
                      cursor: 'pointer',
                      padding: 4,
                    }}
                  >
                    {opt.key === 'auto' ? (
                      <div style={{ fontSize: 16 }}>智</div>
                    ) : (
                      <RatioIcon w={opt.w as number} h={opt.h as number} />
                    )}
                    <span>{opt.label}</span>
                  </div>
                )
              })}
            </div>
          </div>

          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 8 }}>视频质量</div>
            <Segmented
              block
              value={currentState.videoQuality}
              onChange={(v) => updateCurrentState({ videoQuality: v as '480p' | '720p' })}
              options={[
                { label: '480P', value: '480p' },
                { label: '720P', value: '720p' },
              ]}
            />
          </div>

          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 8 }}>
              视频时长：{currentState.videoDuration}秒
            </div>
            <Slider
              min={1}
              max={15}
              step={1}
              value={currentState.videoDuration}
              onChange={(v) => updateCurrentState({ videoDuration: v as number })}
              marks={{
                1: '1s',
                5: '5s',
                10: '10s',
                15: '15s',
              }}
            />
          </div>

          <div style={{ marginBottom: 8 }}>
            <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 8 }}>同时生成声音</div>
            <Segmented
              block
              value={currentState.videoAudio}
              onChange={(v) => updateCurrentState({ videoAudio: v as boolean })}
              options={[
                { label: '开启', value: true },
                { label: '关闭', value: false },
              ]}
            />
          </div>
        </>
      ) : activeCategory === 'image' ? (
        <>
          <div style={{ fontSize: 11, color: '#999', marginBottom: 12 }}>
            {imageSizeSpec.label} 官方尺寸
          </div>
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 8 }}>
              清晰度级别
              <span style={{ fontSize: 12, color: '#999', fontWeight: 400, marginLeft: 8 }}>
                当前 {currentSize}
              </span>
            </div>
            <Segmented
              block
              value={currentState.clarity}
              onChange={(v) => {
                const clarity = v as ImageClarity
                const ratios = getRatiosForClarity(imageSizeSpec, clarity)
                const nextRatio = ratios.includes(currentState.ratio as AspectRatioKey)
                  ? currentState.ratio
                  : ratios[0]
                updateCurrentState({ clarity, ratio: nextRatio as AspectRatioKey })
              }}
              options={clarityOptionsForRatio.map((c) => ({
                label: `${CLARITY_LABELS[c]}（${CLARITY_HINTS[c]}）`,
                value: c,
              }))}
            />
          </div>

          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 8 }}>图片比例</div>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(5, 1fr)',
                gap: 8,
              }}
            >
              {ratioOptionsForClarity.map((opt) => {
                const selected = currentState.ratio === opt.key
                return (
                  <div
                    key={opt.key}
                    onClick={() => {
                      const clarities = getClaritiesForRatio(imageSizeSpec, opt.key)
                      const nextClarity = clarities.includes(currentState.clarity)
                        ? currentState.clarity
                        : clarities[0]
                      updateCurrentState({ ratio: opt.key, clarity: nextClarity })
                    }}
                    style={sizeButtonStyle(selected)}
                  >
                    <RatioIcon w={opt.w} h={opt.h} />
                    <span>{opt.label}</span>
                  </div>
                )
              })}
            </div>
          </div>

          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 8 }}>图像质量</div>
            <Segmented
              block
              value={currentState.quality}
              onChange={(v) => updateCurrentState({ quality: v as any })}
              options={[
                { label: '自动', value: 'auto' },
                { label: '低', value: 'low' },
                { label: '标准', value: 'medium' },
                { label: '高', value: 'high' },
              ]}
            />
          </div>

          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 8 }}>背景模式</div>
            <Segmented
              block
              value={currentState.background}
              onChange={(v) => updateCurrentState({ background: v as any })}
              options={[
                { label: '自动', value: 'auto' },
                { label: '透明', value: 'transparent' },
                { label: '不透明', value: 'opaque' },
              ]}
            />
          </div>

          <div style={{ marginBottom: 8 }}>
            <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 8 }}>生成张数（最多 4 张）</div>
            <Segmented
              block
              value={currentState.count}
              onChange={(v) => updateCurrentState({ count: Number(v) as 1 | 2 | 3 | 4 })}
              options={[1, 2, 3, 4].map((n) => ({ label: `${n} 张`, value: n }))}
            />
          </div>
        </>
      ) : null}
    </div>
  )

  // 需求3: 素材选择组件优化 - 本地上传和从资源库选择并列两个tab
  const pickerModal = (
    <Modal
      title={`选择${pickerCategory === 'image' ? '图片' : pickerCategory === 'video' ? '视频' : '音频'}素材`}
      open={pickerOpen}
      onCancel={() => setPickerOpen(false)}
      onOk={confirmPicker}
      okText="确定"
      cancelText="取消"
      width={900}
      bodyStyle={{ padding: 0 }}
    >
      {/* 需求3: 本地上传和从资源库选择并列两个tab */}
      <Tabs
        activeKey={pickerActiveTab}
        onChange={(k) => {
          setPickerActiveTab(k as any)
          if (k === 'library') {
            handleLoadAssets(pickerCategory)
          }
        }}
        style={{ padding: '0 16px' }}
        items={[
          { key: 'upload', label: '本地上传' },
          { key: 'library', label: '从资源库选择' },
        ]}
      />

      <div style={{ padding: '0 16px 16px' }}>
        {/* 本地上传 */}
        {pickerActiveTab === 'upload' && (
          <div style={{ padding: 8, minHeight: 400 }}>
            <Dragger
              multiple
              accept={pickerCategory === 'image' ? 'image/*' : pickerCategory === 'video' ? 'video/*' : 'audio/*'}
              showUploadList={false}
              beforeUpload={(file) => handleFileUpload(file, pickerCategory)}
              style={{ marginBottom: 16, background: '#fafafa', borderColor: '#d9d9d9' }}
            >
              <p className="ant-upload-drag-icon" style={{ fontSize: 28, color: '#1677ff' }}>
                {pickerCategory === 'image' ? <PictureOutlined /> : pickerCategory === 'video' ? <VideoCameraOutlined /> : <AudioOutlined />}
              </p>
              <p className="ant-upload-text" style={{ fontSize: 13, color: '#1677ff', marginBottom: 4 }}>
                点击上传{pickerCategory === 'image' ? '图片' : pickerCategory === 'video' ? '视频' : '音频'}
              </p>
              <p className="ant-upload-hint" style={{ fontSize: 12, color: '#999' }}>
                或 拖拽本地{pickerCategory === 'image' ? '图片' : pickerCategory === 'video' ? '视频' : '音频'}至此上传
              </p>
            </Dragger>

            {/* 当前已上传的文件 */}
            {pickerCategory === 'image' && currentState.uploadImages.length > 0 && (
              <div>
                <div style={{ fontSize: 12, color: '#666', marginBottom: 8 }}>
                  已上传 {currentState.uploadImages.length} 张图片（点击右上角可移除）
                </div>
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))',
                    gap: 12,
                  }}
                >
                  {currentState.uploadImages.map((img, idx) => (
                    <div
                      key={idx}
                      style={{
                        position: 'relative',
                        borderRadius: 8,
                        overflow: 'hidden',
                        border: '1px solid #f0f0f0',
                        aspectRatio: '1',
                        background: '#fafafa',
                      }}
                    >
                      <Image
                        src={img.cdn_url}
                        alt="upload"
                        preview={false}
                        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      />
                      <Button
                        type="text"
                        danger
                        size="small"
                        onClick={() => handleRemoveFile(idx, 'image')}
                        style={{
                          position: 'absolute',
                          top: 4,
                          right: 4,
                          width: 24,
                          height: 24,
                          minWidth: 24,
                          padding: 0,
                          borderRadius: 12,
                          background: 'rgba(0,0,0,0.5)',
                          color: '#fff',
                        }}
                      >
                        <CloseOutlined />
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {pickerCategory === 'video' && currentState.uploadVideos.length > 0 && (
              <div>
                <div style={{ fontSize: 12, color: '#666', marginBottom: 8 }}>
                  已上传 {currentState.uploadVideos.length} 个视频（点击右上角可移除）
                </div>
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))',
                    gap: 12,
                  }}
                >
                  {currentState.uploadVideos.map((video, idx) => (
                    <div
                      key={idx}
                      style={{
                        position: 'relative',
                        borderRadius: 8,
                        overflow: 'hidden',
                        border: '1px solid #f0f0f0',
                        aspectRatio: '16/9',
                        background: '#fafafa',
                      }}
                    >
                      <VideoCameraOutlined style={{ width: '100%', height: '100%', padding: 20 }} />
                      <Button
                        type="text"
                        danger
                        size="small"
                        onClick={() => handleRemoveFile(idx, 'video')}
                        style={{
                          position: 'absolute',
                          top: 4,
                          right: 4,
                          width: 24,
                          height: 24,
                          minWidth: 24,
                          padding: 0,
                          borderRadius: 12,
                          background: 'rgba(0,0,0,0.5)',
                          color: '#fff',
                        }}
                      >
                        <CloseOutlined />
                      </Button>
                      <div style={{ position: 'absolute', bottom: 4, left: 4, fontSize: 10, color: '#fff', background: 'rgba(0,0,0,0.5)', padding: '2px 4px', borderRadius: 2 }}>
                        {video.file_name}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {pickerCategory === 'audio' && currentState.uploadAudios.length > 0 && (
              <div>
                <div style={{ fontSize: 12, color: '#666', marginBottom: 8 }}>
                  已上传 {currentState.uploadAudios.length} 个音频（点击右上角可移除）
                </div>
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))',
                    gap: 12,
                  }}
                >
                  {currentState.uploadAudios.map((audio, idx) => (
                    <div
                      key={idx}
                      style={{
                        position: 'relative',
                        borderRadius: 8,
                        overflow: 'hidden',
                        border: '1px solid #f0f0f0',
                        aspectRatio: '2/1',
                        background: '#fafafa',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      <AudioOutlined style={{ fontSize: 24, color: '#666' }} />
                      <Button
                        type="text"
                        danger
                        size="small"
                        onClick={() => handleRemoveFile(idx, 'audio')}
                        style={{
                          position: 'absolute',
                          top: 4,
                          right: 4,
                          width: 24,
                          height: 24,
                          minWidth: 24,
                          padding: 0,
                          borderRadius: 12,
                          background: 'rgba(0,0,0,0.5)',
                          color: '#fff',
                        }}
                      >
                        <CloseOutlined />
                      </Button>
                      <div style={{ position: 'absolute', bottom: 4, left: 4, fontSize: 10, color: '#fff', background: 'rgba(0,0,0,0.5)', padding: '2px 4px', borderRadius: 2 }}>
                        {audio.file_name}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {currentState.uploadImages.length === 0 && pickerCategory === 'image' && (
              <Empty description="暂无上传图片" style={{ padding: '48px 0' }} />
            )}
            {currentState.uploadVideos.length === 0 && pickerCategory === 'video' && (
              <Empty description="暂无上传视频" style={{ padding: '48px 0' }} />
            )}
            {currentState.uploadAudios.length === 0 && pickerCategory === 'audio' && (
              <Empty description="暂无上传音频" style={{ padding: '48px 0' }} />
            )}
          </div>
        )}

        {/* 从资源库选择 */}
        {pickerActiveTab === 'library' && (
          <div style={{ padding: 8, minHeight: 400, maxHeight: 480, overflowY: 'auto' }}>
            {assetLoading ? (
              <Empty description="加载中..." style={{ padding: '48px 0' }} />
            ) : assetList.length === 0 ? (
              <Empty description={`资源库暂无${pickerCategory === 'image' ? '图片' : pickerCategory === 'video' ? '视频' : '音频'}`} style={{ padding: '48px 0' }} />
            ) : (
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))',
                  gap: 12,
                }}
              >
                {assetList.map((a) => {
                  const selected = selectedAssets.has(a.id)
                  const cdnReady = pickerCategory !== 'image' || isAssetCdnReady(a)
                  return (
                    <div
                      key={a.id}
                      onClick={() => cdnReady && toggleAsset(a.id)}
                      style={{
                        position: 'relative',
                        borderRadius: 8,
                        overflow: 'hidden',
                        border: selected ? '2px solid #1677ff' : '1px solid #f0f0f0',
                        aspectRatio: pickerCategory === 'image' ? '1' : '16/9',
                        cursor: cdnReady ? 'pointer' : 'not-allowed',
                        background: '#fafafa',
                        boxSizing: 'border-box',
                        opacity: cdnReady ? 1 : 0.45,
                      }}
                    >
                      {pickerCategory === 'image' && (
                        <Image
                          src={a.resolved_cdn_url || a.url}
                          alt={a.file_name}
                          preview={false}
                          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                        />
                      )}
                      {pickerCategory === 'image' && !cdnReady && (
                        <div
                          style={{
                            position: 'absolute',
                            bottom: 0,
                            left: 0,
                            right: 0,
                            background: 'rgba(0,0,0,0.55)',
                            color: '#fff',
                            fontSize: 10,
                            padding: '4px 6px',
                            textAlign: 'center',
                          }}
                        >
                          不可用于生图
                        </div>
                      )}
                      {pickerCategory === 'video' && (
                        <video
                          src={a.url}
                          poster={a.url}
                          muted
                          loop
                          playsInline
                          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                          onClick={(e) => e.stopPropagation()}
                        />
                      )}
                      {pickerCategory === 'audio' && (
                        <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                          <AudioOutlined style={{ fontSize: 24, color: '#666' }} />
                        </div>
                      )}
                      {selected && (
                        <div
                          style={{
                            position: 'absolute',
                            top: 6,
                            right: 6,
                            width: 22,
                            height: 22,
                            borderRadius: 11,
                            background: '#1677ff',
                            color: '#fff',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: 12,
                          }}
                        >
                          <CheckOutlined />
                        </div>
                      )}
                      <div style={{ position: 'absolute', bottom: 4, left: 4, fontSize: 10, color: '#fff', background: 'rgba(0,0,0,0.5)', padding: '2px 4px', borderRadius: 2, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: 'calc(100% - 32px)' }}>
                        {a.file_name}
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}
      </div>
    </Modal>
  )

  return (
    <Card
      className="composer-panel"
      bordered={false}
    >
      {/* 类型选择 */}
      <div
        style={{
          display: 'flex',
          gap: 2,
          marginBottom: 6,
        }}
      >
        {(['image', 'video', 'text'] as const).map((cat) => (
          <button
            key={cat}
            onClick={() => handleSelectCategory(cat)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 3,
              padding: '3px 10px',
              borderRadius: 14,
              background: activeCategory === cat ? 'linear-gradient(135deg, #7c5cfc 0%, #9b7dff 100%)' : 'transparent',
              color: activeCategory === cat ? '#fff' : '#666',
              border: activeCategory === cat ? 'none' : '1px solid #eee',
              cursor: 'pointer',
              fontSize: 11,
              fontWeight: 500,
              transition: 'all 0.2s',
              lineHeight: 1.4,
            }}
          >
            {iconMap[cat]}
            {labelMap[cat]}
          </button>
        ))}
      </div>

      {/* 提示词输入 */}
      <div style={{ marginBottom: 6 }}>
        <div style={{ display: 'flex', gap: 6, marginBottom: 4 }}>
          <Button
            type="text"
            icon={<FileTextOutlined />}
            onClick={handleLoadPrompts}
            style={{ padding: '0 6px', fontSize: 11, color: '#7c5cfc', height: 24 }}
          >
            提示词
          </Button>
          {promptList.length > 0 && (
            <Select
              placeholder="选择预设提示词"
              style={{ width: 200 }}
              size="small"
              loading={promptLoading}
              onSelect={(value) => {
                const prompt = promptList.find((p) => p._id === value)
                if (prompt) handleSelectPrompt(prompt)
              }}
              filterOption={(input, option) =>
                (option?.label as string).toLowerCase().includes(input.toLowerCase())
              }
            >
              {promptList.map((p) => (
                <Select.Option key={p._id} value={p._id} label={p.name}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Tag color={p.category === 'image' ? 'green' : p.category === 'video' ? 'purple' : 'blue'}>
                      {p.category === 'image' ? '图片' : p.category === 'video' ? '视频' : '文本'}
                    </Tag>
                    <span>{p.name}</span>
                  </div>
                </Select.Option>
              ))}
            </Select>
          )}
        </div>
        <TextArea
          value={currentState.prompt}
          onChange={(e) => updateCurrentState({ prompt: e.target.value })}
          placeholder="描述你想要的画面，支持 @ 引用素材..."
          rows={2}
          style={{ borderRadius: 8, border: '1px solid #ebebef', lineHeight: 1.45, fontSize: 13, resize: 'none' }}
        />
      </div>

      {/* 素材按钮区域 - 基于模型配置显示支持的上传类型 */}
      <div style={{ marginBottom: 6 }}>
        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', alignItems: 'center' }}>
          {/* 根据模型配置决定显示哪些上传按钮 */}
          {(currentModel?.supported_inputs?.video !== false || !currentModel) && (
            <Button
              type="default"
              size="small"
              onClick={() => openPicker('video')}
              style={{
                width: 40,
                height: 40,
                borderRadius: 8,
                border: '1px dashed #d9d9d9',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 0,
                color: '#888',
                background: '#fafafa',
                padding: 0,
              }}
            >
              <PlusOutlined style={{ fontSize: 12 }} />
              <span style={{ fontSize: 9 }}>视频</span>
            </Button>
          )}
          {(currentModel?.supported_inputs?.image !== false || !currentModel) && (
            <Button
              type="default"
              size="small"
              onClick={() => openPicker('image')}
              style={{
                width: 40,
                height: 40,
                borderRadius: 8,
                border: '1px dashed #d9d9d9',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 0,
                color: '#888',
                background: '#fafafa',
                padding: 0,
              }}
            >
              <PlusOutlined style={{ fontSize: 12 }} />
              <span style={{ fontSize: 9 }}>图片</span>
            </Button>
          )}
          {(currentModel?.supported_inputs?.audio !== false || !currentModel) && (
            <Button
              type="default"
              size="small"
              onClick={() => openPicker('audio')}
              style={{
                width: 40,
                height: 40,
                borderRadius: 8,
                border: '1px dashed #d9d9d9',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 0,
                color: '#888',
                background: '#fafafa',
                padding: 0,
              }}
            >
              <PlusOutlined style={{ fontSize: 12 }} />
              <span style={{ fontSize: 9 }}>音频</span>
            </Button>
          )}

          {/* 已上传的图片 */}
          {currentState.uploadImages.length > 0 && (
            <div
              style={{
                display: 'flex',
                gap: 8,
                flexWrap: 'wrap',
                marginLeft: 8,
              }}
            >
              {currentState.uploadImages.map((img, idx) => (
                <div
                  key={'img-' + idx}
                  style={{
                    position: 'relative',
                    width: 56,
                    height: 56,
                    borderRadius: 8,
                    overflow: 'hidden',
                    border: '1px solid #f0f0f0',
                  }}
                >
                  <Image
                    src={img.cdn_url}
                    alt="upload"
                    preview={false}
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                  />
                  <Button
                    type="text"
                    danger
                    size="small"
                    onClick={() => handleRemoveFile(idx, 'image')}
                    style={{
                      position: 'absolute',
                      top: 2,
                      right: 2,
                      width: 18,
                      height: 18,
                      minWidth: 18,
                      padding: 0,
                      borderRadius: 9,
                      background: 'rgba(0,0,0,0.5)',
                      color: '#fff',
                    }}
                  >
                    <CloseOutlined />
                  </Button>
                </div>
              ))}
            </div>
          )}

          {/* 已上传的视频 */}
          {currentState.uploadVideos.length > 0 && (
            <div
              style={{
                display: 'flex',
                gap: 8,
                flexWrap: 'wrap',
              }}
            >
              {currentState.uploadVideos.map((video, idx) => (
                <div
                  key={'vid-' + idx}
                  style={{
                    position: 'relative',
                    width: 72,
                    height: 48,
                    borderRadius: 8,
                    overflow: 'hidden',
                    border: '1px solid #f0f0f0',
                    background: '#fafafa',
                  }}
                >
                  <VideoCameraOutlined style={{ width: '100%', height: '100%', padding: 10 }} />
                  <Button
                    type="text"
                    danger
                    size="small"
                    onClick={() => handleRemoveFile(idx, 'video')}
                    style={{
                      position: 'absolute',
                      top: 2,
                      right: 2,
                      width: 18,
                      height: 18,
                      minWidth: 18,
                      padding: 0,
                      borderRadius: 9,
                      background: 'rgba(0,0,0,0.5)',
                      color: '#fff',
                    }}
                  >
                    <CloseOutlined />
                  </Button>
                  <div style={{ position: 'absolute', bottom: 2, left: 2, fontSize: 10, color: '#fff', background: 'rgba(0,0,0,0.5)', padding: '1px 3px', borderRadius: 2 }}>
                    {video.file_name}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* 已上传的音频 */}
          {currentState.uploadAudios.length > 0 && (
            <div
              style={{
                display: 'flex',
                gap: 8,
                flexWrap: 'wrap',
              }}
            >
              {currentState.uploadAudios.map((audio, idx) => (
                <div
                  key={'aud-' + idx}
                  style={{
                    position: 'relative',
                    width: 80,
                    height: 36,
                    borderRadius: 8,
                    overflow: 'hidden',
                    border: '1px solid #f0f0f0',
                    background: '#fafafa',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <AudioOutlined style={{ fontSize: 16, color: '#666' }} />
                  <Button
                    type="text"
                    danger
                    size="small"
                    onClick={() => handleRemoveFile(idx, 'audio')}
                    style={{
                      position: 'absolute',
                      top: 2,
                      right: 2,
                      width: 16,
                      height: 16,
                      minWidth: 16,
                      padding: 0,
                      borderRadius: 8,
                      background: 'rgba(0,0,0,0.5)',
                      color: '#fff',
                    }}
                  >
                    <CloseOutlined />
                  </Button>
                  <div style={{ position: 'absolute', bottom: 2, left: 2, fontSize: 10, color: '#666', padding: '1px 3px' }}>
                    {audio.file_name}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 原有上传区域（保持兼容性） */}
      {activeCategory !== 'text' && (
        <div style={{ display: 'none' }}>
          <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 8 }}>
            {activeCategory === 'image' ? '图片素材' : '素材'}
            <Button
              type="text"
              size="small"
              onClick={() => openPicker('image')}
              style={{ marginLeft: 12, color: '#1677ff', padding: 0 }}
            >
              + 选择图片
            </Button>
            {activeCategory === 'video' && (
              <>
                <Button
                  type="text"
                  size="small"
                  onClick={() => openPicker('video')}
                  style={{ marginLeft: 8, color: '#1677ff', padding: 0 }}
                >
                  + 选择视频
                </Button>
                <Button
                  type="text"
                  size="small"
                  onClick={() => openPicker('audio')}
                  style={{ marginLeft: 8, color: '#1677ff', padding: 0 }}
                >
                  + 选择音频
                </Button>
              </>
            )}
          </div>

          {/* 已上传的图片 */}
          {currentState.uploadImages.length > 0 && (
            <div
              style={{
                display: 'flex',
                gap: 12,
                flexWrap: 'wrap',
              }}
            >
              {currentState.uploadImages.map((img, idx) => (
                <div
                  key={idx}
                  style={{
                    position: 'relative',
                    width: 56,
                    height: 56,
                    borderRadius: 6,
                    overflow: 'hidden',
                    border: '1px solid #f0f0f0',
                  }}
                >
                  <Image
                    src={img.cdn_url}
                    alt="upload"
                    preview={false}
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                  />
                  <Button
                    type="text"
                    danger
                    size="small"
                    onClick={() => handleRemoveFile(idx, 'image')}
                    style={{
                      position: 'absolute',
                      top: 2,
                      right: 2,
                      width: 20,
                      height: 20,
                      minWidth: 20,
                      padding: 0,
                      borderRadius: 10,
                      background: 'rgba(0,0,0,0.5)',
                      color: '#fff',
                    }}
                  >
                    <CloseOutlined />
                  </Button>
                </div>
              ))}
            </div>
          )}

          {/* 已上传的视频 */}
          {activeCategory === 'video' && currentState.uploadVideos.length > 0 && (
            <div
              style={{
                display: 'flex',
                gap: 12,
                flexWrap: 'wrap',
                marginTop: 12,
              }}
            >
              {currentState.uploadVideos.map((video, idx) => (
                <div
                  key={idx}
                  style={{
                    position: 'relative',
                    width: 120,
                    height: 80,
                    borderRadius: 8,
                    overflow: 'hidden',
                    border: '1px solid #f0f0f0',
                    background: '#fafafa',
                  }}
                >
                  <VideoCameraOutlined style={{ width: '100%', height: '100%', padding: 10 }} />
                  <Button
                    type="text"
                    danger
                    size="small"
                    onClick={() => handleRemoveFile(idx, 'video')}
                    style={{
                      position: 'absolute',
                      top: 2,
                      right: 2,
                      width: 20,
                      height: 20,
                      minWidth: 20,
                      padding: 0,
                      borderRadius: 10,
                      background: 'rgba(0,0,0,0.5)',
                      color: '#fff',
                    }}
                  >
                    <CloseOutlined />
                  </Button>
                  <div style={{ position: 'absolute', bottom: 2, left: 2, fontSize: 10, color: '#fff', background: 'rgba(0,0,0,0.5)', padding: '1px 3px', borderRadius: 2 }}>
                    {video.file_name}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* 已上传的音频 */}
          {activeCategory === 'video' && currentState.uploadAudios.length > 0 && (
            <div
              style={{
                display: 'flex',
                gap: 12,
                flexWrap: 'wrap',
                marginTop: 12,
              }}
            >
              {currentState.uploadAudios.map((audio, idx) => (
                <div
                  key={idx}
                  style={{
                    position: 'relative',
                    width: 72,
                    height: 32,
                    borderRadius: 8,
                    overflow: 'hidden',
                    border: '1px solid #f0f0f0',
                    background: '#fafafa',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <AudioOutlined style={{ fontSize: 18, color: '#666' }} />
                  <Button
                    type="text"
                    danger
                    size="small"
                    onClick={() => handleRemoveFile(idx, 'audio')}
                    style={{
                      position: 'absolute',
                      top: 2,
                      right: 2,
                      width: 18,
                      height: 18,
                      minWidth: 18,
                      padding: 0,
                      borderRadius: 9,
                      background: 'rgba(0,0,0,0.5)',
                      color: '#fff',
                    }}
                  >
                    <CloseOutlined />
                  </Button>
                  <div style={{ position: 'absolute', bottom: 2, left: 2, fontSize: 10, color: '#666', padding: '1px 3px' }}>
                    {audio.file_name}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 底部工具栏 */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: 6, borderTop: '1px solid #f0f0f2' }}>
        {/* 左侧：模型选择 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
          <Popover
            content={modelPanel}
            title="选择模型"
            trigger="click"
            placement="bottomLeft"
          >
            <Button
              type="default"
              style={{ 
                borderRadius: 6,
                padding: '4px 12px',
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                fontSize: 12,
              }}
            >
              <span>{currentModel?.model_name || 'Seedance 2.0 Fast VIP'}</span>
              <DownOutlined style={{ fontSize: 10 }} />
            </Button>
          </Popover>

          {/* 图片参数配置 */}
          {activeCategory === 'image' && (
            <Popover
              content={imageConfigPanel}
              title="图片配置"
              trigger="click"
              placement="bottomLeft"
            >
              <Button
                type="default"
                style={{ 
                  borderRadius: 6,
                  padding: '4px 12px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 4,
                  fontSize: 12,
                }}
              >
                <span>{currentSize} | {currentState.quality === 'auto' ? '自动' : currentState.quality === 'low' ? '低' : currentState.quality === 'medium' ? '中' : '高'} | {currentState.count}张</span>
                <DownOutlined style={{ fontSize: 10 }} />
              </Button>
            </Popover>
          )}

          {/* 视频参数配置 */}
          {activeCategory === 'video' && (
            <Popover
              content={configPanel}
              title="视频配置"
              trigger="click"
              placement="bottomLeft"
            >
              <Button
                type="default"
                style={{ 
                  borderRadius: 6,
                  padding: '4px 12px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 4,
                  fontSize: 12,
                }}
              >
                <span>{videoConfigLabel}</span>
                <DownOutlined style={{ fontSize: 10 }} />
              </Button>
            </Popover>
          )}

          {/* 图片参数配置 */}
          {activeCategory === 'image' && (
            <span style={{ fontSize: 11, color: '#999' }}>
              {currentSize}
            </span>
          )}

          {/* 文本模式不显示额外配置 */}
          {activeCategory === 'text' && (
            <span style={{ fontSize: 12, color: '#999' }}>
              —
            </span>
          )}
        </div>

        {/* 右侧：功能按钮和提交按钮 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          {/* 功能图标按钮 */}
          {/* 生成按钮 - 只保留"开始创作" */}
          <Button
            type="primary"
            size="small"
            loading={submitting}
            onClick={handleSubmit}
            style={{
              height: 26,
              borderRadius: 13,
              padding: '0 16px',
              fontSize: 11,
              fontWeight: 500,
              background: 'linear-gradient(135deg, #7c5cfc 0%, #9b7dff 100%)',
              border: 'none',
            }}
          >
            开始创作
          </Button>
        </div>
      </div>

      {/* 素材选择弹窗 */}
      {pickerModal}

      {/* 配置弹窗 */}
      <Modal
        title="参数配置"
        open={configOpen}
        onCancel={() => setConfigOpen(false)}
        footer={null}
        width={560}
      >
        {configPanel}
      </Modal>
    </Card>
  )
}
