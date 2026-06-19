import { useState, useEffect, useMemo } from 'react'
import { Link } from 'react-router-dom'
import {
  Drawer,
  Form,
  Input,
  Button,
  Space,
  Select,
  Tag,
  Divider,
  Alert,
  Typography,
  message,
  Descriptions,
} from 'antd'
import {
  ThunderboltOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons'
import {
  generate,
  debugChannelAdmin,
  getTaskAdmin,
} from '@/api'
import type { ModelItem, ChannelItem, EndpointConfig } from '@/types'

const { TextArea } = Input
const { Text } = Typography
const { Option } = Select

export type DebugPerspective = 'model' | 'channel'

interface Props {
  open: boolean
  onClose: () => void
  perspective: DebugPerspective
  model?: ModelItem | null
  channel?: ChannelItem | null
}

const DEFAULT_PROMPTS: Record<string, string> = {
  text: '你好，请用一句话介绍你自己。',
  chat: '你好，请用一句话介绍你自己。',
  image: '一只在阳光下打盹的橘猫，插画风格',
  image_edits: '根据参考图风格生成一张类似插画',
  video: '海浪轻轻拍打沙滩，夕阳西下',
  video_image: '海浪轻轻拍打沙滩，夕阳西下',
}

const ENDPOINT_TYPE_LABEL: Record<string, string> = {
  text: '文生文',
  chat: '对话式',
  image: '文生图',
  image_edits: '图生图',
  video: '文生视频',
  video_image: '图生视频',
  audio: '音频',
}

function categoryFromEndpoint(endpointType: string, protocolSlot?: string): 'text' | 'image' | 'video' {
  if (protocolSlot === 'openai.chat.image.text_to_image' || protocolSlot === 'openai.chat.image.image_to_image' || protocolSlot === 'openai.chat.image') {
    return 'image'
  }
  if (endpointType === 'video' || endpointType === 'video_image') return 'video'
  if (endpointType === 'image' || endpointType === 'image_edits') return 'image'
  return 'text'
}

function buildDefaultParams(category: string): Record<string, unknown> {
  const prompt = DEFAULT_PROMPTS[category] || DEFAULT_PROMPTS.text
  if (category === 'text') return { prompt }
  if (category === 'image') return { prompt, size: '1024x1024', n: 1 }
  if (category === 'video') return { prompt, duration: 5 }
  return { prompt }
}

function buildChannelDebugParams(
  endpointType: string,
  prompt: string,
  imageLines: string,
  size: string,
  channelModelId: string,
): Record<string, unknown> {
  const params: Record<string, unknown> = {
    prompt: prompt.trim() || DEFAULT_PROMPTS[endpointType] || DEFAULT_PROMPTS.text,
  }
  if (size.trim()) params.size = size.trim()
  if (endpointType === 'image' || endpointType === 'image_edits') {
    params.n = 1
  }
  if (endpointType === 'video' || endpointType === 'video_image') {
    params.duration = 5
  }
  const images = imageLines
    .split('\n')
    .map((s) => s.trim())
    .filter(Boolean)
  if (images.length) {
    params.images = images
  }
  if (channelModelId.trim()) {
    params.model = channelModelId.trim()
  }
  return params
}

function debugSessionId(): string {
  return `debug_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
}

function endpointLabel(ep: EndpointConfig, index: number): string {
  const typeLabel = ENDPOINT_TYPE_LABEL[ep.type] || ep.type
  const slot = ep.protocol_slot ? ` · ${ep.protocol_slot}` : ''
  return `[${index + 1}] ${typeLabel} · ${ep.method} ${ep.endpoint}${slot}`
}

export default function IntegrationDebugDrawer({
  open,
  onClose,
  perspective,
  model,
  channel,
}: Props) {
  const [running, setRunning] = useState(false)
  const [prompt, setPrompt] = useState('')
  const [channelModelId, setChannelModelId] = useState('')
  const [imageLines, setImageLines] = useState('')
  const [size, setSize] = useState('1024x1024')
  const [selectedEndpointIdx, setSelectedEndpointIdx] = useState(0)
  const [lastResult, setLastResult] = useState<{
    task_id?: string
    trace_id?: string
    status?: string
    error?: string
    duration_ms?: number
    success?: boolean
  } | null>(null)

  const endpoints = useMemo(() => channel?.endpoints || [], [channel?.endpoints])
  const selectedEndpoint = endpoints[selectedEndpointIdx] || null
  const selectedEndpointType = selectedEndpoint?.type || ''

  const needsImages =
    perspective === 'channel' &&
    (selectedEndpointType === 'image_edits' ||
      selectedEndpointType === 'video_image' ||
      (selectedEndpointType === 'chat' && imageLines.trim().length > 0))

  useEffect(() => {
    if (!open) return
    setLastResult(null)
    if (perspective === 'model') {
      const cat = model?.category || 'text'
      setPrompt(DEFAULT_PROMPTS[cat] || DEFAULT_PROMPTS.text)
    } else if (perspective === 'channel') {
      setSelectedEndpointIdx(0)
      setChannelModelId('')
      setImageLines('')
      setSize('1024x1024')
      const firstType = endpoints[0]?.type || 'text'
      setPrompt(DEFAULT_PROMPTS[firstType] || DEFAULT_PROMPTS.text)
    }
  }, [open, perspective, model?.category, channel?.id, endpoints])

  useEffect(() => {
    if (!open || perspective !== 'channel' || !selectedEndpointType) return
    setPrompt(DEFAULT_PROMPTS[selectedEndpointType] || DEFAULT_PROMPTS.text)
    if (selectedEndpointType === 'image' || selectedEndpointType === 'image_edits') {
      setSize('1024x1024')
    }
  }, [open, perspective, selectedEndpointType])

  const handleRunModel = async () => {
    if (!model) {
      message.warning('模型信息缺失')
      return
    }
    if (model.status === 'offline' || model.status === 'maintenance') {
      message.warning('模型当前非在线状态，试跑可能失败')
    }
    setRunning(true)
    setLastResult(null)
    try {
      const params = {
        ...buildDefaultParams(model.category),
        prompt: prompt.trim() || DEFAULT_PROMPTS[model.category],
      }
      const res = await generate({
        model_code: model.model_code,
        category: model.category,
        session_id: debugSessionId(),
        params,
      })
      if (res.code === 'success' && res.data) {
        const data = res.data
        let traceId = data.trace_id
        if (!traceId && data.task_id) {
          try {
            const taskRes = await getTaskAdmin(data.task_id)
            traceId = taskRes.data?.trace_id
          } catch {
            /* ignore */
          }
        }
        setLastResult({
          task_id: data.task_id,
          trace_id: traceId,
          status: data.status,
          duration_ms: data.duration_ms,
          success: data.status === 'success',
        })
        message.success('试跑已提交')
      } else {
        setLastResult({ error: res.message || '试跑失败', success: false })
        message.error(res.message || '试跑失败')
      }
    } catch (e: unknown) {
      const err = e as { message?: string; response?: { data?: { message?: string } } }
      const msg = err.response?.data?.message || err.message || '试跑异常'
      setLastResult({ error: msg, success: false })
      message.error(msg)
    } finally {
      setRunning(false)
    }
  }

  const handleRunChannel = async () => {
    if (!channel?.id) {
      message.warning('渠道信息缺失')
      return
    }
    if (!selectedEndpoint) {
      message.warning('请先配置至少一个端点')
      return
    }
    if (!channelModelId.trim()) {
      message.warning('请填写渠道侧模型 ID（channel_model_id）')
      return
    }
    if (selectedEndpointType === 'image_edits' && !imageLines.trim()) {
      message.warning('图生图端点需要至少一张参考图 URL')
      return
    }

    setRunning(true)
    setLastResult(null)
    try {
      const params = buildChannelDebugParams(
        selectedEndpointType,
        prompt,
        imageLines,
        size,
        channelModelId,
      )
      const res = await debugChannelAdmin(channel.id, {
        endpoint_type: selectedEndpointType,
        channel_model_id: channelModelId.trim(),
        params,
        category: categoryFromEndpoint(selectedEndpointType, selectedEndpoint?.protocol_slot),
      })
      if (res.code === 'success' && res.data) {
        const data = res.data
        setLastResult({
          trace_id: data.trace_id,
          duration_ms: data.duration_ms,
          success: data.success,
          error: data.success ? undefined : data.error_message,
        })
        if (data.success) {
          message.success('端点调试成功')
        } else {
          message.error(data.error_message || '端点调试失败')
        }
      } else {
        setLastResult({ error: res.message || '调试失败', success: false })
        message.error(res.message || '调试失败')
      }
    } catch (e: unknown) {
      const err = e as { message?: string; response?: { data?: { message?: string } } }
      const msg = err.response?.data?.message || err.message || '调试异常'
      setLastResult({ error: msg, success: false })
      message.error(msg)
    } finally {
      setRunning(false)
    }
  }

  const handleRun = perspective === 'channel' ? handleRunChannel : handleRunModel

  const title =
    perspective === 'model'
      ? `模型调试 · ${model?.model_name || model?.model_code || ''}`
      : `渠道调试 · ${channel?.channel_name || ''}`

  const runDisabled =
    perspective === 'channel' &&
    (!selectedEndpoint || !channelModelId.trim() || endpoints.length === 0)

  return (
    <Drawer title={title} open={open} onClose={onClose} width={580} destroyOnClose>
      {perspective === 'model' && model && (
        <Descriptions size="small" column={2} bordered style={{ marginBottom: 16 }}>
          <Descriptions.Item label="模型编码">{model.model_code}</Descriptions.Item>
          <Descriptions.Item label="分类">
            <Tag>{model.category}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="状态">{model.status || 'online'}</Descriptions.Item>
          <Descriptions.Item label="绑定渠道">{(model.channel_bindings || []).length} 个</Descriptions.Item>
        </Descriptions>
      )}

      {perspective === 'channel' && channel && (
        <>
          <Descriptions size="small" column={1} bordered style={{ marginBottom: 12 }}>
            <Descriptions.Item label="Base URL">
              <Text copyable={{ text: channel.base_url }} style={{ fontSize: 12 }}>
                {channel.base_url}
              </Text>
            </Descriptions.Item>
            <Descriptions.Item label="提供商">{channel.channel_provider || '-'}</Descriptions.Item>
          </Descriptions>

          {endpoints.length === 0 ? (
            <Alert
              type="warning"
              showIcon
              style={{ marginBottom: 12 }}
              message="该渠道尚未配置端点"
              description="请先在渠道编辑页添加端点后再调试。"
            />
          ) : (
            <Form layout="vertical">
              <Form.Item label="调试端点" required>
                <Select
                  value={selectedEndpointIdx}
                  onChange={setSelectedEndpointIdx}
                  optionLabelProp="label"
                >
                  {endpoints.map((ep, idx) => (
                    <Option key={idx} value={idx} label={endpointLabel(ep, idx)}>
                      <div style={{ fontSize: 12 }}>
                        <Tag color="blue">{ENDPOINT_TYPE_LABEL[ep.type] || ep.type}</Tag>
                        <code>
                          {ep.method} {ep.endpoint}
                        </code>
                        {ep.protocol_slot && (
                          <Tag color="geekblue" style={{ marginLeft: 6 }}>
                            {ep.protocol_slot}
                          </Tag>
                        )}
                      </div>
                    </Option>
                  ))}
                </Select>
              </Form.Item>
              <Form.Item
                label="渠道模型 ID"
                required
                extra="对应渠道 API 的 model 字段，与平台 model_code 无关"
              >
                <Input
                  value={channelModelId}
                  onChange={(e) => setChannelModelId(e.target.value)}
                  placeholder="如 gpt-image-2、ep-xxx"
                />
              </Form.Item>
            </Form>
          )}
        </>
      )}

      <Divider orientation="left" plain>
        {perspective === 'channel' ? '端点试跑' : '冒烟试跑'}
      </Divider>

      <Form layout="vertical">
        <Form.Item label="Prompt">
          <TextArea
            rows={3}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="输入试跑提示词"
          />
        </Form.Item>
        {perspective === 'channel' &&
          (selectedEndpointType === 'image' ||
            selectedEndpointType === 'image_edits' ||
            selectedEndpointType === 'chat') && (
            <Form.Item label="尺寸 size">
              <Input
                value={size}
                onChange={(e) => setSize(e.target.value)}
                placeholder="1024x1024"
              />
            </Form.Item>
          )}
        {perspective === 'channel' &&
          (selectedEndpointType === 'image_edits' ||
            selectedEndpointType === 'chat' ||
            selectedEndpointType === 'image') && (
            <Form.Item
              label="参考图 URL"
              required={selectedEndpointType === 'image_edits'}
              extra={needsImages ? '每行一个 CDN 图片地址' : '图生图必填；对话式/文生图可选'}
            >
              <TextArea
                rows={3}
                value={imageLines}
                onChange={(e) => setImageLines(e.target.value)}
                placeholder="https://cdn.example.com/image.png"
              />
            </Form.Item>
          )}
        <Button
          type="primary"
          icon={<ThunderboltOutlined />}
          loading={running}
          onClick={handleRun}
          disabled={runDisabled}
          block
        >
          {perspective === 'channel' ? '调用端点' : '发起试跑'}
        </Button>
      </Form>

      {lastResult && (
        <Alert
          style={{ marginTop: 12 }}
          type={
            lastResult.error || lastResult.success === false
              ? 'error'
              : lastResult.success
                ? 'success'
                : 'info'
          }
          showIcon
          icon={
            lastResult.error || lastResult.success === false ? (
              <CloseCircleOutlined />
            ) : lastResult.success ? (
              <CheckCircleOutlined />
            ) : undefined
          }
          message={
            lastResult.error || lastResult.success === false ? '调试失败' : '调试结果'
          }
          description={
            <Space direction="vertical" size={4}>
              {!lastResult.error && lastResult.success !== false && (
                <>
                  {lastResult.task_id && (
                    <div>
                      任务 ID：<code>{lastResult.task_id}</code>
                    </div>
                  )}
                  {lastResult.status && <div>状态：{lastResult.status}</div>}
                  {lastResult.duration_ms != null && <div>耗时：{lastResult.duration_ms} ms</div>}
                </>
              )}
              {lastResult.error && <div>{lastResult.error}</div>}
              {lastResult.trace_id && (
                <Link to={`/admin/trace-logs?trace_id=${encodeURIComponent(lastResult.trace_id)}`}>
                  查看本次链路日志 →
                </Link>
              )}
            </Space>
          }
        />
      )}

    </Drawer>
  )
}
