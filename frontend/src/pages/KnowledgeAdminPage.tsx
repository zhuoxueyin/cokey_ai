import { useEffect, useMemo, useState } from 'react'
import {
  Button,
  Empty,
  Input,
  Popconfirm,
  Space,
  Table,
  Tag,
  Typography,
  message,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  BookOutlined,
  DeleteOutlined,
  EditOutlined,
  FolderOpenOutlined,
  PlusOutlined,
  ReloadOutlined,
  SearchOutlined,
  SendOutlined,
} from '@ant-design/icons'
import {
  deleteKnowledgeAdmin,
  reindexKnowledgeVectors,
  listKnowledgeAdmin,
  listKnowledgeCategories,
  publishKnowledgeAdmin,
  type KnowledgeCategory,
  type KnowledgeEntry,
} from '@/api/dramaKnowledge'
import KnowledgeEditorDrawer from '@/components/knowledge/KnowledgeEditorDrawer'
import KnowledgeCategoryManageModal from '@/components/knowledge/KnowledgeCategoryManageModal'
import { extractApiErrorMessage } from '@/utils/apiError'

const { Title, Text, Paragraph } = Typography

export default function KnowledgeAdminPage() {
  const [loading, setLoading] = useState(false)
  const [categories, setCategories] = useState<KnowledgeCategory[]>([])
  const [data, setData] = useState<KnowledgeEntry[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [activeCategory, setActiveCategory] = useState<string>('')
  const [keyword, setKeyword] = useState('')
  const [editorOpen, setEditorOpen] = useState(false)
  const [categoryManageOpen, setCategoryManageOpen] = useState(false)
  const [reindexing, setReindexing] = useState(false)
  const [editorMode, setEditorMode] = useState<'create' | 'edit'>('create')
  const [editingId, setEditingId] = useState<string>()

  const categoryMap = useMemo(
    () => Object.fromEntries(categories.map((c) => [c.code, c.name])),
    [categories],
  )

  const loadCategories = async () => {
    const res = await listKnowledgeCategories()
    setCategories((res.data as KnowledgeCategory[]) || [])
  }

  const load = async () => {
    setLoading(true)
    try {
      const res = await listKnowledgeAdmin({
        page,
        page_size: 20,
        category: activeCategory || undefined,
        keyword: keyword || undefined,
      })
      setData((res.data as KnowledgeEntry[]) || [])
      setTotal(res.total || 0)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadCategories()
  }, [])

  useEffect(() => {
    load()
  }, [page, activeCategory])

  const handleReindexVectors = async () => {
    setReindexing(true)
    try {
      const res = await reindexKnowledgeVectors()
      message.success(`向量索引已重建：${res.data?.reindexed ?? 0} 条`)
    } catch (e) {
      message.error(extractApiErrorMessage(e, '向量索引重建失败'))
    } finally {
      setReindexing(false)
    }
  }

  const openCreate = () => {
    setEditorMode('create')
    setEditingId(undefined)
    setEditorOpen(true)
  }

  const openEdit = (entryId: string) => {
    setEditorMode('edit')
    setEditingId(entryId)
    setEditorOpen(true)
  }

  const columns: ColumnsType<KnowledgeEntry> = [
    {
      title: '标题',
      dataIndex: 'title',
      ellipsis: true,
      render: (title, r) => (
        <div>
          <div className="knowledge-hub__title-cell">{title}</div>
          {r.summary && (
            <Text type="secondary" className="knowledge-hub__summary-cell">
              {r.summary}
            </Text>
          )}
        </div>
      ),
    },
    {
      title: '分类',
      dataIndex: 'category',
      width: 120,
      render: (v) => <Tag>{categoryMap[v] || v}</Tag>,
    },
    {
      title: '来源',
      width: 100,
      render: (_, r) => {
        const t = r.source?.type || 'manual'
        const map: Record<string, string> = {
          manual: '在线',
          file: '文件',
          feishu: '飞书',
        }
        return <Tag color="default">{map[t] || t}</Tag>
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      render: (v) => (
        <Tag color={v === 'published' ? 'green' : v === 'draft' ? 'gold' : 'default'}>{v}</Tag>
      ),
    },
    {
      title: '操作',
      width: 200,
      render: (_, r) => (
        <Space size={4}>
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => openEdit(r.entry_id)}>
            编辑
          </Button>
          {r.status !== 'published' && (
            <Button
              type="link"
              size="small"
              icon={<SendOutlined />}
              onClick={() =>
                publishKnowledgeAdmin(r.entry_id).then(() => {
                  message.success('已发布')
                  load()
                })
              }
            >
              发布
            </Button>
          )}
          <Popconfirm title="确定删除？" onConfirm={() => deleteKnowledgeAdmin(r.entry_id).then(load)}>
            <Button type="link" size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div className="knowledge-hub">
      <div className="knowledge-hub__hero">
        <div>
          <Title level={3} className="knowledge-hub__hero-title">
            <BookOutlined /> 专业知识库
          </Title>
          <Paragraph type="secondary" className="knowledge-hub__hero-desc">
            按影视/AIGC 专业域组织知识，支持 Markdown 在线编写、本地文件与飞书链接导入，供创作助手 RAG 检索。
          </Paragraph>
        </div>
        <Space>
          <Button loading={reindexing} onClick={() => void handleReindexVectors()}>
            重建向量索引
          </Button>
          <Button icon={<ReloadOutlined />} onClick={load}>
            刷新
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
            新建知识
          </Button>
        </Space>
      </div>

      <div className="knowledge-hub__layout">
        <aside className="knowledge-hub__sidebar">
          <div className="knowledge-hub__sidebar-head">
            <div className="knowledge-hub__sidebar-title">知识分类</div>
            <Button
              type="link"
              size="small"
              icon={<FolderOpenOutlined />}
              className="knowledge-hub__sidebar-manage"
              onClick={() => setCategoryManageOpen(true)}
            >
              管理
            </Button>
          </div>
          <button
            type="button"
            className={`knowledge-hub__cat${activeCategory === '' ? ' knowledge-hub__cat--active' : ''}`}
            onClick={() => {
              setActiveCategory('')
              setPage(1)
            }}
          >
            全部分类
          </button>
          {categories.map((c) => (
            <button
              key={c.code}
              type="button"
              className={`knowledge-hub__cat${
                activeCategory === c.code ? ' knowledge-hub__cat--active' : ''
              }`}
              onClick={() => {
                setActiveCategory(c.code)
                setPage(1)
              }}
            >
              <span>{c.name}</span>
              {c.description && (
                <Text type="secondary" className="knowledge-hub__cat-desc">
                  {c.description}
                </Text>
              )}
              <Text type="secondary" className="knowledge-hub__cat-code">
                {c.code}
              </Text>
            </button>
          ))}
        </aside>

        <main className="knowledge-hub__main">
          <div className="knowledge-hub__toolbar">
            <Input
              prefix={<SearchOutlined />}
              placeholder="搜索标题 / 摘要 / ID"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              onPressEnter={() => {
                setPage(1)
                load()
              }}
              allowClear
              style={{ maxWidth: 360 }}
            />
            <Button onClick={() => { setPage(1); load() }}>搜索</Button>
          </div>

          {data.length === 0 && !loading ? (
            <Empty description="暂无知识条目" className="knowledge-hub__empty">
              <Button type="primary" onClick={openCreate}>
                创建第一条知识
              </Button>
            </Empty>
          ) : (
            <Table
              rowKey="entry_id"
              loading={loading}
              columns={columns}
              dataSource={data}
              pagination={{
                current: page,
                total,
                pageSize: 20,
                onChange: setPage,
                showTotal: (t) => `共 ${t} 条`,
              }}
            />
          )}
        </main>
      </div>

      <KnowledgeEditorDrawer
        open={editorOpen}
        mode={editorMode}
        entryId={editingId}
        defaultCategory={activeCategory}
        categories={categories}
        onClose={() => setEditorOpen(false)}
        onSaved={load}
      />

      <KnowledgeCategoryManageModal
        open={categoryManageOpen}
        onClose={() => setCategoryManageOpen(false)}
        onChanged={async () => {
          const res = await listKnowledgeCategories()
          const next = (res.data as KnowledgeCategory[]) || []
          setCategories(next)
          if (activeCategory && !next.some((c) => c.code === activeCategory)) {
            setActiveCategory('')
            setPage(1)
          }
          load()
        }}
      />
    </div>
  )
}
