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
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ReloadOutlined,
  EyeOutlined,
} from '@ant-design/icons'
import {
  listChannelsAdmin,
  createChannelAdmin,
  updateChannelAdmin,
  deleteChannelAdmin,
  setChannelStatus,
} from '@/api'
import type { ChannelItem } from '@/types'

const { TextArea } = Input
const { Option } = Select

const channelTypeMap: Record<string, { label: string; color: string }> = {
  aggregator: { label: '聚合渠道', color: 'blue' },
  direct: { label: '直连渠道', color: 'cyan' },
}

const statusMap: Record<string, { label: string; color: string }> = {
  active: { label: '启用', color: 'green' },
  inactive: { label: '停用', color: 'default' },
}

interface ChannelFormData {
  channel_code: string
  channel_name: string
  channel_type: 'aggregator' | 'direct'
  base_url: string
  description?: string
  status: 'active' | 'inactive'
  text_api_key?: string
  image_api_key?: string
  video_api_key?: string
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

  const handleAdd = () => {
    setEditingItem(null)
    form.resetFields()
    form.setFieldsValue({
      channel_type: 'direct',
      status: 'active',
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
    form.setFieldsValue({
      channel_code: record.channel_code,
      channel_name: record.channel_name,
      channel_type: record.channel_type,
      base_url: record.base_url,
      description: record.description,
      status: record.status,
      text_api_key: record.auth_config?.text_api_key,
      image_api_key: record.auth_config?.image_api_key,
      video_api_key: record.auth_config?.video_api_key,
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

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()

      const payload: any = {
        channel_code: values.channel_code,
        channel_name: values.channel_name,
        channel_type: values.channel_type,
        base_url: values.base_url,
        description: values.description,
        status: values.status,
        auth_config: {
          text_api_key: values.text_api_key,
          image_api_key: values.image_api_key,
          video_api_key: values.video_api_key,
        },
        retry_config: {
          timeout: values.retry_timeout,
          max_retries: values.retry_max_retries,
          retry_delay: values.retry_retry_delay,
        },
        rate_limit_config: {
          requests_per_minute: values.rate_limit_per_minute,
          requests_per_hour: values.rate_limit_per_hour,
          requests_per_day: values.rate_limit_per_day,
        },
      }

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
      message.error(e.message || '提交失败')
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
      render: (v) => <strong>{v}</strong>,
    },
    {
      title: '编码',
      dataIndex: 'channel_code',
      key: 'channel_code',
      render: (v) => <code style={{ background: '#f5f5f5', padding: '2px 6px', borderRadius: 4 }}>{v}</code>,
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
      title: '接口地址',
      dataIndex: 'base_url',
      key: 'base_url',
      render: (v) => <code style={{ fontSize: 12 }}>{v}</code>,
      ellipsis: true,
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
      render: (v) => v?.replace('T', ' ').slice(0, 19),
    },
    {
      title: '操作',
      key: 'actions',
      width: 160,
      fixed: 'right',
      render: (_, r) => (
        <Space size="small">
          <Tooltip title="查看">
            <Button size="small" icon={<EyeOutlined />} onClick={() => setViewItem(r)} />
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
    <div>
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
          rowKey="id"
          loading={loading}
          dataSource={data}
          columns={columns}
          pagination={{
            current: page,
            pageSize,
            total,
            onChange: (p, ps) => { setPage(p); setPageSize(ps) },
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (t) => `共 ${t} 条`,
          }}
          scroll={{ x: 1100 }}
        />
      </Card>

      <Modal
        title={editingItem ? '编辑渠道' : '新增渠道'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={720}
        okText="保存"
        cancelText="取消"
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="channel_code" label="渠道编码" rules={[{ required: true, message: '请输入渠道编码' }]}>
                <Input placeholder="如: openai" disabled={!!editingItem} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="channel_name" label="渠道名称" rules={[{ required: true, message: '请输入渠道名称' }]}>
                <Input placeholder="如: OpenAI" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="channel_type" label="渠道类型" rules={[{ required: true }]}>
                <Select>
                  <Option value="direct">直连渠道</Option>
                  <Option value="aggregator">聚合渠道</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="status" label="状态" rules={[{ required: true }]}>
                <Select>
                  <Option value="active">启用</Option>
                  <Option value="inactive">停用</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="base_url" label="接口根地址" rules={[{ required: true, message: '请输入接口地址' }]}>
            <Input placeholder="https://api.example.com/v1" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <TextArea rows={2} placeholder="渠道说明..." />
          </Form.Item>

          <Divider style={{ margin: '12px 0' }}>认证配置</Divider>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="text_api_key" label="文本模型 API Key">
                <Input.Password placeholder="sk-..." />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="image_api_key" label="图像模型 API Key">
                <Input.Password placeholder="sk-..." />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="video_api_key" label="视频模型 API Key">
                <Input.Password placeholder="sk-..." />
              </Form.Item>
            </Col>
          </Row>

          <Divider style={{ margin: '12px 0' }}>重试配置</Divider>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="retry_timeout" label="超时时间(秒)">
                <InputNumber style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="retry_max_retries" label="最大重试次数">
                <InputNumber style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="retry_retry_delay" label="重试间隔(秒)">
                <InputNumber style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Divider style={{ margin: '12px 0' }}>限流配置</Divider>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="rate_limit_per_minute" label="每分钟请求数">
                <InputNumber style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="rate_limit_per_hour" label="每小时请求数">
                <InputNumber style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="rate_limit_per_day" label="每日请求数">
                <InputNumber style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>

      <Modal
        title={`渠道详情 - ${viewItem?.channel_name}`}
        open={!!viewItem}
        onCancel={() => setViewItem(null)}
        footer={[<Button key="close" onClick={() => setViewItem(null)}>关闭</Button>]}
        width={640}
      >
        {viewItem && (
          <div>
            <Row gutter={16} style={{ marginBottom: 12 }}>
              <Col span={12}>
                <div style={{ color: '#888', fontSize: 12 }}>编码</div>
                <code>{viewItem.channel_code}</code>
              </Col>
              <Col span={12}>
                <div style={{ color: '#888', fontSize: 12 }}>类型</div>
                <Tag color={channelTypeMap[viewItem.channel_type]?.color}>{channelTypeMap[viewItem.channel_type]?.label}</Tag>
              </Col>
            </Row>
            <Row gutter={16} style={{ marginBottom: 12 }}>
              <Col span={24}>
                <div style={{ color: '#888', fontSize: 12 }}>接口地址</div>
                <code>{viewItem.base_url}</code>
              </Col>
            </Row>
            {viewItem.description && (
              <div style={{ marginBottom: 12 }}>
                <div style={{ color: '#888', fontSize: 12, marginBottom: 4 }}>描述</div>
                <div>{viewItem.description}</div>
              </div>
            )}

            <Divider style={{ margin: '12px 0' }}>认证配置</Divider>
            <Card size="small" style={{ marginBottom: 8 }}>
              <Row gutter={8}>
                <Col span={8}>
                  <div style={{ color: '#888', fontSize: 12 }}>文本 API Key</div>
                  <div>{viewItem.auth_config?.text_api_key ? '******' : '未设置'}</div>
                </Col>
                <Col span={8}>
                  <div style={{ color: '#888', fontSize: 12 }}>图像 API Key</div>
                  <div>{viewItem.auth_config?.image_api_key ? '******' : '未设置'}</div>
                </Col>
                <Col span={8}>
                  <div style={{ color: '#888', fontSize: 12 }}>视频 API Key</div>
                  <div>{viewItem.auth_config?.video_api_key ? '******' : '未设置'}</div>
                </Col>
              </Row>
            </Card>

            <Divider style={{ margin: '12px 0' }}>重试配置</Divider>
            <Card size="small" style={{ marginBottom: 8 }}>
              <Row gutter={8}>
                <Col span={8}>超时: {viewItem.retry_config?.timeout || 0} 秒</Col>
                <Col span={8}>重试: {viewItem.retry_config?.max_retries || 0} 次</Col>
                <Col span={8}>间隔: {viewItem.retry_config?.retry_delay || 0} 秒</Col>
              </Row>
            </Card>

            <Divider style={{ margin: '12px 0' }}>限流配置</Divider>
            <Card size="small">
              <Row gutter={8}>
                <Col span={8}>每分钟: {viewItem.rate_limit_config?.requests_per_minute || 0} 次</Col>
                <Col span={8}>每小时: {viewItem.rate_limit_config?.requests_per_hour || 0} 次</Col>
                <Col span={8}>每日: {viewItem.rate_limit_config?.requests_per_day || 0} 次</Col>
              </Row>
            </Card>
          </div>
        )}
      </Modal>
    </div>
  )
}
