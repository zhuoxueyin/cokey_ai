import { useEffect, useState } from 'react'
import {
  Alert,
  Button,
  Card,
  Drawer,
  Form,
  Input,
  Popconfirm,
  Segmented,
  Space,
  Table,
  Tag,
  Typography,
  message,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { DeleteOutlined, EditOutlined, PlusOutlined, ReloadOutlined } from '@ant-design/icons'
import {
  createDramaStyleAdmin,
  deleteDramaStyleAdmin,
  getDramaStyleAdmin,
  listDramaStylesAdmin,
  publishDramaStyle,
  updateDramaStyleAdmin,
} from '@/api/drama'
import StyleFormFields, { STYLE_EDIT_PANEL_WIDTH, styleFormToPayload, styleToFormValues } from '@/components/drama/StyleFormFields'
import type { DramaRenderClass, DramaStylePreset } from '@/types/drama'
import { RENDER_CLASS_LABELS, RENDER_CLASS_TABS } from '@/types/drama'

export default function DramaStyleAdmin() {
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<DramaStylePreset[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(50)
  const [renderClass, setRenderClass] = useState<string>('all')
  const [keyword, setKeyword] = useState('')
  const [statusFilter, setStatusFilter] = useState<string | undefined>()
  const [editOpen, setEditOpen] = useState(false)
  const [editLoading, setEditLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [creating, setCreating] = useState(false)
  const [editingStyle, setEditingStyle] = useState<DramaStylePreset | null>(null)
  const [form] = Form.useForm()

  const fetchData = async () => {
    setLoading(true)
    try {
      const tab = RENDER_CLASS_TABS.find((t) => t.key === renderClass)
      const res = await listDramaStylesAdmin({
        page,
        page_size: pageSize,
        render_class: tab?.value,
        status: statusFilter,
        keyword: keyword || undefined,
      })
      setData((res.data as DramaStylePreset[]) || [])
      setTotal(res.total || 0)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [page, pageSize, renderClass, statusFilter])

  const handlePublish = async (styleId: string) => {
    try {
      await publishDramaStyle(styleId)
      message.success('已发布')
      fetchData()
    } catch {
      /* request 层已提示 */
    }
  }

  const openCreate = () => {
    setCreating(true)
    setEditingStyle(null)
    form.resetFields()
    form.setFieldsValue({ render_class: 'live_action' })
    setEditOpen(true)
  }

  const openEdit = async (styleId: string) => {
    setCreating(false)
    setEditOpen(true)
    setEditLoading(true)
    setEditingStyle(null)
    form.resetFields()
    try {
      const res = await getDramaStyleAdmin(styleId)
      const style = res.data as DramaStylePreset
      if (!style) {
        message.error('风格不存在')
        setEditOpen(false)
        return
      }
      setEditingStyle(style)
      form.setFieldsValue(styleToFormValues(style))
    } finally {
      setEditLoading(false)
    }
  }

  const handleSave = async () => {
    try {
      const values = await form.validateFields()
      const payload = styleFormToPayload(values)
      setSaving(true)
      if (creating) {
        await createDramaStyleAdmin({ ...payload, publish: false })
        message.success('已创建（draft），可在列表中发布')
      } else if (editingStyle) {
        await updateDramaStyleAdmin(editingStyle.style_id, payload)
        message.success('已保存')
      }
      setEditOpen(false)
      fetchData()
    } catch {
      /* 校验或请求失败 */
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (styleId: string) => {
    try {
      await deleteDramaStyleAdmin(styleId)
      message.success('已删除')
      if (editingStyle?.style_id === styleId) {
        setEditOpen(false)
        setEditingStyle(null)
      }
      fetchData()
    } catch (e: unknown) {
      message.error((e as { message?: string })?.message || '删除失败')
    }
  }

  const columns: ColumnsType<DramaStylePreset> = [
    {
      title: 'style_id',
      dataIndex: 'style_id',
      width: 220,
      render: (v) => <code style={{ fontSize: 11 }}>{v}</code>,
    },
    { title: '名称', dataIndex: 'name', ellipsis: true },
    {
      title: '分类',
      dataIndex: 'render_class',
      width: 80,
      render: (v: DramaRenderClass) => <Tag>{RENDER_CLASS_LABELS[v] || v}</Tag>,
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 90,
      render: (v) => (
        <Tag color={v === 'published' ? 'green' : v === 'draft' ? 'orange' : 'default'}>{v}</Tag>
      ),
    },
    {
      title: '来源',
      dataIndex: 'origin',
      width: 80,
      render: (v) => (v === 'seed' ? <Tag color="blue">历史导入</Tag> : <Tag>{v || 'manual'}</Tag>),
    },
    {
      title: '操作',
      key: 'actions',
      width: 200,
      render: (_, r) => (
        <Space size="small">
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => openEdit(r.style_id)}>
            编辑
          </Button>
          {r.status !== 'published' ? (
            <Button type="link" size="small" onClick={() => handlePublish(r.style_id)}>
              发布
            </Button>
          ) : null}
          <Popconfirm
            title="删除此风格？"
            description="软删除后不可恢复。"
            okText="删除"
            cancelText="取消"
            okButtonProps={{ danger: true }}
            onConfirm={() => handleDelete(r.style_id)}
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div className="admin-page">
      <Card
        title="风格运营（管理端）"
        extra={
          <Space>
            <Button icon={<ReloadOutlined />} onClick={fetchData}>
              刷新
            </Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
              新建风格
            </Button>
          </Space>
        }
      >
        <Alert
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
          message="风格广场为唯一数据源"
          description={
            <>
              在此或用户端「风格广场」新增、编辑风格；数据写入 MongoDB，供创作助手与生图/生视频使用。
              编辑项：名称、封面图、渲染类型、标签、风格描述（Markdown 八段），保存后自动解析为 model_prompts / visual。
            </>
          }
        />
        <Space wrap style={{ marginBottom: 16 }}>
          <Segmented
            options={RENDER_CLASS_TABS.map((t) => ({ label: t.label, value: t.key }))}
            value={renderClass}
            onChange={(v) => {
              setRenderClass(v as string)
              setPage(1)
            }}
          />
          <Input.Search
            placeholder="搜索名称 / style_id"
            allowClear
            style={{ width: 240 }}
            onSearch={(v) => {
              setKeyword(v)
              setPage(1)
              fetchData()
            }}
          />
          <Segmented
            options={[
              { label: '全部状态', value: '' },
              { label: 'draft', value: 'draft' },
              { label: 'published', value: 'published' },
            ]}
            value={statusFilter ?? ''}
            onChange={(v) => setStatusFilter(v ? (v as string) : undefined)}
          />
        </Space>
        <Typography.Text type="secondary">共 {total} 条</Typography.Text>
        <Table
          rowKey="style_id"
          loading={loading}
          columns={columns}
          dataSource={data}
          style={{ marginTop: 12 }}
          pagination={{
            current: page,
            pageSize,
            total,
            showSizeChanger: true,
            onChange: (p, ps) => {
              setPage(p)
              setPageSize(ps)
            },
          }}
        />
      </Card>

      <Drawer
        title={creating ? '新建风格' : editingStyle ? `编辑风格 · ${editingStyle.name}` : '编辑风格'}
        width={STYLE_EDIT_PANEL_WIDTH}
        open={editOpen}
        onClose={() => setEditOpen(false)}
        destroyOnClose
        styles={{ body: { paddingBottom: 24, maxHeight: 'calc(100vh - 120px)', overflowY: 'auto' } }}
        extra={
          <Space>
            <Button onClick={() => setEditOpen(false)}>取消</Button>
            <Button type="primary" loading={saving} onClick={() => void handleSave()}>
              保存
            </Button>
          </Space>
        }
      >
        {editLoading ? (
          <Typography.Text type="secondary">加载中…</Typography.Text>
        ) : (
          <Form form={form} layout="vertical">
            {editingStyle && (
              <Typography.Paragraph type="secondary" style={{ fontSize: 12 }}>
                style_id: <code>{editingStyle.style_id}</code>
              </Typography.Paragraph>
            )}
            <StyleFormFields form={form} />
          </Form>
        )}
      </Drawer>
    </div>
  )
}
