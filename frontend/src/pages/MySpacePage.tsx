import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  Button,
  Empty,
  Input,
  Popconfirm,
  Space,
  Tabs,
  Tag,
  Typography,
  message,
} from 'antd'
import {
  BlockOutlined,
  DeleteOutlined,
  ReloadOutlined,
  RocketOutlined,
  SearchOutlined,
} from '@ant-design/icons'
import { deleteAgentThread, listAgentThreads } from '@/api/dramaAgent'
import { deleteCanvasProject } from '@/api/canvas'
import { formatServerDateTime } from '@/utils/formatDateTime'
import type { DramaAgentThread } from '@/types/dramaAgent'
import { getAgentModeLabel } from '@/types/dramaAgent'
import type { CanvasProject } from '@/types/canvas'
import { canvasProjectPath, fetchCanvasProjects } from '@/utils/canvasNav'
import { useGenerationStore } from '@/store/generation'

const { Title, Text, Paragraph } = Typography

function DeleteCardAction({
  title,
  onConfirm,
}: {
  title: string
  onConfirm: () => void | Promise<void>
}) {
  return (
    <Popconfirm title={title} okText="删除" cancelText="取消" onConfirm={onConfirm}>
      <Button
        type="text"
        size="small"
        danger
        icon={<DeleteOutlined />}
        className="my-space-card__delete"
        aria-label="删除"
        onClick={(e) => e.stopPropagation()}
      />
    </Popconfirm>
  )
}

