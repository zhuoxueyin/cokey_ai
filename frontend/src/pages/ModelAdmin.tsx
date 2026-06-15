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
  Switch,
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
  SettingOutlined,
  EyeOutlined,
  CodeOutlined,
} from '@ant-design/icons'
import {
  listModelsAdmin,
  createModelAdmin,
  updateModelAdmin,
  deleteModelAdmin,
  setModelStatus,
  listChannelsAdmin,
} from '@/api'
import type { ModelItem, ParamField, ChannelBinding, ChannelItem } from '@/types'

const { TextArea } = Input
const { Option } = Select

const categoryMap: Record<string, { label: string; color: string }> = {
  text: { label: '文本', color: 'blue' },
  image: { label: '图像', color: 'green' },
  video: { label: '视频', color: 'purple' },
}

const statusMap: Record<string, { label: string; color: string }> = {
  online: { label: '在线', color: 'green' },
  offline: { label: '离线', color: 'default' },
  maintenance: { label: '维护中', color: 'orange' },
}

interface ModelFormData {
  model_code: string
  model_name: string
  category: 'text' | 'image' | 'video'
  description?: string
  cover?: string
  tags?: string
  status: 'online' | 'offline' | 'maintenance'
  sort_order: number
  is_default: boolean
}

export default function ModelAdmin() {
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<ModelItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [filterCategory, setFilterCategory] = useState<string | undefined>()
  const [filterStatus, setFilterStatus] = useState<string | undefined>()
  const [modalVisible, setModalVisible] = useState(false)
  const [editingItem, setEditingItem] = useState<ModelItem | null>(null)
  const [viewItem, setViewItem] = useState<ModelItem | null>(null)
  const [form] = Form.useForm<ModelFormData>()
  const [channelList, setChannelList] = useState<ChannelItem[]>([])
  const [bindings, setBindings] = useState<ChannelBinding[]>([])

  const fetchChannels = async () => {
    try {
      const res = await listChannelsAdmin({ page: 1, page_size: 100 })
      setChannelList(res.data || [])
    } catch (e) {
      console.error(e)
    }
  }

  const fetchData = async () => {
    setLoading(true)
    try {
      const res = await listModelsAdmin({
        page,
        page_size: pageSize,
        category: filterCategory,
        status: filterStatus,
      })
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
  }, [page, pageSize, filterCategory, filterStatus])

  const handleAdd = async () => {
    setEditingItem(null)
    form.resetFields()
    form.setFieldsValue({
      category: 'text',
      status: 'online',
      sort_order: 0,
      is_default: false,
    })
    setBindings([])
    await fetchChannels()
    setModalVisible(true)
  }

  const handleEdit = async (record: ModelItem) => {
    setEditingItem(record)
    form.setFieldsValue({
      model_code: record.model_code,
      model_name: record.model_name,
      category: record.category,
      description: record.description,
      cover: record.cover,
      tags: record.tags?.join(', '),
      status: record.status || 'online',
      sort_order: record.sort_order || 0,
      is_default: record.is_default || false,
    })
    setBindings(record.channel_bindings ? [...record.channel_bindings] : [])
    await fetchChannels()
    setModalVisible(true)
  }

  const addBinding = () => {
    const defaultChannel = channelList.find((c) => c.status === 'active') || channelList[0]
    if (!defaultChannel) {
      message.warning('请先创建一个可用的渠道')
      return
    }
    setBindings([
      ...bindings,
      {
        channel_code: defaultChannel.channel_code,
        channel_model_id: '',
        priority: 10,
        status: 'active',
      },
    ])
  }

  const updateBinding = (idx: number, patch: Partial<ChannelBinding>) => {
    const next = [...bindings]
    next[idx] = { ...next[idx], ...patch }
    setBindings(next)
  }

  const removeBinding = (idx: number) => {
    const next = bindings.filter((_, i) => i !== idx)
    setBindings(next)
  }

  const handleDelete = async (record: ModelItem) => {
    try {
      await deleteModelAdmin(record.id)
      message.success('删除成功')
      fetchData()
    } catch (e: any) {
      message.error(e.message || '删除失败')
    }
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      const tagsArr = values.tags
        ? values.tags.split(',').map((t: string) => t.trim()).filter(Boolean)
        : []

      const cleanedBindings = bindings
        .filter((b) => b.channel_code && b.channel_model_id && b.channel_model_id.trim())
        .map((b) => ({
          channel_code: b.channel_code,
          channel_model_id: b.channel_model_id.trim(),
          priority: typeof b.priority === 'number' ? b.priority : 10,
          status: b.status || 'active',
        }))

      const payload: any = {
        model_code: values.model_code,
        model_name: values.model_name,
        category: values.category,
        description: values.description,
        cover: values.cover,
        tags: tagsArr,
        status: values.status,
        sort_order: values.sort_order,
        is_default: values.is_default,
        param_schema: { fields: [] },
        channel_bindings: cleanedBindings,
      }

      if (editingItem) {
        await updateModelAdmin(editingItem.id, payload)
        message.success('更新成功')
      } else {
        await createModelAdmin(payload)
        message.success('创建成功')
      }
      setModalVisible(false)
      fetchData()
    } catch (e: any) {
      if (e.errorFields) return
      message.error(e.message || '提交失败')
    }
  }

  const handleStatusChange = async (record: ModelItem, status: 'online' | 'offline' | 'maintenance') => {
    try {
      await setModelStatus(record.id, status)
      message.success('状态已更新')
      fetchData()
    } catch (e: any) {
      message.error(e.message || '更新失败')
    }
  }

  const columns: ColumnsType<ModelItem> = [
    {
      title: '模型名称',
      dataIndex: 'model_name',
      key: 'model_name',
      render: (v, r) => (
        <Space>
          <strong>{v}</strong>
          {r.is_default && <Tag color="gold">默认</Tag>}
        </Space>
      ),
    },
    {
      title: '编码',
      dataIndex: 'model_code',
      key: 'model_code',
      render: (v) => <code style={{ background: '#f5f5f5', padding: '2px 6px', borderRadius: 4 }}>{v}</code>,
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      width: 100,
      render: (v) => {
        const c = categoryMap[v] || { label: v, color: 'default' }
        return <Tag color={c.color}>{c.label}</Tag>
      },
    },
    {
      title: '标签',
      dataIndex: 'tags',
      key: 'tags',
      render: (v: string[]) => (
        <Space size={4} wrap>
          {v?.map((t: string) => <Tag key={t}>{t}</Tag>)}
        </Space>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 140,
      render: (v, r) => {
        const s = statusMap[v || 'online'] || { label: v, color: 'default' }
        return (
          <Select
            size="small"
            value={v || 'online'}
            style={{ width: 100 }}
            onChange={(val) => handleStatusChange(r, val)}
          >
            <Option value="online"><Tag color="green">在线</Tag></Option>
            <Option value="offline"><Tag>离线</Tag></Option>
            <Option value="maintenance"><Tag color="orange">维护中</Tag></Option>
          </Select>
        )
      },
    },
    {
      title: '排序',
      dataIndex: 'sort_order',
      key: 'sort_order',
      width: 80,
    },
    {
      title: '渠道绑定',
      key: 'bindings',
      width: 120,
      render: (_: any, r: ModelItem) => {
        const count = r.channel_bindings?.length || 0
        const active = (r.channel_bindings || []).filter((b) => b.status === 'active').length
        if (count === 0) return <Tag color="red">未绑定</Tag>
        return (
          <Space size={2}>
            <Tag color="green">{active} 启用</Tag>
            <Tag>{count - active} 禁用</Tag>
          </Space>
        )
      },
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
      width: 180,
      fixed: 'right',
      render: (_, r) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button size="small" icon={<EyeOutlined />} onClick={() => setViewItem(r)} />
          </Tooltip>
          <Tooltip title="编辑">
            <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(r)} />
          </Tooltip>
          <Popconfirm title="确定删除该模型？" onConfirm={() => handleDelete(r)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <Card
        title="模型管理"
        extra={
          <Space>
            <Select
              placeholder="分类筛选"
              allowClear
              style={{ width: 120 }}
              value={filterCategory}
              onChange={(v) => { setFilterCategory(v); setPage(1) }}
            >
              <Option value="text">文本</Option>
              <Option value="image">图像</Option>
              <Option value="video">视频</Option>
            </Select>
            <Select
              placeholder="状态筛选"
              allowClear
              style={{ width: 120 }}
              value={filterStatus}
              onChange={(v) => { setFilterStatus(v); setPage(1) }}
            >
              <Option value="online">在线</Option>
              <Option value="offline">离线</Option>
              <Option value="maintenance">维护中</Option>
            </Select>
            <Button icon={<ReloadOutlined />} onClick={fetchData} />
            <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
              新增模型
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
          scroll={{ x: 1200 }}
        />
      </Card>

      <Modal
        title={editingItem ? '编辑模型' : '新增模型'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={760}
        okText="保存"
        cancelText="取消"
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="model_code" label="模型编码" rules={[{ required: true, message: '请输入模型编码' }]}>
                <Input placeholder="如: gpt-4o-mini" disabled={!!editingItem} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="model_name" label="模型名称" rules={[{ required: true, message: '请输入模型名称' }]}>
                <Input placeholder="如: GPT-4o Mini" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="category" label="分类" rules={[{ required: true }]}>
                <Select>
                  <Option value="text">文本</Option>
                  <Option value="image">图像</Option>
                  <Option value="video">视频</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="status" label="状态" rules={[{ required: true }]}>
                <Select>
                  <Option value="online">在线</Option>
                  <Option value="offline">离线</Option>
                  <Option value="maintenance">维护中</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="sort_order" label="排序权重" initialValue={0}>
                <InputNumber style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="description" label="描述">
            <TextArea rows={2} placeholder="模型描述..." />
          </Form.Item>
          <Form.Item name="tags" label="标签（逗号分隔）">
            <Input placeholder="如: 通用,对话,高质量" />
          </Form.Item>
          <Form.Item name="cover" label="封面图 URL">
            <Input placeholder="https://..." />
          </Form.Item>
          <Form.Item name="is_default" label="设为该分类默认模型" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Divider orientation="left" plain>渠道绑定</Divider>
          <div style={{ marginBottom: 12 }}>
            <Space>
              <Button type="dashed" onClick={addBinding}>+ 添加渠道</Button>
              <span style={{ color: '#888', fontSize: 12 }}>选择一个或多个渠道，网关按优先级从高到低路由</span>
            </Space>
          </div>
          {bindings.length === 0 && (
            <Empty
              description="还没有绑定渠道"
              style={{ margin: '12px 0 16px' }}
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          )}
          {bindings.map((b, idx) => (
            <Card
              key={idx}
              size="small"
              style={{ marginBottom: 8 }}
              title={
                <Space>
                  <span>绑定 #{idx + 1}</span>
                  {b.status === 'active' && <Tag color="green" style={{ margin: 0 }}>启用</Tag>}
                  {b.status !== 'active' && <Tag color="default" style={{ margin: 0 }}>禁用</Tag>}
                </Space>
              }
              extra={
                <Button size="small" danger type="text" onClick={() => removeBinding(idx)}>删除</Button>
              }
            >
              <Row gutter={12}>
                <Col span={10}>
                  <div style={{ fontSize: 12, color: '#666', marginBottom: 4 }}>渠道</div>
                  <Select
                    value={b.channel_code}
                    onChange={(val) => updateBinding(idx, { channel_code: val })}
                    style={{ width: '100%' }}
                  >
                    {channelList.map((c) => (
                      <Option key={c.channel_code} value={c.channel_code}>
                        {c.channel_name}
                        {c.status === 'active' ? '' : ' (已禁用)'}
                      </Option>
                    ))}
                  </Select>
                </Col>
                <Col span={10}>
                  <div style={{ fontSize: 12, color: '#666', marginBottom: 4 }}>渠道内模型 ID</div>
                  <Input
                    placeholder="如: gpt-5.5 / gemini-2.5-flash"
                    value={b.channel_model_id}
                    onChange={(e) => updateBinding(idx, { channel_model_id: e.target.value })}
                  />
                </Col>
                <Col span={4}>
                  <div style={{ fontSize: 12, color: '#666', marginBottom: 4 }}>优先级</div>
                  <InputNumber
                    value={b.priority}
                    onChange={(val) => updateBinding(idx, { priority: Number(val) || 0 })}
                    style={{ width: '100%' }}
                  />
                </Col>
                <Col span={4}>
                  <div style={{ fontSize: 12, color: '#666', marginBottom: 4 }}>状态</div>
                  <Select
                    value={b.status}
                    onChange={(val) => updateBinding(idx, { status: val })}
                    style={{ width: '100%' }}
                  >
                    <Option value="active">启用</Option>
                    <Option value="inactive">禁用</Option>
                  </Select>
                </Col>
              </Row>
            </Card>
          ))}
        </Form>
      </Modal>

      <Modal
        title={
          <Space>
            <CodeOutlined />
            <span>{viewItem?.model_name} - 配置详情</span>
          </Space>
        }
        open={!!viewItem}
        onCancel={() => setViewItem(null)}
        footer={[<Button key="close" onClick={() => setViewItem(null)}>关闭</Button>]}
        width={720}
      >
        {viewItem && (
          <div>
            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={12}>
                <div style={{ color: '#888', fontSize: 12 }}>模型编码</div>
                <code>{viewItem.model_code}</code>
              </Col>
              <Col span={12}>
                <div style={{ color: '#888', fontSize: 12 }}>分类</div>
                <Tag color={categoryMap[viewItem.category]?.color}>{categoryMap[viewItem.category]?.label}</Tag>
              </Col>
            </Row>
            {viewItem.description && (
              <div style={{ marginBottom: 16 }}>
                <div style={{ color: '#888', fontSize: 12, marginBottom: 4 }}>描述</div>
                <div>{viewItem.description}</div>
              </div>
            )}
            {viewItem.tags && viewItem.tags.length > 0 && (
              <div style={{ marginBottom: 16 }}>
                <div style={{ color: '#888', fontSize: 12, marginBottom: 4 }}>标签</div>
                <Space wrap>
                  {viewItem.tags.map((t) => <Tag key={t}>{t}</Tag>)}
                </Space>
              </div>
            )}

            <Divider style={{ margin: '12px 0' }}>参数 Schema</Divider>
            {viewItem.param_schema?.fields && viewItem.param_schema.fields.length > 0 ? (
              <div style={{ background: '#fafafa', padding: 12, borderRadius: 6, maxHeight: 300, overflowY: 'auto' }}>
                {viewItem.param_schema.fields.map((f: ParamField, i: number) => (
                  <Card key={i} size="small" style={{ marginBottom: 8 }}>
                    <Row gutter={8}>
                      <Col span={6}><code>{f.name}</code></Col>
                      <Col span={6}>{f.label}</Col>
                      <Col span={6}><Tag>{f.field_type}</Tag></Col>
                      <Col span={6}>{f.required ? <Tag color="red">必填</Tag> : <Tag>可选</Tag>}</Col>
                    </Row>
                    {f.help_text && <div style={{ color: '#888', fontSize: 12, marginTop: 4 }}>{f.help_text}</div>}
                  </Card>
                ))}
              </div>
            ) : (
              <Empty description="暂无参数配置" />
            )}

            {viewItem.channel_bindings && viewItem.channel_bindings.length > 0 && (
              <>
                <Divider style={{ margin: '12px 0' }}>渠道绑定</Divider>
                {viewItem.channel_bindings.map((cb: ChannelBinding, i: number) => (
                  <Card key={i} size="small" style={{ marginBottom: 8 }}>
                    <Row gutter={8}>
                      <Col span={8}><code>{cb.channel_code}</code></Col>
                      <Col span={10}>模型ID: {cb.channel_model_id}</Col>
                      <Col span={6}>优先级: {cb.priority}</Col>
                    </Row>
                  </Card>
                ))}
              </>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}
