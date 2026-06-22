import { useEffect, useState } from 'react'
import { Button, Form, Input, Modal, Popconfirm, Select, Space, Table, Tag, message } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { DeleteOutlined, EditOutlined, PlusOutlined } from '@ant-design/icons'
import {
  createKnowledgeCategory,
  deleteKnowledgeCategory,
  listKnowledgeCategories,
  listKnowledgeStages,
  updateKnowledgeCategory,
  type CreationStageOption,
  type KnowledgeCategory,
} from '@/api/dramaKnowledge'
import { extractApiErrorMessage } from '@/utils/apiError'

interface KnowledgeCategoryManageModalProps {
  open: boolean
  onClose: () => void
  onChanged: () => void
}

type EditorMode = 'create' | 'edit'

type CategoryFormValues = {
  code: string
  name: string
  description?: string
  applicable_stages?: string[]
}

export default function KnowledgeCategoryManageModal({
  open,
  onClose,
  onChanged,
}: KnowledgeCategoryManageModalProps) {
  const [loading, setLoading] = useState(false)
  const [categories, setCategories] = useState<KnowledgeCategory[]>([])
  const [stageOptions, setStageOptions] = useState<CreationStageOption[]>([])
  const [editorOpen, setEditorOpen] = useState(false)
  const [editorMode, setEditorMode] = useState<EditorMode>('create')
  const [editingCode, setEditingCode] = useState<string>()
  const [saving, setSaving] = useState(false)
  const [form] = Form.useForm<CategoryFormValues>()

  const stageLabelMap = Object.fromEntries(stageOptions.map((s) => [s.stage, s.label]))

  const load = async () => {
    setLoading(true)
    try {
      const [catRes, stageRes] = await Promise.all([
        listKnowledgeCategories(),
        listKnowledgeStages(),
      ])
      setCategories((catRes.data as KnowledgeCategory[]) || [])
      setStageOptions((stageRes.data as CreationStageOption[]) || [])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (open) load()
  }, [open])

  const openCreate = () => {
    setEditorMode('create')
    setEditingCode(undefined)
    form.resetFields()
    setEditorOpen(true)
  }

  const openEdit = (cat: KnowledgeCategory) => {
    setEditorMode('edit')
    setEditingCode(cat.code)
    form.setFieldsValue({
      code: cat.code,
      name: cat.name,
      description: cat.description || '',
      applicable_stages: cat.applicable_stages || [],
    })
    setEditorOpen(true)
  }

  const handleSave = async () => {
    const values = await form.validateFields()
    setSaving(true)
    try {
      if (editorMode === 'create') {
        await createKnowledgeCategory({
          code: values.code.trim(),
          name: values.name.trim(),
          description: values.description?.trim() || '',
          applicable_stages: values.applicable_stages || [],
        })
        message.success('分类已创建')
      } else if (editingCode) {
        await updateKnowledgeCategory(editingCode, {
          name: values.name.trim(),
          description: values.description?.trim() || '',
          applicable_stages: values.applicable_stages || [],
        })
        message.success('分类已更新')
      }
      setEditorOpen(false)
      await load()
      onChanged()
    } catch (e) {
      message.error(extractApiErrorMessage(e, '保存失败'))
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (code: string) => {
    try {
      await deleteKnowledgeCategory(code)
      message.success('分类已删除')
      await load()
      onChanged()
    } catch (e) {
      message.error(extractApiErrorMessage(e, '删除失败'))
    }
  }

  const columns: ColumnsType<KnowledgeCategory> = [
    {
      title: '名称',
      dataIndex: 'name',
      width: 120,
    },
    {
      title: 'Code',
      dataIndex: 'code',
      width: 140,
      render: (code) => <Tag>{code}</Tag>,
    },
    {
      title: '适用阶段',
      dataIndex: 'applicable_stages',
      width: 200,
      render: (stages?: string[]) => {
        if (!stages?.length) {
          return <Tag color="default">全阶段</Tag>
        }
        return (
          <Space size={[0, 4]} wrap>
            {stages.map((s) => (
              <Tag key={s} color="purple">{stageLabelMap[s] || s}</Tag>
            ))}
          </Space>
        )
      },
    },
    {
      title: '说明',
      dataIndex: 'description',
      ellipsis: true,
    },
    {
      title: '条目',
      dataIndex: 'entry_count',
      width: 72,
      align: 'center',
      render: (n) => n ?? 0,
    },
    {
      title: '类型',
      width: 88,
      render: (_, r) =>
        r.builtin ? <Tag color="blue">内置</Tag> : <Tag color="default">自定义</Tag>,
    },
    {
      title: '操作',
      width: 120,
      render: (_, r) => (
        <Space size={4}>
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => openEdit(r)}>
            编辑
          </Button>
          <Popconfirm
            title="确定删除该分类？"
            description={
              (r.entry_count || 0) > 0
                ? `该分类下有 ${r.entry_count} 条知识，无法删除`
                : '删除后不可恢复'
            }
            disabled={(r.entry_count || 0) > 0}
            onConfirm={() => void handleDelete(r.code)}
          >
            <Button
              type="link"
              size="small"
              danger
              icon={<DeleteOutlined />}
              disabled={(r.entry_count || 0) > 0}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <>
      <Modal
        title="管理知识分类"
        open={open}
        onCancel={onClose}
        width={900}
        footer={null}
        destroyOnClose
        className="knowledge-category-manage-modal"
      >
        <div className="knowledge-category-manage-modal__toolbar">
          <span className="knowledge-category-manage-modal__hint">
            分类可配置适用创作阶段；创作助手检索时仅命中当前阶段适用的分类。未配置适用阶段视为全阶段可用。
          </span>
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
            新增分类
          </Button>
        </div>
        <Table
          rowKey="code"
          size="small"
          loading={loading}
          columns={columns}
          dataSource={categories}
          pagination={false}
          scroll={{ y: 360 }}
        />
      </Modal>

      <Modal
        title={editorMode === 'create' ? '新增知识分类' : '编辑知识分类'}
        open={editorOpen}
        onCancel={() => setEditorOpen(false)}
        onOk={() => void handleSave()}
        confirmLoading={saving}
        destroyOnClose
        width={520}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="code"
            label="分类 Code"
            rules={[
              { required: true, message: '请输入 code' },
              {
                pattern: /^[a-z][a-z0-9_]{0,47}$/,
                message: '小写字母开头，仅含字母、数字、下划线',
              },
            ]}
          >
            <Input
              placeholder="如 animation_short"
              disabled={editorMode === 'edit'}
            />
          </Form.Item>
          <Form.Item
            name="name"
            label="显示名称"
            rules={[{ required: true, message: '请输入名称' }]}
          >
            <Input placeholder="如 动画短片" />
          </Form.Item>
          <Form.Item
            name="applicable_stages"
            label="适用创作阶段"
            tooltip="多选；不选表示全阶段适用"
          >
            <Select
              mode="multiple"
              allowClear
              placeholder="选择适用的创作阶段（可多选）"
              options={stageOptions.map((s) => ({ value: s.stage, label: s.label }))}
            />
          </Form.Item>
          <Form.Item name="description" label="说明">
            <Input.TextArea rows={3} placeholder="该分类适用的知识范围（可选）" />
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}