export default function MySpacePage() {
  const navigate = useNavigate()
  const { userId } = useGenerationStore()
  const [agentLoading, setAgentLoading] = useState(false)
  const [canvasLoading, setCanvasLoading] = useState(false)
  const [agentThreads, setAgentThreads] = useState<DramaAgentThread[]>([])
  const [canvasProjects, setCanvasProjects] = useState<CanvasProject[]>([])
  const [agentKeyword, setAgentKeyword] = useState('')
  const [canvasKeyword, setCanvasKeyword] = useState('')

  const loadAgents = async () => {
    setAgentLoading(true)
    try {
      const res = await listAgentThreads({ page: 1, page_size: 100 })
      setAgentThreads((res.data as DramaAgentThread[]) || [])
    } finally {
      setAgentLoading(false)
    }
  }

  const loadCanvas = async () => {
    setCanvasLoading(true)
    try {
      setCanvasProjects(await fetchCanvasProjects(userId))
    } finally {
      setCanvasLoading(false)
    }
  }

  useEffect(() => {
    loadAgents()
    loadCanvas()
  }, [userId])

  const filteredAgents = agentThreads.filter((t) => {
    if (!agentKeyword.trim()) return true
    const q = agentKeyword.toLowerCase()
    return (
      t.title?.toLowerCase().includes(q) ||
      t.thread_id.toLowerCase().includes(q) ||
      getAgentModeLabel(t.agent_mode).includes(q)
    )
  })

  const filteredCanvas = canvasProjects.filter((p) => {
    if (!canvasKeyword.trim()) return true
    const q = canvasKeyword.toLowerCase()
    return p.title?.toLowerCase().includes(q) || p.project_id.toLowerCase().includes(q)
  })

  const handleDeleteAgent = async (thread: DramaAgentThread) => {
    const res = await deleteAgentThread(thread.thread_id)
    if (res.code === 'success') {
      message.success('已删除')
      loadAgents()
    } else {
      message.error(res.message || '删除失败')
    }
  }

  const handleDeleteCanvas = async (project: CanvasProject) => {
    const res = await deleteCanvasProject(project.project_id)
    if (res.code === 'success') {
      message.success('已删除')
      loadCanvas()
    } else {
      message.error(res.message || '删除失败')
    }
  }

  return (
    <div className="my-space-page">
      <div className="my-space-page__hero">
        <div>
          <Title level={3} className="my-space-page__title">
            我的空间
          </Title>
          <Paragraph type="secondary" className="my-space-page__desc">
            管理你的创作助手对话与无限画布项目，随时可重入继续创作。
          </Paragraph>
        </div>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={() => { loadAgents(); loadCanvas() }}>
            刷新
          </Button>
        </Space>
      </div>

      <Tabs
        className="my-space-page__tabs"
        items={[
          {
            key: 'agent',
            label: (
              <span>
                <RocketOutlined /> 创作助手 ({filteredAgents.length})
              </span>
            ),
            children: (
              <div className="my-space-panel">
                <Input
                  prefix={<SearchOutlined />}
                  placeholder="搜索对话标题 / 模式"
                  value={agentKeyword}
                  onChange={(e) => setAgentKeyword(e.target.value)}
                  allowClear
                  style={{ maxWidth: 320, marginBottom: 16 }}
                />
                {filteredAgents.length === 0 && !agentLoading ? (
                  <Empty description="暂无创作助手对话">
                    <Link to="/drama">
                      <Button type="primary">开始第一次创作</Button>
                    </Link>
                  </Empty>
                ) : (
                  <div className="my-space-list">
                    {filteredAgents.map((t) => (
                      <div key={t.thread_id} className="my-space-card my-space-card--agent">
                        <Link to={`/drama/${t.thread_id}`} className="my-space-card__body">
                          <div className="my-space-card__head">
                            <Tag color="purple">{getAgentModeLabel(t.agent_mode)}</Tag>
                            {t.canvas_project_id ? (
                              <Tag color="blue">已绑定画布</Tag>
                            ) : (
                              <Tag color="default">独立对话</Tag>
                            )}
                            <Text type="secondary" className="my-space-card__time">
                              {formatServerDateTime(t.created_at)}
                            </Text>
                          </div>
                          <div className="my-space-card__title">{t.title || '未命名创作'}</div>
                          <div className="my-space-card__preview">
                            {(t as DramaAgentThread & { last_message_preview?: string }).last_message_preview ||
                              '点击继续对话…'}
                          </div>
                          <div className="my-space-card__meta">
                            {(t as DramaAgentThread & { message_count?: number }).message_count ?? 0} 条消息
                            {t.canvas_project_id && (
                              <Button
                                type="link"
                                size="small"
                                className="my-space-card__canvas-link"
                                onClick={(e) => {
                                  e.preventDefault()
                                  e.stopPropagation()
                                  navigate(canvasProjectPath(t.canvas_project_id!))
                                }}
                              >
                                打开画布
                              </Button>
                            )}
                          </div>
                        </Link>
                        <DeleteCardAction
                          title="确定删除该创作助手对话？"
                          onConfirm={() => handleDeleteAgent(t)}
                        />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ),
          },
          {
            key: 'canvas',
            label: (
              <span>
                <BlockOutlined /> 无限画布 ({filteredCanvas.length})
              </span>
            ),
            children: (
              <div className="my-space-panel">
                <Input
                  prefix={<SearchOutlined />}
                  placeholder="搜索画布项目名称"
                  value={canvasKeyword}
                  onChange={(e) => setCanvasKeyword(e.target.value)}
                  allowClear
                  style={{ maxWidth: 320, marginBottom: 16 }}
                />
                {filteredCanvas.length === 0 && !canvasLoading ? (
                  <Empty description="暂无画布项目">
                    <Link to="/canvas">
                      <Button type="primary">开始创作</Button>
                    </Link>
                  </Empty>
                ) : (
                  <div className="my-space-list">
                    {filteredCanvas.map((p) => (
                      <div key={p.project_id} className="my-space-card my-space-card--canvas">
                        <Link to={canvasProjectPath(p.project_id)} className="my-space-card__body">
                          <div className="my-space-card__head">
                            <Space size={4} wrap>
                              <Tag color="blue">无限画布</Tag>
                              {p.agent_thread_id && <Tag color="purple">创作助手二阶段</Tag>}
                            </Space>
                            <Text type="secondary" className="my-space-card__time">
                              {formatServerDateTime(p.created_at)}
                            </Text>
                          </div>
                          <div className="my-space-card__title">{p.title || '未命名画布'}</div>
                          <div className="my-space-card__meta">{p.project_id}</div>
                        </Link>
                        <DeleteCardAction
                          title="确定删除该画布？"
                          onConfirm={() => handleDeleteCanvas(p)}
                        />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ),
          },
        ]}
      />
    </div>
  )
}
