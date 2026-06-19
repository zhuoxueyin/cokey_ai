import { useState, useEffect } from 'react'
import {
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  Select,
  InputNumber,
  message,
  Popconfirm,
  Card,
  Row,
  Col,
  Tooltip,
  Empty,
  Divider,
  Switch,
  Collapse,
  Alert,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ReloadOutlined,
  EyeOutlined,
  CopyOutlined,
  MinusCircleOutlined,
  PlusCircleOutlined,
  BugOutlined,
} from '@ant-design/icons'
import {
  listChannelsAdmin,
  createChannelAdmin,
  updateChannelAdmin,
  deleteChannelAdmin,
  setChannelStatus,
} from '@/api'
import type { ChannelItem, ParamMapping, EndpointConfig as EndpointConfigType, BodyParam } from '@/types'
import { parseCurl, ParsedCurl, BodyField, bodyFieldsToBodyParams, extractContentTypeAndHeaders } from '@/utils/curlParser'
import { PROTOCOL_SLOT_PRESETS, getPresetByProtocolSlot, PROTOCOL_SLOT_TYPE_HINT } from '@/constants/protocol'
import {
  BODY_PARAM_SOURCE,
  BODY_PARAM_SOURCE_LABELS,
  BUILTIN_OPTIONS,
  getBodyParamPreset,
  normalizeBodyParam,
  createEmptyBodyParam,
} from '@/constants/bodyParamPresets'
import IntegrationDebugDrawer from '@/components/IntegrationDebugDrawer'
import { formatServerDateTime } from '@/utils/formatDateTime'

const { TextArea } = Input
const { Option } = Select
const { Panel } = Collapse

const channelTypeMap: Record<string, { label: string; color: string }> = {
  aggregator: { label: '聚合渠道', color: 'blue' },
  direct: { label: '直连渠道', color: 'cyan' },
}

const channelProviderMap: Record<string, { label: string; type: 'aggregator' | 'direct'; color: string }> = {
  weelinking: { label: '微链 WeeLinking (聚合)', type: 'aggregator', color: 'blue' },
  apiyi: { label: 'APIYi (聚合)', type: 'aggregator', color: 'geekblue' },
  volcengine: { label: '火山引擎 (直连)', type: 'direct', color: 'cyan' },
}

const statusMap: Record<string, { label: string; color: string }> = {
  active: { label: '启用', color: 'green' },
  inactive: { label: '停用', color: 'default' },
}

const endpointContentTypeMap: Record<string, string> = {
  text: 'application/json',
  chat: 'application/json',
  image: 'application/json',
  image_edits: 'multipart/form-data',
  video: 'application/json',
  video_image: 'application/json',
  audio: 'application/json',
}

const endpointTypeMap: Record<string, { label: string; color: string }> = {
  text: { label: '文生文', color: 'blue' },
  chat: { label: '对话式', color: 'cyan' },
  image: { label: '文生图', color: 'green' },
  image_edits: { label: '图生图', color: 'purple' },
  video: { label: '文生视频', color: 'orange' },
  video_image: { label: '图生视频', color: 'pink' },
  audio: { label: '音频生成', color: 'red' },
  other: { label: '其他', color: 'default' },
}

interface EndpointConfig {
  type: string
  endpoint: string
  method: string
  request_body?: string
  description?: string
}

interface ChannelFormData {
  channel_name: string
  channel_type: 'aggregator' | 'direct'
  channel_provider?: 'weelinking' | 'apiyi' | 'volcengine' | null
  base_url: string
  status: 'active' | 'inactive'
  api_key?: string
  endpoints: any[]
  text_stream: boolean
  retry_timeout: number
  retry_max_retries: number
  retry_retry_delay: number
  rate_limit_per_minute: number
  rate_limit_per_hour: number
  rate_limit_per_day: number
}

