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
  EyeOutlined,
  CodeOutlined,
  CopyOutlined,
  BugOutlined,
} from '@ant-design/icons'
import {
  listModelsAdmin,
  createModelAdmin,
  updateModelAdmin,
  deleteModelAdmin,
  setModelStatus,
  listChannelsAdmin,
  listProtocolProfilesAdmin,
} from '@/api'
import type { ModelItem, ParamField, ChannelBinding, ChannelItem } from '@/types'
import ChannelBindingEditor from '@/components/ChannelBindingEditor'
import IntegrationDebugDrawer from '@/components/IntegrationDebugDrawer'
import { BUILTIN_PROFILE_OPTIONS } from '@/constants/onboarding'

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
  allow_channel_fallback?: boolean
  supported_inputs?: {
    image?: boolean
    video?: boolean
    audio?: boolean
  }
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
  const [profileOptions, setProfileOptions] = useState(BUILTIN_PROFILE_OPTIONS)
  const [debugModel, setDebugModel] = useState<ModelItem | null>(null)
  const categoryWatch = Form.useWatch('category', form)

  const fetchChannels = async () => {
    try {
      const res = await listChannelsAdmin({ page: 1, page_size: 100 })
      setChannelList(res.data || [])
    } catch (e) {
      console.error(e)
    }
  }

  const fetchProfiles = async () => {
    try {
      const res = await listProtocolProfilesAdmin({ page: 1, page_size: 100 })
      if (res.code === 'success' && res.data?.length) {
        const fromApi = res.data.map((p) => ({
          value: p.profile_id,
          label: `${p.name} (${p.profile_id})`,
          mode: p.invocation_mode,
        }))
        const seen = new Set(fromApi.map((x) => x.value))
        setProfileOptions([
          ...fromApi,
          ...BUILTIN_PROFILE_OPTIONS.filter((b) => !seen.has(b.value)),
        ])
      }
    } catch {
      /* builtin fallback */
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
      allow_channel_fallback: true,
      supported_inputs: {
        image: false,
        video: false,
        audio: false,
      },
    })
    setBindings([])
    await Promise.all([fetchChannels(), fetchProfiles()])
    setModalVisible(true)
  }

  const handleEdit = async (record: ModelItem) => {
    setEditingItem(record)
    const inputs = record.supported_inputs && Object.keys(record.supported_inputs).length > 0
      ? record.supported_inputs
      : { image: false, video: false, audio: false }
    form.setFieldsValue({
      model_code: record.model_code,
      model_name: record.model_name,
      category: record.category,
      description: record.description,
      status: record.status || 'online',
      sort_order: record.sort_order || 0,
      is_default: record.is_default || false,
      allow_channel_fallback: record.allow_channel_fallback !== false,
      supported_inputs: inputs,
    })
    setBindings(record.channel_bindings ? [...record.channel_bindings] : [])
    await Promise.all([fetchChannels(), fetchProfiles()])
    setModalVisible(true)
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

  const handleCopy = async (record: ModelItem) => {
    setEditingItem(null)
    form.resetFields()
    const inputs = record.supported_inputs && Object.keys(record.supported_inputs).length > 0
      ? record.supported_inputs
      : { image: false, video: false, audio: false }
    form.setFieldsValue({
      model_code: record.model_code + '_copy',
      model_name: record.model_name + ' (副本)',
      category: record.category,
      description: record.description,
      status: 'offline',
      sort_order: record.sort_order || 0,
      is_default: false,
      allow_channel_fallback: record.allow_channel_fallback !== false,
      supported_inputs: inputs,
    })
    setBindings(record.channel_bindings ? record.channel_bindings.map(b => ({ ...b, status: 'inactive' })) : [])
    await Promise.all([fetchChannels(), fetchProfiles()])
    setModalVisible(true)
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()

      const cleanedBindings = bindings
        .filter((b) => b.channel_code && b.channel_model_id && b.channel_model_id.trim())
        .map((b) => {
          const item: ChannelBinding = {
            channel_code: b.channel_code,
            channel_model_id: b.channel_model_id.trim(),
            priority: typeof b.priority === 'number' ? b.priority : 10,
            status: b.status || 'active',
          }
          if (b.mode_profiles && Object.keys(b.mode_profiles).length > 0) {
            item.mode_profiles = Object.fromEntries(
              Object.entries(b.mode_profiles).filter(([, v]) => v?.trim()),
            )
          }
          if (b.supported_modes?.length) item.supported_modes = b.supported_modes
          if (b.protocol_profile_id) item.protocol_profile_id = b.protocol_profile_id
          if (b.fallback !== undefined) item.fallback = b.fallback
          return item
        })

      const payload: any = {
        model_code: values.model_code,
        model_name: values.model_name,
        category: values.category,
        description: values.description,
        status: values.status,
        sort_order: values.sort_order,
        is_default: values.is_default,
        allow_channel_fallback: values.allow_channel_fallback !== false,
        supported_inputs: {
          image: !!values.supported_inputs?.image,
          video: !!values.supported_inputs?.video,
          audio: !!values.supported_inputs?.audio,
        },
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
      width: 200,
      render: (v, r) => (
        <div>
          <strong>{v}</strong>
          {r.is_default && <Tag color="gold" style={{ marginLeft: 8, fontSize: 10 }}>默认</Tag>}
        </div>
      ),
    },
    {
      title: '编码',
      dataIndex: 'model_code',
      key: 'model_code',
      width: 180,
      render: (v) => <code style={{ background: '#f5f5f5', padding: '2px 6px', borderRadius: 4, fontSize: 12 }}>{v}</code>,
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      width: 80,
      render: (v) => {
        const c = categoryMap[v] || { label: v, color: 'default' }
        return <Tag color={c.color} style={{ fontSize: 12 }}>{c.label}</Tag>
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (v, r) => {
        const s = statusMap[v || 'online'] || { label: v, color: 'default' }
        return (
          <Select
            size="small"
            value={v || 'online'}
            style={{ width: 90 }}
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
      width: 60,
    },
    {
      title: '渠道绑定',
      key: 'bindings',
      width: 120,
      render: (_: any, r: ModelItem) => {
        const list = r.channel_bindings || []
        const count = list.length
        const active = list.filter((b) => b.status === 'active').length
        const withProfiles = list.filter((b) => b.mode_profiles && Object.keys(b.mode_profiles).length > 0).length
        if (count === 0) return <Tag color="red">未绑定</Tag>
        return (
          <Space size={2} wrap>
            <Tag color="green">{active} 启用</Tag>
            {withProfiles > 0 ? (
              <Tag color="blue">{withProfiles} 已配路由</Tag>
            ) : (
              <Tag color="orange">推断路由</Tag>
            )}
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
      width: 260,
      fixed: 'right',
      render: (_, r) => (
        <Space size="small">
          <Tooltip title="调试">
            <Button size="small" icon={<BugOutlined />} onClick={() => setDebugModel(r)} />
          </Tooltip>
          <Tooltip title="查看详情">
            <Button size="small" icon={<EyeOutlined />} onClick={() => setViewItem(r)} />
          </Tooltip>
          <Tooltip title="复制">
            <Button size="small" icon={<CopyOutlined />} onClick={() => handleCopy(r)} />
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
    <div style={{ padding: 24, height: '100%', overflowY: 'auto', boxSizing: 'border-box' }}>
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
          size="small"
          style={{
            border: 'none',
            boxShadow: 'none',
          }}
          pagination={{
            current: page,
            pageSize,
            total,
            size: 'small',
            onChange: (p, ps) => { setPage(p); setPageSize(ps) },
            showSizeChanger: true,
            showQuickJumper: true,
          }}
          scroll={{ x: 1200 }}
        />
      </Card>

      <Modal
        title={editingItem ? '编辑模型' : '新增模型'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={860}
        okText="保存"
        cancelText="取消"
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          {/* 基本信息 */}
          <Card size="small" title="基本信息" style={{ marginBottom: 12 }}>
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
            <Form.Item name="is_default" label="设为该分类默认模型" valuePropName="checked">
              <Switch />
            </Form.Item>
          </Card>

          {/* 输入类型 */}
          <Card size="small" title="支持的输入类型" style={{ marginBottom: 12 }}>
            <Form.Item label="可选输入类型" style={{ marginBottom: 0 }}>
              <Space wrap>
                <Form.Item name={['supported_inputs', 'image']} valuePropName="checked" noStyle>
                  <Switch checkedChildren="图片" unCheckedChildren="图片" />
                </Form.Item>
                <Form.Item name={['supported_inputs', 'video']} valuePropName="checked" noStyle>
                  <Switch checkedChildren="视频" unCheckedChildren="视频" />
                </Form.Item>
                <Form.Item name={['supported_inputs', 'audio']} valuePropName="checked" noStyle>
                  <Switch checkedChildren="音频" unCheckedChildren="音频" />
                </Form.Item>
              </Space>
            </Form.Item>
          </Card>

          {/* 渠道绑定 */}
          <Card size="small" title="渠道绑定与协议路由" style={{ marginBottom: 12 }}>
            <Form.Item
              name="allow_channel_fallback"
              label="渠道降级"
              valuePropName="checked"
              tooltip="开启后，主渠道（最高 priority）失败时自动尝试下一个绑定渠道"
              style={{ marginBottom: 12 }}
            >
              <Switch checkedChildren="允许降级" unCheckedChildren="禁止降级" />
            </Form.Item>
            <ChannelBindingEditor
              bindings={bindings}
              channelList={channelList}
              profileOptions={profileOptions}
              category={(categoryWatch || form.getFieldValue('category') || 'text') as 'text' | 'image' | 'video'}
              onChange={setBindings}
            />
          </Card>
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

            {viewItem.supported_inputs && (
              <div style={{ marginBottom: 16 }}>
                <div style={{ color: '#888', fontSize: 12, marginBottom: 4 }}>支持上传类型</div>
                <Space wrap>
                  {viewItem.supported_inputs.image && <Tag color="green">图片</Tag>}
                  {viewItem.supported_inputs.video && <Tag color="purple">视频</Tag>}
                  {viewItem.supported_inputs.audio && <Tag color="blue">音频</Tag>}
                  {(!viewItem.supported_inputs.image && !viewItem.supported_inputs.video && !viewItem.supported_inputs.audio) && (
                    <Tag color="default">仅文本</Tag>
                  )}
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
                <div style={{ marginBottom: 8, fontSize: 13 }}>
                  渠道降级：
                  <Tag color={viewItem.allow_channel_fallback !== false ? 'green' : 'orange'}>
                    {viewItem.allow_channel_fallback !== false ? '允许（默认）' : '禁止'}
                  </Tag>
                </div>
                {viewItem.channel_bindings.map((cb: ChannelBinding, i: number) => (
                  <Card key={i} size="small" style={{ marginBottom: 8 }}>
                    <Row gutter={8}>
                      <Col span={8}><code>{cb.channel_code}</code></Col>
                      <Col span={8}>模型ID: {cb.channel_model_id}</Col>
                      <Col span={4}>优先级: {cb.priority}</Col>
                      <Col span={4}>{cb.status}</Col>
                    </Row>
                    {cb.mode_profiles && Object.keys(cb.mode_profiles).length > 0 && (
                      <div style={{ marginTop: 8, fontSize: 12 }}>
                        {Object.entries(cb.mode_profiles).map(([mode, pid]) => (
                          <div key={mode}>
                            <Tag>{mode}</Tag> → <code>{pid}</code>
                          </div>
                        ))}
                      </div>
                    )}
                  </Card>
                ))}
              </>
            )}
          </div>
        )}
      </Modal>
      <IntegrationDebugDrawer
        open={!!debugModel}
        onClose={() => setDebugModel(null)}
        perspective="model"
        model={debugModel}
      />
    </div>
  )
}
