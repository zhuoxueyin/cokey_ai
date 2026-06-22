import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Button,
  Card,
  Empty,
  Form,
  Input,
  List,
  Modal,
  Select,
  Space,
  Tag,
  Typography,
  message,
} from 'antd'
import { PlusOutlined, RocketOutlined } from '@ant-design/icons'
import {
  createDramaProject,
  dramaProjectChat,
  listDramaProjects,
  listDramaStylesUser,
} from '@/api/drama'
import type { DramaProject, DramaStylePreset } from '@/types/drama'
import { RENDER_CLASS_LABELS, RENDER_CLASS_TABS } from '@/types/drama'

export default function DramaProjectHome() {
  const [projects, setProjects] = useState<DramaProject[]>([])
  const [styles, setStyles] = useState<DramaStylePreset[]>([])
  const [loading, setLoading] = useState(false)
  const [createOpen, setCreateOpen] = useState(false)
  const [renderClass, setRenderClass] = useState<string>('all')
  const [chatProject, setChatProject] = useState<DramaProject | null>(null)
  const [chatReply, setChatReply] = useState('')
  const [chatLoading, setChatLoading] = useState(false)
  const [form] = Form.useForm()

  const load = async () => {
    setLoading(true)
    try {
      const [pRes, sRes] = await Promise.all([
        listDramaProjects({ page: 1, page_size: 50 }),
        listDramaStylesUser({
          page: 1,
          page_size: 100,
          render_class: RENDER_CLASS_TABS.find((t) => t.key === renderClass)?.value,
        }),
      ])
      setProjects((pRes.data as DramaProject[]) || [])
      setStyles((sRes.data as DramaStylePreset[]) || [])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [renderClass])

  const handleCreate = async () => {
    const values = await form.validateFields()
    const res = await createDramaProject(values)
    message.success('项目已创建')
    setCreateOpen(false)
    form.resetFields()
    await load()
    if (res.data) setChatProject(res.data as DramaProject)
  }

  const handleChat = async (msg: string) => {
    if (!chatProject) return
    setChatLoading(true)
    try {
      const res = await dramaProjectChat(chatProject.project_id, { message: msg })
      setChatReply(String((res.data as { reply_markdown?: string })?.reply_markdown || ''))
    } finally {
      setChatLoading(false)
    }
  }

  return (
    <div style={{ padding: 24, maxWidth: 1200, margin: '0 auto' }}>
      <Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: 16 }}>
        <Typography.Title level={3} style={{ margin: 0 }}>
          <RocketOutlined /> 短剧创作
        </Typography.Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
          新建项目
        </Button>
      </Space>

      <Card title="我的项目" loading={loading} style={{ marginBottom: 24 }}>
        {projects.length === 0 ? (
          <Empty description="暂无项目" />
        ) : (
          <List
            dataSource={projects}
            renderItem={(item) => (
              <List.Item
                actions={[
                  <Button type="link" key="chat" onClick={() => setChatProject(item)}>
                    导演对话
                  </Button>,
                ]}
              >
                <List.Item.Meta
                  title={item.title}
                  description={
                    <Space>
                      <Tag>{item.stage}</Tag>
                      {item.style_preset_id && <Tag color="purple">{item.style_preset_id}</Tag>}
                    </Space>
                  }
                />
              </List.Item>
            )}
          />
        )}
      </Card>

      <Card
        title="风格库"
        extra={
          <Link to="/admin/drama/styles">管理端</Link>
        }
      >
        <Space style={{ marginBottom: 16 }}>
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
          <Empty description="暂无已发布风格，请先在管理端导入并发布" />
        ) : (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))',
              gap: 12,
            }}
          >
            {styles.map((s) => (
              <div
                key={s.style_id}
                style={{
                  borderRadius: 12,
                  overflow: 'hidden',
                  background: 'linear-gradient(135deg,#667eea 0%,#764ba2 100%)',
                  minHeight: 100,
                  position: 'relative',
                }}
              >
                <div
                  style={{
                    position: 'absolute',
                    bottom: 0,
                    left: 0,
                    right: 0,
                    padding: '24px 8px 8px',
                    background: 'linear-gradient(transparent,rgba(0,0,0,.65))',
                    color: '#fff',
                    fontSize: 12,
                    textAlign: 'center',
                  }}
                >
                  {s.name}
                  <div style={{ opacity: 0.8, fontSize: 10 }}>
                    {RENDER_CLASS_LABELS[s.render_class]}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      <Modal
        title={chatProject ? `导演对话 · ${chatProject.title}` : '导演对话'}
        open={!!chatProject}
        onCancel={() => {
          setChatProject(null)
          setChatReply('')
        }}
        footer={null}
        width={640}
      >
        {chatProject && (
          <>
            <Typography.Paragraph type="secondary">
              阶段：{chatProject.stage}（MVP 占位，后续接入 Skill + LLM）
            </Typography.Paragraph>
            <Input.Search
              placeholder="输入创作指令…"
              enterButton="发送"
              loading={chatLoading}
              onSearch={handleChat}
            />
            {chatReply && (
              <Card size="small" style={{ marginTop: 16, whiteSpace: 'pre-wrap' }}>
                {chatReply}
              </Card>
            )}
          </>
        )}
      </Modal>

      <Modal title="新建短剧项目" open={createOpen} onOk={handleCreate} onCancel={() => setCreateOpen(false)}>
        <Form form={form} layout="vertical">
          <Form.Item name="title" label="项目名称" rules={[{ required: true }]}>
            <Input placeholder="例：重生复仇：大婚之夜" />
          </Form.Item>
          <Form.Item name="genre" label="题材">
            <Input placeholder="女频重生" />
          </Form.Item>
          <Form.Item name="style_preset_id" label="风格（可选）">
            <Select
              allowClear
              placeholder="选择已发布风格"
              options={styles.map((s) => ({ value: s.style_id, label: s.name }))}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
