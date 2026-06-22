import { useEffect, useState } from 'react'
import {
  Button,
  Empty,
  Form,
  Input,
  Modal,
  Popconfirm,
  Space,
  Tag,
  Typography,
  message,
} from 'antd'
import { PlusOutlined, DeleteOutlined, EditOutlined, ReloadOutlined } from '@ant-design/icons'
import {
  createUserStyle,
  deleteUserStyle,
  getDramaStyle,
  listDramaStylesUser,
  updateUserStyle,
} from '@/api/drama'
import StyleFormFields, { STYLE_EDIT_PANEL_WIDTH, styleFormToPayload, styleToFormValues } from '@/components/drama/StyleFormFields'
import StylePlazaDetailDrawer from '@/components/drama/StylePlazaDetailDrawer'
import type { DramaStylePreset } from '@/types/drama'
import { RENDER_CLASS_LABELS, RENDER_CLASS_TABS } from '@/types/drama'
import { getStyleDisplayTags, getStyleSummary } from '@/utils/styleDisplay'
import { resolveStylePreview } from '@/utils/stylePreview'

export default function StylePlazaPage() {
  const [loading, setLoading] = useState(false)
  const [styles, setStyles] = useState<DramaStylePreset[]>([])
  const [renderClass, setRenderClass] = useState('all')
  const [keyword, setKeyword] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [detailOpen, setDetailOpen] = useState(false)
  const [detailLoading, setDetailLoading] = useState(false)
  const [detailStyle, setDetailStyle] = useState<DramaStylePreset | null>(null)
  const [editingStyle, setEditingStyle] = useState<DramaStylePreset | null>(null)
  const [form] = Form.useForm()

  const load = async () => {
    setLoading(true)
    try {
      const tab = RENDER_CLASS_TABS.find((t) => t.key === renderClass)
      const res = await listDramaStylesUser({
        page: 1,
        page_size: 200,
        render_class: tab?.value,
        keyword: keyword || undefined,
      })
      setStyles((res.data as DramaStylePreset[]) || [])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [renderClass, keyword])

  const openCreate = () => {
    setEditingId(null)
    setEditingStyle(null)
    form.resetFields()
    form.setFieldsValue({ render_class: 'live_action' })
    setModalOpen(true)
  }

  const openEdit = async (styleId: string) => {
    const res = await getDramaStyle(styleId)
    const style = res.data as DramaStylePreset
    if (!style) return
    setEditingId(styleId)
    setEditingStyle(style)
    form.setFieldsValue(styleToFormValues(style))
    setDetailOpen(false)
    setModalOpen(true)
  }

  const openDetail = async (styleId: string) => {
    setDetailOpen(true)
    setDetailLoading(true)
    setDetailStyle(null)
    try {
      const res = await getDramaStyle(styleId)
      setDetailStyle((res.data as DramaStylePreset) || null)
    } finally {
      setDetailLoading(false)
    }
  }

  const handleSubmit = async () => {
    const values = await form.validateFields()
    const payload = styleFormToPayload(values)
    if (editingId) {
      await updateUserStyle(editingId, payload)
      message.success('已保存')
    } else {
      await createUserStyle({ ...payload, publish: true })
      message.success('已创建')
    }
    setModalOpen(false)
    load()
    if (detailOpen && editingId) {
      openDetail(editingId)
    }
  }

  const handleDelete = async (styleId: string) => {
    try {
      await deleteUserStyle(styleId)
      message.success('已删除')
      setModalOpen(false)
      setEditingId(null)
      setEditingStyle(null)
      setDetailOpen(false)
      setDetailStyle(null)
      load()
    } catch (e: unknown) {
      message.error((e as { message?: string })?.message || '删除失败')
      throw e
    }
  }

  return (
    <div className="style-plaza-page">
      <div className="style-plaza-page__header">
        <Typography.Title level={3} style={{ margin: 0 }}>
          风格广场
        </Typography.Title>
        <Space>
          <Input.Search
            placeholder="搜索"
            allowClear
            onSearch={setKeyword}
            style={{ width: 200 }}
          />
          <Button icon={<ReloadOutlined />} onClick={load} loading={loading}>
            刷新
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
            新建
          </Button>
        </Space>
      </div>

      <Space wrap style={{ marginBottom: 16 }}>
        {RENDER_CLASS_TABS.map((t) => (
          <Button
            key={t.key}
            type={renderClass === t.key ? 'primary' : 'default'}
            size="small"
            onClick={() => setRenderClass(t.key)}
          >
            {t.label}
          </Button>
        ))}
      </Space>

      {styles.length === 0 ? (
        <Empty description="暂无风格" />
      ) : (
        <div className="style-plaza-grid">
          {styles.map((s) => {
            const preview = resolveStylePreview(s)
            const summary = getStyleSummary(s)
            return (
              <div key={s.style_id} className="style-plaza-grid__card-wrap">
                <button
                  type="button"
                  className="style-plaza-grid__card"
                  onClick={() => openDetail(s.style_id)}
                >
                  <div className="style-plaza-grid__thumb">
                    {preview.coverUrl ? (
                      <img src={preview.coverUrl} alt="" className="style-cover-img" />
                    ) : (
                      <div
                        className="style-plaza-grid__thumb-fallback"
                        style={{ background: preview.gradient }}
                      />
                    )}
                  </div>
                  <div className="style-plaza-grid__body">
                    <div className="style-plaza-grid__name">{s.name}</div>
                    {summary && (
                      <div className="style-plaza-grid__summary" title={summary}>
                        {summary}
                      </div>
                    )}
                    <Space size={4} wrap>
                      <Tag>{RENDER_CLASS_LABELS[s.render_class]}</Tag>
                      {getStyleDisplayTags(s, 3).map((t) => (
                        <Tag key={t}>{t}</Tag>
                      ))}
                    </Space>
                  </div>
                </button>
                <Space className="style-plaza-grid__actions" size={4}>
                  <Button
                    type="text"
                    size="small"
                    icon={<EditOutlined />}
                    aria-label="编辑"
                    onClick={(e) => {
                      e.stopPropagation()
                      void openEdit(s.style_id)
                    }}
                  />
                  <Popconfirm
                    title="删除此风格？"
                    description="软删除后不可恢复。"
                    okText="删除"
                    cancelText="取消"
                    okButtonProps={{ danger: true }}
                    onConfirm={() => handleDelete(s.style_id)}
                  >
                    <Button
                      type="text"
                      size="small"
                      danger
                      icon={<DeleteOutlined />}
                      aria-label="删除"
                      onClick={(e) => e.stopPropagation()}
                    />
                  </Popconfirm>
                </Space>
              </div>
            )
          })}
        </div>
      )}

      <StylePlazaDetailDrawer
        open={detailOpen}
        style={detailStyle}
        loading={detailLoading}
        onClose={() => setDetailOpen(false)}
        onEdit={openEdit}
        onDelete={handleDelete}
      />

      <Modal
        title={editingId ? '编辑风格' : '新建风格'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        width={STYLE_EDIT_PANEL_WIDTH}
        destroyOnClose
        styles={{ body: { maxHeight: 'calc(100vh - 220px)', overflowY: 'auto' } }}
        footer={
          <div className="style-plaza-modal-footer">
            {editingId && editingStyle && !editingStyle.immutable && (
                <Popconfirm
                  title="删除此风格？"
                  description="软删除后不可恢复。"
                  okText="删除"
                  cancelText="取消"
                  okButtonProps={{ danger: true }}
                  onConfirm={() => handleDelete(editingId)}
                >
                  <Button danger icon={<DeleteOutlined />}>
                    删除
                  </Button>
                </Popconfirm>
              )}
            <Space>
              <Button onClick={() => setModalOpen(false)}>取消</Button>
              <Button type="primary" onClick={() => void handleSubmit()}>
                保存
              </Button>
            </Space>
          </div>
        }
      >
        <Form form={form} layout="vertical">
          <StyleFormFields form={form} />
        </Form>
      </Modal>
    </div>
  )
}