export default function ChannelAdmin() {
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<ChannelItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [filterStatus, setFilterStatus] = useState<string | undefined>()
  const [modalVisible, setModalVisible] = useState(false)
  const [editingItem, setEditingItem] = useState<ChannelItem | null>(null)
  const [viewItem, setViewItem] = useState<ChannelItem | null>(null)
  const [form] = Form.useForm<ChannelFormData>()
  const [generatedCode, setGeneratedCode] = useState('')
  const [debugChannel, setDebugChannel] = useState<ChannelItem | null>(null)

  // curl 粘贴浮窗状态
  const [curlModalVisible, setCurlModalVisible] = useState(false)
  const [curlText, setCurlText] = useState('')

  const fetchData = async () => {
    setLoading(true)
    try {
      const res = await listChannelsAdmin({ page, page_size: pageSize, status: filterStatus })
      setData(res.data || [])
      setTotal(res.total || 0)
    } catch (e: any) {
      message.error(e.message || '加载失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [page, pageSize, filterStatus])

  const generateChannelCode = () => {
    const timestamp = Date.now().toString(36)
    const random = Math.random().toString(36).substr(2, 6)
    return `channel_${timestamp}_${random}`
  }

  /**
   * 从 curl 解析并生成新端点（只识别 header 和 body，不影响 base_url 和 API Key）
   */
  const handleParseCurlFromModal = () => {
    if (!curlText || !curlText.trim()) {
      message.warning('请先粘贴 curl 命令')
      return
    }
    try {
      const parsed = parseCurl(curlText)

      // 从 headers 中提取 content_type + custom_headers（不识别 API KEY）
      const { content_type, custom_headers } = extractContentTypeAndHeaders(parsed.headers)

      // 将 body_fields 转换为 body_params 格式
      const body_params = bodyFieldsToBodyParams(parsed.body_fields)

      // 推断端点类型
      let endpointType = 'text'
      const lower = parsed.endpoint.toLowerCase()
      if (lower.includes('image')) {
        if (lower.includes('edit') || lower.includes('variation')) endpointType = 'image_edits'
        else endpointType = 'image'
      } else if (lower.includes('video')) {
        if (lower.includes('image')) endpointType = 'video_image'
        else endpointType = 'video'
      } else if (lower.includes('chat')) {
        endpointType = 'chat'
      } else if (lower.includes('audio') || lower.includes('speech')) {
        endpointType = 'audio'
      }

      // custom_headers 是对象 {key: value}，转为 Form.List 数组格式 [{key, value}]
      const headersArray = Object.keys(custom_headers).map(k => ({ key: k, value: custom_headers[k] }))

      // 构建新端点（只填 endpoint 路径、method、content_type、headers、body_params）
      const newEndpoint = {
        type: endpointType,
        endpoint: parsed.endpoint,
        method: parsed.method,
        description: `从 curl 自动生成 · ${parsed.method} ${parsed.endpoint}`,
        content_type,
        headers: headersArray,
        body_params,
        param_mappings: [],
        response_mappings: [],
      }

      // 保留已有端点，追加新端点
      const currentEndpoints = form.getFieldValue('endpoints') || []
      const mergedEndpoints = [...currentEndpoints, newEndpoint]

      // 只更新 endpoints，不影响 base_url 和 API Key
      form.setFieldsValue({ endpoints: mergedEndpoints })

      setCurlModalVisible(false)
      setCurlText('')

      message.success(
        `解析成功！已识别 ${body_params.length} 个 body 参数，端点类型=${endpointTypeMap[endpointType]?.label || endpointType}`
      )
    } catch (e: any) {
      message.error('curl 解析失败：' + (e.message || '请检查格式'))
    }
  }

  const handleAdd = () => {
    setEditingItem(null)
    form.resetFields()
    const code = generateChannelCode()
    setGeneratedCode(code)
    form.setFieldsValue({
      channel_type: 'direct',
      channel_provider: null,
      status: 'inactive',
      endpoints: [],
      text_stream: true,
      retry_timeout: 30,
      retry_max_retries: 3,
      retry_retry_delay: 2,
      rate_limit_per_minute: 60,
      rate_limit_per_hour: 1000,
      rate_limit_per_day: 10000,
    })
    setModalVisible(true)
  }

  const handleEdit = (record: ChannelItem) => {
    setEditingItem(record)
    setGeneratedCode(record.channel_code)
    
    let formEndpoints: any[] = []

    const endpointToForm = (ep: EndpointConfigType): any => {
      const result: any = {
        type: ep.type,
        protocol_slot: ep.protocol_slot || '',
        endpoint: ep.endpoint,
        method: ep.method,
        description: ep.description,
        content_type: ep.content_type || 'application/json',
        // 从 {key: value} 对象转换为 [{key, value}, ...] 数组供 Form.List 使用
        headers: ep.headers && typeof ep.headers === 'object'
          ? Object.entries(ep.headers).map(([k, v]) => ({ key: k, value: v }))
          : [],
        body_params: (ep.body_params || []).map((bp) => normalizeBodyParam(bp)),
        param_mappings: ep.param_mappings || [],
        response_mappings: ep.response_mappings || [],
      }
      if (ep.params_template) result.params_template_json = JSON.stringify(ep.params_template, null, 2)
      if (ep.required_params) result.required_params_json = ep.required_params.join(', ')
      if (ep.default_params) result.default_params_json = JSON.stringify(ep.default_params, null, 2)
      if (ep.response_extract_path) result.response_extract_path = ep.response_extract_path
      return result
    }

    if (record.endpoints && record.endpoints.length > 0) {
      formEndpoints = (record.endpoints as EndpointConfigType[]).map(endpointToForm)
    } else if (record.api_config) {
      // 兼容旧数据：从 api_config 中提取路径配置
      if (record.api_config.text_path) {
        formEndpoints.push({ type: 'text', endpoint: record.api_config.text_path, method: 'POST', description: '文生文接口', content_type: 'application/json', headers: {}, body_params: [], param_mappings: [], response_mappings: [] })
      }
      if (record.api_config.image_path) {
        formEndpoints.push({ type: 'image', endpoint: record.api_config.image_path, method: 'POST', description: '文生图接口', content_type: 'application/json', headers: {}, body_params: [], param_mappings: [], response_mappings: [] })
      }
      if (record.api_config.image_edits_path) {
        formEndpoints.push({ type: 'image_edits', endpoint: record.api_config.image_edits_path, method: 'POST', description: '图生图接口', content_type: 'application/json', headers: {}, body_params: [], param_mappings: [], response_mappings: [] })
      }
      if (record.api_config.video_path) {
        formEndpoints.push({ type: 'video', endpoint: record.api_config.video_path, method: 'POST', description: '文生视频接口', content_type: 'application/json', headers: {}, body_params: [], param_mappings: [], response_mappings: [] })
      }
    }

    form.setFieldsValue({
      channel_name: record.channel_name,
      channel_type: record.channel_type,
      channel_provider: (record as any).channel_provider || null,
      base_url: record.base_url,
      status: record.status,
      api_key: record.auth_config?.api_key,
      endpoints: formEndpoints,
      text_stream: record.api_config?.text_stream !== undefined ? record.api_config.text_stream : true,
      retry_timeout: record.retry_config?.timeout || 30,
      retry_max_retries: record.retry_config?.max_retries || 3,
      retry_retry_delay: record.retry_config?.retry_delay || 2,
      rate_limit_per_minute: record.rate_limit_config?.requests_per_minute || 60,
      rate_limit_per_hour: record.rate_limit_config?.requests_per_hour || 1000,
      rate_limit_per_day: record.rate_limit_config?.requests_per_day || 10000,
    })
    setModalVisible(true)
  }

  const handleDelete = async (record: ChannelItem) => {
    try {
      await deleteChannelAdmin(record.id)
      message.success('删除成功')
      fetchData()
    } catch (e: any) {
      message.error(e.message || '删除失败')
    }
  }

  const handleCopy = (record: ChannelItem) => {
    setEditingItem(null)
    form.resetFields()
    const code = generateChannelCode()
    setGeneratedCode(code)

    let formEndpoints: any[] = []

    const endpointToForm = (ep: EndpointConfigType): any => {
      const result: any = {
        type: ep.type,
        protocol_slot: ep.protocol_slot || '',
        endpoint: ep.endpoint,
        method: ep.method,
        description: ep.description,
        content_type: ep.content_type || 'application/json',
        // 从 {key: value} 对象转换为 [{key, value}, ...] 数组供 Form.List 使用
        headers: ep.headers && typeof ep.headers === 'object'
          ? Object.entries(ep.headers).map(([k, v]) => ({ key: k, value: v }))
          : [],
        body_params: (ep.body_params || []).map((bp) => normalizeBodyParam(bp)),
        param_mappings: ep.param_mappings || [],
        response_mappings: ep.response_mappings || [],
      }
      if (ep.params_template) result.params_template_json = JSON.stringify(ep.params_template, null, 2)
      if (ep.required_params) result.required_params_json = ep.required_params.join(', ')
      if (ep.default_params) result.default_params_json = JSON.stringify(ep.default_params, null, 2)
      if (ep.response_extract_path) result.response_extract_path = ep.response_extract_path
      return result
    }

    if (record.endpoints && record.endpoints.length > 0) {
      formEndpoints = (record.endpoints as EndpointConfigType[]).map(endpointToForm)
    } else if (record.api_config) {
      if (record.api_config.text_path) {
        formEndpoints.push({ type: 'text', endpoint: record.api_config.text_path, method: 'POST', description: '文生文接口', content_type: 'application/json', headers: [], body_params: [], param_mappings: [], response_mappings: [] })
      }
      if (record.api_config.image_path) {
        formEndpoints.push({ type: 'image', endpoint: record.api_config.image_path, method: 'POST', description: '文生图接口', content_type: 'application/json', headers: [], body_params: [], param_mappings: [], response_mappings: [] })
      }
      if (record.api_config.image_edits_path) {
        formEndpoints.push({ type: 'image_edits', endpoint: record.api_config.image_edits_path, method: 'POST', description: '图生图接口', content_type: 'application/json', headers: [], body_params: [], param_mappings: [], response_mappings: [] })
      }
      if (record.api_config.video_path) {
        formEndpoints.push({ type: 'video', endpoint: record.api_config.video_path, method: 'POST', description: '文生视频接口', content_type: 'application/json', headers: [], body_params: [], param_mappings: [], response_mappings: [] })
      }
    }
    
    form.setFieldsValue({
      channel_name: record.channel_name + ' (副本)',
      channel_type: record.channel_type,
      channel_provider: (record as any).channel_provider || null,
      base_url: record.base_url,
      status: 'inactive',
      api_key: record.auth_config?.api_key,
      endpoints: formEndpoints,
      text_stream: record.api_config?.text_stream !== undefined ? record.api_config.text_stream : true,
      retry_timeout: record.retry_config?.timeout || 30,
      retry_max_retries: record.retry_config?.max_retries || 3,
      retry_retry_delay: record.retry_config?.retry_delay || 2,
      rate_limit_per_minute: record.rate_limit_config?.requests_per_minute || 60,
      rate_limit_per_hour: record.rate_limit_config?.requests_per_hour || 1000,
      rate_limit_per_day: record.rate_limit_config?.requests_per_day || 10000,
    })
    setModalVisible(true)
  }

  const numOr = (val: unknown, fallback: number) =>
    val === null || val === undefined || val === '' ? fallback : Number(val)

  const resolveChannelType = (values: ChannelFormData): 'aggregator' | 'direct' => {
    if (values.channel_type) return values.channel_type
    const provider = values.channel_provider
    if (provider && channelProviderMap[provider]) {
      return channelProviderMap[provider].type
    }
    return 'aggregator'
  }

  const formatApiError = (e: any): string => {
    const data = e?.response?.data
    if (Array.isArray(data?.detail)) {
      return data.detail
        .map((d: any) => {
          const loc = Array.isArray(d?.loc) ? d.loc.join('.') : ''
          return loc ? `${loc}: ${d?.msg || ''}` : d?.msg || String(d)
        })
        .join('; ')
    }
    return e?.message || data?.message || data?.detail || '提交失败'
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()

      const processEndpoint = (ep: any): EndpointConfigType => {
        const result: EndpointConfigType = {
          type: ep.type,
          endpoint: ep.endpoint,
          method: ep.method,
          description: ep.description,
        }
        if (ep.protocol_slot?.trim()) result.protocol_slot = ep.protocol_slot.trim()
        // —— 新字段：content_type ——
        if (ep.content_type) result.content_type = ep.content_type

        // —— 新字段：headers（从 [{key, value}] 数组转换为 {key: value} 对象）——
        if (ep.headers && Array.isArray(ep.headers)) {
          const hdrObj: Record<string, string> = {}
          for (const h of ep.headers) {
            if (h && h.key && h.key.trim() !== '') {
              hdrObj[h.key.trim()] = h.value || ''
            }
          }
          if (Object.keys(hdrObj).length > 0) {
            result.headers = hdrObj
          }
        } else if (ep.headers && typeof ep.headers === 'object' && Object.keys(ep.headers).length > 0) {
          // 兼容：如果已经是对象形式，直接使用
          result.headers = ep.headers
        }

        // —— 新字段：body_params（入参表）——
        if (ep.body_params && ep.body_params.length > 0) {
          result.body_params = ep.body_params
            .filter((bp: BodyParam) => bp && bp.key && bp.key.trim() !== '')
            .map((bp: BodyParam) => {
              const n = normalizeBodyParam(bp)
              const row: BodyParam = {
                key: n.key.trim(),
                source: n.source || 'task_param',
                description: n.description,
              }
              if (n.source === 'literal') row.literal = n.literal ?? ''
              if (n.source === 'task_param' || n.source === 'image_urls') row.param = n.param ?? ''
              if (n.source === 'builtin') row.builtin = n.builtin || 'channel_model_id'
              return row
            })
        }

        // —— 旧格式兼容字段 ——
        if (ep.params_template_json) {
          try { result.params_template = JSON.parse(ep.params_template_json) } catch (e) {}
        }
        if (ep.param_mappings?.length) {
          const valid = ep.param_mappings.filter(
            (m: ParamMapping) => m?.source?.trim() && m?.target?.trim(),
          )
          if (valid.length) result.param_mappings = valid
        }
        if (ep.response_mappings?.length) {
          const valid = ep.response_mappings.filter(
            (m: any) => m?.source?.trim() && m?.target?.trim(),
          )
          if (valid.length) result.response_mappings = valid
        }
        if (ep.required_params_json) {
          result.required_params = ep.required_params_json.split(',').map((s: string) => s.trim()).filter(Boolean)
        }
        if (ep.default_params_json) {
          try { result.default_params = JSON.parse(ep.default_params_json) } catch (e) {}
        }
        if (ep.response_extract_path) result.response_extract_path = ep.response_extract_path
        return result
      }

      const channelType = resolveChannelType(values)
      const processedEndpoints = (values.endpoints || []).map(processEndpoint)

      const payload: any = {
        channel_code: generatedCode,
        channel_name: values.channel_name,
        channel_type: channelType,
        channel_provider: values.channel_provider || null,
        base_url: values.base_url,
        status: values.status,
        auth_config: {
          api_key: values.api_key || '',
        },
        api_config: {
          text_stream: values.text_stream ?? true,
        },
        endpoints: processedEndpoints,
        retry_config: {
          timeout: numOr(values.retry_timeout, 30),
          max_retries: numOr(values.retry_max_retries, 3),
          retry_delay: numOr(values.retry_retry_delay, 2),
        },
        rate_limit_config: {
          requests_per_minute: numOr(values.rate_limit_per_minute, 60),
          requests_per_hour: numOr(values.rate_limit_per_hour, 1000),
          requests_per_day: numOr(values.rate_limit_per_day, 10000),
        },
      }

      processedEndpoints.forEach((ep: EndpointConfig) => {
        if (ep.type === 'text') {
          payload.api_config.text_path = ep.endpoint
        } else if (ep.type === 'image') {
          payload.api_config.image_path = ep.endpoint
        } else if (ep.type === 'image_edits') {
          payload.api_config.image_edits_path = ep.endpoint
        } else if (ep.type === 'video') {
          payload.api_config.video_path = ep.endpoint
        } else if (ep.type === 'video_image') {
          payload.api_config.video_image_path = ep.endpoint
        } else if (ep.type === 'audio') {
          payload.api_config.audio_path = ep.endpoint
        }
      })

      if (editingItem) {
        await updateChannelAdmin(editingItem.id, payload)
        message.success('更新成功')
      } else {
        await createChannelAdmin(payload)
        message.success('创建成功')
      }
      setModalVisible(false)
      fetchData()
    } catch (e: any) {
      if (e.errorFields) return
      message.error(formatApiError(e))
    }
  }

  const handleStatusToggle = async (record: ChannelItem) => {
    const newStatus = record.status === 'active' ? 'inactive' : 'active'
    try {
      await setChannelStatus(record.id, newStatus)
      message.success('状态已更新')
      fetchData()
    } catch (e: any) {
      message.error(e.message || '更新失败')
    }
  }

  const columns: ColumnsType<ChannelItem> = [
    {
      title: '渠道名称',
      dataIndex: 'channel_name',
      key: 'channel_name',
      width: 200,
    },
    {
      title: '类型',
      dataIndex: 'channel_type',
      key: 'channel_type',
      width: 120,
      render: (v) => {
        const c = channelTypeMap[v] || { label: v, color: 'default' }
        return <Tag color={c.color}>{c.label}</Tag>
      },
    },
    {
      title: '提供商',
      dataIndex: 'channel_provider',
      key: 'channel_provider',
      width: 160,
      render: (v) => {
        if (!v) return <Tag color="default">默认/自动</Tag>
        const c = channelProviderMap[v] || { label: v, color: 'default' }
        return <Tag color={c.color}>{c.label}</Tag>
      },
    },
    {
      title: '接口根地址',
      dataIndex: 'base_url',
      key: 'base_url',
      render: (v) => <code style={{ fontSize: 12 }}>{v}</code>,
      ellipsis: true,
    },
    {
      title: '端点数量',
      key: 'endpoint_count',
      width: 100,
      render: (_: any, r: ChannelItem) => {
        const count = r.endpoints?.length || Object.keys(r.api_config || {}).filter(k => k.endsWith('_path')).length || 0
        return <Tag color="blue">{count} 个</Tag>
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (v, r) => (
        <Button
          type={v === 'active' ? 'primary' : 'default'}
          size="small"
          onClick={() => handleStatusToggle(r)}
        >
          {statusMap[v]?.label || v}
        </Button>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (v) => formatServerDateTime(v),
    },
    {
      title: '操作',
      key: 'actions',
      width: 240,
      fixed: 'right',
      render: (_, r) => (
        <Space size="small">
          <Tooltip title="调试">
            <Button size="small" icon={<BugOutlined />} onClick={() => setDebugChannel(r)} />
          </Tooltip>
          <Tooltip title="查看">
            <Button size="small" icon={<EyeOutlined />} onClick={() => setViewItem(r)} />
          </Tooltip>
          <Tooltip title="复制">
            <Button size="small" icon={<CopyOutlined />} onClick={() => handleCopy(r)} />
          </Tooltip>
          <Tooltip title="编辑">
            <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(r)} />
          </Tooltip>
          <Popconfirm title="确定删除该渠道？" onConfirm={() => handleDelete(r)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div style={{ padding: 24, height: '100%', overflowY: 'auto', boxSizing: 'border-box' }}>
      <Card
        title="渠道管理"
        extra={
          <Space>
            <Select
              placeholder="状态筛选"
              allowClear
              style={{ width: 120 }}
              value={filterStatus}
              onChange={(v) => { setFilterStatus(v); setPage(1) }}
            >
              <Option value="active">启用</Option>
              <Option value="inactive">停用</Option>
            </Select>
            <Button icon={<ReloadOutlined />} onClick={fetchData} />
            <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
              新增渠道
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={data}
          loading={loading}
          rowKey="id"
          pagination={{
            current: page,
            pageSize,
            total,
            onChange: (p, s) => { setPage(p); setPageSize(s) },
          }}
          scroll={{ x: 1200 }}
        />
      </Card>

      <Modal
        title={editingItem ? '编辑渠道' : '新增渠道'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={[
          <Button key="back" onClick={() => setModalVisible(false)}>取消</Button>,
          <Button key="submit" type="primary" loading={loading} onClick={handleSubmit}>
            {editingItem ? '更新' : '创建'}
          </Button>,
        ]}
        width={1180}
        styles={{ body: { maxHeight: 'calc(100vh - 200px)', overflowY: 'auto' } }}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          {/* ========= 基本信息 ========= */}
          <Card size="small" title="① 基本信息（渠道 + 鉴权）" style={{ marginBottom: 12 }}>
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  label="渠道名称"
                  name="channel_name"
                  rules={[{ required: true, message: '请输入' }]}
                >
                  <Input placeholder="如：火山引擎-豆包" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="渠道编码">
                  <Input value={generatedCode} disabled style={{ background: '#f5f5f5' }} />
                </Form.Item>
              </Col>
            </Row>
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  label="渠道类型"
                  name="channel_provider"
                  rules={[{ required: true, message: '请选择' }]}
                >
                  <Select
                    placeholder="选择渠道类型"
                    onChange={(val: string) => {
                      const info = channelProviderMap[val as keyof typeof channelProviderMap]
                      if (info) form.setFieldsValue({ channel_type: info.type })
                    }}
                  >
                    <Option value="weelinking">📦 微链 WeeLinking（聚合）</Option>
                    <Option value="apiyi">🔗 APIYi（聚合）</Option>
                    <Option value="volcengine">🌋 火山引擎（直连）</Option>
                  </Select>
                </Form.Item>
                <Form.Item name="channel_type" hidden>
                  <Input />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="状态" name="status">
                  <Select>
                    <Option value="active">🟢 启用</Option>
                    <Option value="inactive">⚪ 停用</Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>
            <Row gutter={16}>
              <Col span={14}>
                <Form.Item
                  label="Base URL"
                  name="base_url"
                  rules={[{ required: true, message: '请输入' }]}
                >
                  <Input placeholder="https://api.example.com/v1" />
                </Form.Item>
              </Col>
              <Col span={10}>
                <Form.Item label="API Key" name="api_key">
                  <Input.Password placeholder="Bearer 后部分（可留空）" />
                </Form.Item>
              </Col>
            </Row>
          </Card>

          {/* ========= 端点配置（核心，极简表格） ========= */}
          <Card
            size="small"
            title={
              <Space wrap>
                <span>② HTTP 端点</span>
                <Tag color="green">协议画像决定如何构参；此处只配 URL</Tag>
                <Button
                  size="small"
                  type="primary"
                  ghost
                  onClick={() => setCurlModalVisible(true)}
                >
                  粘贴 curl 识别
                </Button>
              </Space>
            }
            style={{ marginBottom: 12 }}
            extra={
              <Space wrap size={4}>
                {PROTOCOL_SLOT_PRESETS.map((preset) => (
                  <Button
                    key={preset.protocol_slot}
                    size="small"
                    type="dashed"
                    onClick={() => {
                      const current = form.getFieldValue('endpoints') || []
                      const exists = current.some((e: any) => e.protocol_slot === preset.protocol_slot)
                      if (exists) {
                        message.info('该协议槽位已存在')
                        return
                      }
                      form.setFieldsValue({
                        endpoints: [
                          ...current,
                          {
                            protocol_slot: preset.protocol_slot,
                            type: preset.type,
                            endpoint: preset.endpoint,
                            method: preset.method,
                            content_type: preset.content_type,
                            headers: [],
                            body_params: [],
                          },
                        ],
                      })
                    }}
                  >
                    + {preset.label}
                  </Button>
                ))}
              </Space>
            }
          >
            <Alert
              type="info"
              showIcon
              style={{ marginBottom: 12, fontSize: 12 }}
              message="协议槽位 vs 类型"
              description={
                <ul style={{ margin: 0, paddingLeft: 18 }}>
                  <li><strong>协议槽位</strong>：API 契约名（如 <code>openai.images.generations</code>），与模型侧协议画像一致</li>
                  <li><strong>类型</strong>：系统查找本渠道端点配置的键（<code>image</code> / <code>chat</code> / <code>image_edits</code>）</li>
                  <li>选择预设槽位后，<strong>类型、路径、方法、Content-Type 会自动联动</strong>；类型字段会锁定</li>
                  <li>同一类型可对应多个槽位（例如 <code>openai.chat.image.text_to_image</code> 与 <code>openai.chat.image.image_to_image</code> 都是 <code>chat</code>）</li>
                  <li><strong>火山视频</strong>请使用 <code>volcengine.video.multimodal</code>：同一端点支持文/图/视频/音频组合，类型统一为 <code>video</code></li>
                </ul>
              }
            />
            <Form.List name="endpoints">
              {(fields, { add, remove }) => (
                <>
                  {fields.map((field) => (
                    <div
                      key={field.key}
                      style={{
                        background: '#fafafa',
                        border: '1px solid #e8e8e8',
                        borderRadius: 8,
                        padding: '12px 14px',
                        marginBottom: 10,
                      }}
                    >
                      <Row gutter={[12, 8]} align="middle">
                        <Col flex="auto">
                          <Form.Item
                            {...field}
                            name={[field.name, 'protocol_slot']}
                            label={<span style={{ fontSize: 12, fontWeight: 600 }}>协议槽位</span>}
                            tooltip="描述走哪套 API 契约，与协议画像 protocol_slot 对应"
                            extra={PROTOCOL_SLOT_TYPE_HINT}
                            style={{ marginBottom: 0 }}
                          >
                            <Select
                              allowClear
                              showSearch
                              placeholder="如 openai.images.generations"
                              popupMatchSelectWidth={false}
                              dropdownStyle={{ minWidth: 420 }}
                              optionLabelProp="value"
                              options={PROTOCOL_SLOT_PRESETS.map((p) => ({
                                value: p.protocol_slot,
                                label: (
                                  <div>
                                    <div style={{ fontWeight: 500 }}>{p.label}</div>
                                    <div style={{ fontSize: 11, color: '#888' }}>{p.protocol_slot}</div>
                                  </div>
                                ),
                              }))}
                              onChange={(val: string) => {
                                const preset = PROTOCOL_SLOT_PRESETS.find((p) => p.protocol_slot === val)
                                if (!preset) return
                                const endpoints = [...(form.getFieldValue('endpoints') || [])]
                                endpoints[field.name] = {
                                  ...endpoints[field.name],
                                  protocol_slot: preset.protocol_slot,
                                  type: preset.type,
                                  endpoint: preset.endpoint,
                                  method: preset.method,
                                  content_type: preset.content_type,
                                }
                                form.setFieldsValue({ endpoints })
                              }}
                            />
                          </Form.Item>
                        </Col>
                        <Col flex="none">
                          <Button
                            danger
                            type="text"
                            icon={<MinusCircleOutlined />}
                            onClick={() => remove(field.name)}
                            style={{ marginTop: 22 }}
                          >
                            删除
                          </Button>
                        </Col>
                      </Row>

                      <Form.Item noStyle shouldUpdate>
                        {() => {
                          const ep = (form.getFieldValue('endpoints') || [])[field.name] || {}
                          const linked = !!getPresetByProtocolSlot(ep.protocol_slot)
                          return (
                      <Row gutter={12} style={{ marginTop: 4 }}>
                        <Col xs={24} sm={12} md={5}>
                          <Form.Item
                            {...field}
                            name={[field.name, 'type']}
                            label={
                              <Space size={4}>
                                <span style={{ fontSize: 12, fontWeight: 600 }}>类型</span>
                                {linked && <Tag color="processing" style={{ margin: 0, fontSize: 10 }}>已联动</Tag>}
                              </Space>
                            }
                            tooltip="endpoint_type：网关/适配器用此键匹配 endpoints[].type"
                            rules={[{ required: true, message: '请选择类型' }]}
                            style={{ marginBottom: 0 }}
                          >
                            <Select
                              placeholder="端点类型"
                              disabled={linked}
                              onChange={(val: string) => {
                                const endpoints = form.getFieldValue('endpoints') || []
                                if (endpoints[field.name]) {
                                  endpoints[field.name] = {
                                    ...endpoints[field.name],
                                    content_type: endpointContentTypeMap[val] || 'application/json',
                                  }
                                  form.setFieldsValue({ endpoints })
                                }
                              }}
                            >
                              <Option value="text">文生文</Option>
                              <Option value="chat">对话</Option>
                              <Option value="image">文生图</Option>
                              <Option value="image_edits">图生图</Option>
                              <Option value="video">文生视频</Option>
                              <Option value="video_image">图生视频</Option>
                              <Option value="audio">音频</Option>
                              <Option value="other">其他</Option>
                            </Select>
                          </Form.Item>
                        </Col>
                        <Col xs={24} sm={12} md={3}>
                          <Form.Item
                            {...field}
                            name={[field.name, 'method']}
                            label={<span style={{ fontSize: 12, fontWeight: 600 }}>方法</span>}
                            style={{ marginBottom: 0 }}
                          >
                            <Select>
                              <Option value="POST">POST</Option>
                              <Option value="GET">GET</Option>
                              <Option value="PUT">PUT</Option>
                              <Option value="DELETE">DELETE</Option>
                            </Select>
                          </Form.Item>
                        </Col>
                        <Col xs={24} sm={24} md={10}>
                          <Form.Item
                            {...field}
                            name={[field.name, 'endpoint']}
                            label={<span style={{ fontSize: 12, fontWeight: 600 }}>端点路径</span>}
                            rules={[{ required: true, message: '请填写路径' }]}
                            style={{ marginBottom: 0 }}
                          >
                            <Input placeholder="images/generations" />
                          </Form.Item>
                        </Col>
                        <Col xs={24} sm={24} md={6}>
                          <Form.Item
                            {...field}
                            name={[field.name, 'content_type']}
                            label={<span style={{ fontSize: 12, fontWeight: 600 }}>Content-Type</span>}
                            style={{ marginBottom: 0 }}
                          >
                            <Select allowClear placeholder="默认 JSON">
                              <Option value="application/json">application/json</Option>
                              <Option value="multipart/form-data">multipart/form-data</Option>
                              <Option value="application/x-www-form-urlencoded">x-www-form-urlencoded</Option>
                            </Select>
                          </Form.Item>
                        </Col>
                      </Row>
                          )
                        }}
                      </Form.Item>

                      {/* 高级：ConfigEngine 入参（默认折叠） */}
                      <Collapse
                        ghost
                        size="small"
                        style={{ marginTop: 6 }}
                        items={[{
                          key: 'advanced',
                          label: (
                            <Form.Item shouldUpdate={() => true} style={{ marginBottom: 0 }}>
                              {() => {
                                const list: any[] = form.getFieldValue('endpoints') || []
                                const thisEp = list[field.name] || {}
                                const bp: any[] = thisEp.body_params || []
                                const hd: any = thisEp.headers || []
                                const hCount = Array.isArray(hd) ? hd.length : 0
                                return (
                                  <span style={{ fontSize: 12 }}>
                                    高级 ConfigEngine 入参
                                    {(bp.length > 0 || hCount > 0) && (
                                      <Tag color="blue" style={{ marginLeft: 8 }}>已配置</Tag>
                                    )}
                                    <span style={{ color: '#999', marginLeft: 8 }}>
                                      多数场景由协议画像 builder 处理，无需填写
                                    </span>
                                  </span>
                                )
                              }}
                            </Form.Item>
                          ),
                          children: (
                      <div style={{ padding: '0 4px', background: '#fbfbfb', borderRadius: 4 }}>
                        <Alert
                          type="info"
                          showIcon
                          style={{ marginBottom: 8, fontSize: 12 }}
                          message="Body 入参怎么填"
                          description={
                            <ul style={{ margin: 0, paddingLeft: 18 }}>
                              <li><strong>API 字段</strong>：写入渠道 HTTP body 的 key（如 model、prompt、content）</li>
                              <li><strong>取值来源</strong>与<strong>来源配置</strong>一一对应，不再混用同一列</li>
                              <li>有协议画像 builder 的槽位（如火山视频、APIYI 对话式）<strong>建议留空</strong>，由适配器构建</li>
                              <li>可点「套用入参模板」按 protocol_slot 填充；curl 导入的示例值会自动标为「固定值」</li>
                            </ul>
                          }
                        />
                        <div style={{ marginBottom: 8 }}>
                          <Button
                            size="small"
                            type="link"
                            onClick={() => {
                              const list: any[] = form.getFieldValue('endpoints') || []
                              const slot = list[field.name]?.protocol_slot
                              const preset = getBodyParamPreset(slot)
                              if (!preset) {
                                message.info('当前协议槽位暂无入参模板，可留空由适配器处理')
                                return
                              }
                              const next = [...list]
                              next[field.name] = {
                                ...next[field.name],
                                body_params: preset.params.map((p) => ({ ...p })),
                              }
                              form.setFieldsValue({ endpoints: next })
                              message.success(`已套用「${preset.label}」模板：${preset.hint}`)
                            }}
                          >
                            套用入参模板（按 protocol_slot）
                          </Button>
                          <Button
                            size="small"
                            type="link"
                            danger
                            onClick={() => {
                              const list: any[] = form.getFieldValue('endpoints') || []
                              const next = [...list]
                              next[field.name] = { ...next[field.name], body_params: [] }
                              form.setFieldsValue({ endpoints: next })
                              message.success('已清空 body 入参，将走适配器 builder')
                            }}
                          >
                            清空（推荐 builder 场景）
                          </Button>
                        </div>
                        <div style={{ display: 'flex', gap: 6, marginBottom: 4, fontSize: 11, color: '#999', paddingLeft: 2 }}>
                          <span style={{ width: '20%' }}>API 字段</span>
                          <span style={{ width: '22%' }}>取值来源</span>
                          <span style={{ flex: 1 }}>来源配置</span>
                        </div>
                        <Form.List {...field} name={[field.name, 'body_params']}>
                          {(bpFields, { add: addBp, remove: removeBp }) => (
                            <>
                              {bpFields.map((bf) => (
                                <Form.Item
                                  key={bf.key}
                                  noStyle
                                  shouldUpdate={(prev, cur) =>
                                    prev?.endpoints?.[field.name]?.body_params?.[bf.name]?.source
                                    !== cur?.endpoints?.[field.name]?.body_params?.[bf.name]?.source
                                  }
                                >
                                  {() => {
                                    const source =
                                      form.getFieldValue(['endpoints', field.name, 'body_params', bf.name, 'source'])
                                      || 'task_param'
                                    return (
                                      <Row key={bf.key} gutter={6} align="middle" style={{ marginBottom: 6 }}>
                                        <Col span={5}>
                                          <Form.Item {...bf} name={[bf.name, 'key']} style={{ marginBottom: 0 }}>
                                            <Input size="small" placeholder="如 model" />
                                          </Form.Item>
                                        </Col>
                                        <Col span={5}>
                                          <Form.Item {...bf} name={[bf.name, 'source']} style={{ marginBottom: 0 }}>
                                            <Select size="small" placeholder="来源">
                                              {Object.entries(BODY_PARAM_SOURCE_LABELS).map(([k, label]) => (
                                                <Option key={k} value={k}>{label}</Option>
                                              ))}
                                            </Select>
                                          </Form.Item>
                                        </Col>
                                        <Col span={12}>
                                          {source === BODY_PARAM_SOURCE.LITERAL && (
                                            <Form.Item {...bf} name={[bf.name, 'literal']} style={{ marginBottom: 0 }}>
                                              <Input size="small" placeholder="固定字面量，对象/数组可写 JSON" />
                                            </Form.Item>
                                          )}
                                          {(source === BODY_PARAM_SOURCE.TASK_PARAM
                                            || source === BODY_PARAM_SOURCE.IMAGE_URLS) && (
                                            <Form.Item {...bf} name={[bf.name, 'param']} style={{ marginBottom: 0 }}>
                                              <Input
                                                size="small"
                                                placeholder={
                                                  source === BODY_PARAM_SOURCE.IMAGE_URLS
                                                    ? '任务参数字段，默认 images'
                                                    : '任务参数字段，留空=与 API 字段同名'
                                                }
                                              />
                                            </Form.Item>
                                          )}
                                          {source === BODY_PARAM_SOURCE.BUILTIN && (
                                            <Form.Item {...bf} name={[bf.name, 'builtin']} style={{ marginBottom: 0 }}>
                                              <Select size="small" placeholder="内置变量">
                                                {BUILTIN_OPTIONS.map((o) => (
                                                  <Option key={o.value} value={o.value}>{o.label}</Option>
                                                ))}
                                              </Select>
                                            </Form.Item>
                                          )}
                                          {source === BODY_PARAM_SOURCE.CHAT_MESSAGES && (
                                            <span style={{ fontSize: 11, color: '#888', lineHeight: '24px' }}>
                                              自动由 prompt + images 组装 messages
                                            </span>
                                          )}
                                        </Col>
                                        <Col span={2} style={{ textAlign: 'right' }}>
                                          <Button
                                            size="small"
                                            danger
                                            type="text"
                                            icon={<MinusCircleOutlined />}
                                            onClick={() => removeBp(bf.name)}
                                          />
                                        </Col>
                                      </Row>
                                    )
                                  }}
                                </Form.Item>
                              ))}
                              <Button
                                size="small"
                                type="dashed"
                                onClick={() => addBp(createEmptyBodyParam())}
                                style={{ width: '100%', marginTop: 2 }}
                              >
                                + 添加入参映射
                              </Button>
                            </>
                          )}
                        </Form.List>

                        {/* 自定义 headers */}
                        <div style={{ marginTop: 8 }}>
                          <div style={{ fontSize: 12, color: '#666', marginBottom: 6, fontWeight: 500 }}>
                            🔧 自定义 Headers
                            <span style={{ color: '#999', marginLeft: 8, fontWeight: 'normal' }}>
                              Authorization 由系统自动添加，无需配置
                            </span>
                          </div>
                          <Form.List {...field} name={[field.name, 'headers']}>
                            {(hdrFields, { add: addHdr, remove: removeHdr }) => (
                              <>
                                {hdrFields.map((hf) => (
                                  <Row key={hf.key} gutter={6} align="middle" style={{ marginBottom: 4 }}>
                                    <Col span={6}>
                                      <Form.Item {...hf} name={[hf.name, 'key']} style={{ marginBottom: 0 }}>
                                        <Input size="small" placeholder="header 名" />
                                      </Form.Item>
                                    </Col>
                                    <Col span={16}>
                                      <Form.Item {...hf} name={[hf.name, 'value']} style={{ marginBottom: 0 }}>
                                        <Input size="small" placeholder="header 值" />
                                      </Form.Item>
                                    </Col>
                                    <Col span={1} style={{ textAlign: 'right' }}>
                                      <Button size="small" danger type="text" icon={<MinusCircleOutlined />} onClick={() => removeHdr(hf.name)} />
                                    </Col>
                                  </Row>
                                ))}
                                <Button
                                  size="small"
                                  type="dashed"
                                  onClick={() => addHdr({ key: '', value: '' })}
                                  style={{ width: '100%', marginTop: 2 }}
                                >
                                  + 添加自定义 header
                                </Button>
                              </>
                            )}
                          </Form.List>
                        </div>
                      </div>
                          ),
                        }]}
                      />
                    </div>
                  ))}

                  <Button
                    type="dashed"
                    onClick={() =>
                      add({
                        type: '',
                        endpoint: '',
                        method: 'POST',
                        content_type: 'application/json',
                        body_params: [],
                        headers: [],
                      })
                    }
                    style={{ width: '100%', marginTop: 8 }}
                    icon={<PlusOutlined />}
                  >
                    添加端点
                  </Button>
                </>
              )}
            </Form.List>
          </Card>

          {/* ========= 高级配置（折叠） ========= */}
          <Collapse bordered={false} style={{ background: '#fafafa', borderRadius: 6 }}>
            <Panel header="⚙ 高级配置（可选：重试/限流）" key="advanced">
              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item label="流式响应" name="text_stream" valuePropName="checked">
                    <Switch />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item label="超时(秒)" name="retry_timeout">
                    <InputNumber min={5} max={600} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item label="最大重试" name="retry_max_retries">
                    <InputNumber min={0} max={10} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>
              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item label="重试延迟(秒)" name="retry_retry_delay">
                    <InputNumber min={1} max={60} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item label="每分钟限流" name="rate_limit_per_minute">
                    <InputNumber min={1} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item label="每小时限流" name="rate_limit_per_hour">
                    <InputNumber min={1} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>
              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item label="每日限流" name="rate_limit_per_day">
                    <InputNumber min={1} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>
            </Panel>
          </Collapse>
        </Form>

        {/* curl 粘贴识别：嵌套在编辑弹窗内，避免被父级 Modal 遮挡 */}
        <Modal
          title="📋 粘贴 curl 识别端点"
          open={curlModalVisible}
          zIndex={2000}
          onCancel={() => {
            setCurlModalVisible(false)
            setCurlText('')
          }}
          onOk={handleParseCurlFromModal}
          width={720}
          okText="🔍 解析并添加端点"
          cancelText="取消"
          destroyOnClose
        >
          <div style={{ marginBottom: 12, color: '#666', fontSize: 13 }}>
            粘贴 curl 命令，系统自动识别 <b>header</b> 和 <b>body 参数</b> 生成端点配置。
            <span style={{ color: '#999', marginLeft: 8 }}>（不影响 base_url 和 API Key）</span>
          </div>
          <TextArea
            value={curlText}
            onChange={(e) => setCurlText(e.target.value)}
            rows={12}
            style={{ fontFamily: 'Menlo, Consolas, monospace', fontSize: 12 }}
            placeholder={`示例：\ncurl https://api.weelink.ai/v1/chat/completions \\\n  -H "Authorization: Bearer YOUR_API_KEY" \\\n  -H "Content-Type: application/json" \\\n  -d "{\\\"model\\\": \\\"gpt-4o\\\", \\\"messages\\\": [{\\\"role\\\": \\\"user\\\", \\\"content\\\": \\\"hi\\\"}]}"\n\n或 multipart/form-data 格式：\ncurl https://api.example.com/v1/images/edits \\\n  -H "Authorization: Bearer YOUR_API_KEY" \\\n  -F "model=gpt-image-2" \\\n  -F "prompt=Place the product into the scene"`}
          />
        </Modal>
      </Modal>

      <Modal
        title="渠道详情"
        visible={!!viewItem}
        onCancel={() => setViewItem(null)}
        footer={null}
        width={700}
      >
        {viewItem && (
          <div style={{ padding: 16 }}>
            <Row gutter={16}>
              <Col span={12}>
                <div><strong>渠道名称:</strong> {viewItem.channel_name}</div>
              </Col>
              <Col span={12}>
                <div><strong>渠道编码:</strong> <code>{viewItem.channel_code}</code></div>
              </Col>
            </Row>
            <Row gutter={16} style={{ marginTop: 12 }}>
              <Col span={12}>
                <div><strong>渠道类型:</strong> <Tag color={channelTypeMap[viewItem.channel_type]?.color}>{channelTypeMap[viewItem.channel_type]?.label}</Tag></div>
              </Col>
              <Col span={12}>
                <div><strong>状态:</strong> <Tag color={statusMap[viewItem.status]?.color}>{statusMap[viewItem.status]?.label}</Tag></div>
              </Col>
            </Row>
            <Row gutter={16} style={{ marginTop: 12 }}>
              <Col span={24}>
                <div><strong>接口根地址:</strong> <code>{viewItem.base_url}</code></div>
              </Col>
            </Row>
            <Divider style={{ margin: '16px 0' }} />
            <div><strong>端点API列表:</strong></div>
            {viewItem.endpoints && viewItem.endpoints.length > 0 ? (
              <div style={{ marginTop: 8 }}>
                {viewItem.endpoints.map((ep: any, idx: number) => (
                  <div key={idx} style={{ background: '#f9f9f9', padding: 12, marginBottom: 8, borderRadius: 6 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
                      {ep.protocol_slot && (
                        <Tag color="geekblue"><code>{ep.protocol_slot}</code></Tag>
                      )}
                      <Tag color={endpointTypeMap[ep.type]?.color}>{endpointTypeMap[ep.type]?.label}</Tag>
                      <Tag color="blue">{ep.method}</Tag>
                      <code>{ep.endpoint}</code>
                    </div>
                    {ep.description && <div style={{ marginTop: 8, color: '#666', fontSize: 12 }}>描述: {ep.description}</div>}
                    {ep.request_body && <div style={{ marginTop: 8, fontSize: 12 }}>请求体规范: {ep.request_body}</div>}
                  </div>
                ))}
              </div>
            ) : (
              <Empty description="暂无端点配置" />
            )}
          </div>
        )}
      </Modal>
      <IntegrationDebugDrawer
        open={!!debugChannel}
        onClose={() => setDebugChannel(null)}
        perspective="channel"
        channel={debugChannel}
      />
    </div>
  )
}
