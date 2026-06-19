import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Button, Card, Empty, Input, List, Modal, Spin, message } from 'antd'
import { PlusOutlined, DeleteOutlined, EditOutlined, AppstoreOutlined, RightOutlined } from '@ant-design/icons'
import { createCanvasProject, deleteCanvasProject, updateCanvasProject } from '@/api/canvas'
import type { CanvasProject } from '@/types/canvas'
import { useGenerationStore } from '@/store/generation'
import { canvasProjectPath, canvasProjectLinkProps, fetchCanvasProjects, openCanvasProject } from '@/utils/canvasNav'

export default function CanvasHome() {
  const { userId } = useGenerationStore()
  const [projects, setProjects] = useState<CanvasProject[]>([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [renameTarget, setRenameTarget] = useState<CanvasProject | null>(null)
  const [renameTitle, setRenameTitle] = useState('')

  const loadProjects = async () => {
    setLoading(true)
    try {
      setProjects(await fetchCanvasProjects(userId))
    } catch {
      message.error('加载项目失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadProjects()
  }, [userId])

  const handleCreate = async (title?: string) => {
    setCreating(true)
    try {
      const res = await createCanvasProject({
        title: title || `创造项目 ${new Date().toLocaleDateString()}`,
        user_id: userId || undefined,
      })
      if (res.code === 'success' && res.data?.project_id) {
        openCanvasProject(res.data.project_id)
      } else {
        message.error(res.message || '创建失败')
      }
    } catch {
      message.error('创建失败')
    } finally {
      setCreating(false)
    }
  }

  const handleDelete = async (project: CanvasProject) => {
    if (!confirm(`确定删除「${project.title}」？`)) return
    const res = await deleteCanvasProject(project.project_id)
    if (res.code === 'success') {
      message.success('已删除')
      loadProjects()
    }
  }

  const handleRename = async () => {
    if (!renameTarget || !renameTitle.trim()) return
    const res = await updateCanvasProject(renameTarget.project_id, { title: renameTitle.trim() })
    if (res.code === 'success') {
      message.success('已重命名')
      setRenameTarget(null)
      loadProjects()
    }
  }

  return (
    <div className="canvas-home">
      <div className="canvas-home__hero">
        <div>
          <h1>无限画布</h1>
          <p>节点式 AI 创作：连接上游结果作为参考，独立运行生文 / 生图 / 生视频</p>
        </div>
        <Button type="primary" size="large" icon={<PlusOutlined />} loading={creating} onClick={() => handleCreate()}>
          新建创造项目
        </Button>
      </div>

      {loading ? (
        <div className="canvas-home__loading">
          <Spin />
        </div>
      ) : projects.length === 0 ? (
        <Empty description="还没有创造项目">
          <Button type="primary" onClick={() => handleCreate()} loading={creating}>
            创建第一个项目
          </Button>
        </Empty>
      ) : (
        <List
          grid={{ gutter: 16, xs: 1, sm: 2, md: 3, lg: 4 }}
          dataSource={projects}
          renderItem={(item) => (
            <List.Item>
              <Card
                hoverable
                className="canvas-home__card"
                actions={[
                  <EditOutlined
                    key="edit"
                    onClick={(e) => {
                      e.preventDefault()
                      e.stopPropagation()
                      setRenameTarget(item)
                      setRenameTitle(item.title)
                    }}
                  />,
                  <DeleteOutlined
                    key="del"
                    onClick={(e) => {
                      e.preventDefault()
                      e.stopPropagation()
                      handleDelete(item)
                    }}
                  />,
                ]}
              >
                <Link
                  to={canvasProjectPath(item.project_id)}
                  {...canvasProjectLinkProps}
                  className="canvas-home__card-link"
                  onClick={(e) => e.stopPropagation()}
                >
                  <Card.Meta
                    avatar={<AppstoreOutlined style={{ fontSize: 24, color: '#7c5cfc' }} />}
                    title={
                      <span className="canvas-home__card-title">
                        {item.title}
                        <RightOutlined className="canvas-home__card-arrow" />
                      </span>
                    }
                    description={`更新于 ${new Date(item.updated_at).toLocaleString()}`}
                  />
                </Link>
              </Card>
            </List.Item>
          )}
        />
      )}

      <Modal
        title="重命名项目"
        open={!!renameTarget}
        onCancel={() => setRenameTarget(null)}
        onOk={handleRename}
      >
        <Input value={renameTitle} onChange={(e) => setRenameTitle(e.target.value)} />
      </Modal>
    </div>
  )
}

/** 主页快捷入口：最近项目 + 新建 */
export function CanvasProjectEntry({ compact }: { compact?: boolean }) {
  const { userId } = useGenerationStore()
  const [creating, setCreating] = useState(false)
  const [recentProjects, setRecentProjects] = useState<CanvasProject[]>([])

  useEffect(() => {
    fetchCanvasProjects(userId, 6).then(setRecentProjects).catch(() => {})
  }, [userId])

  const handleCreate = async () => {
    setCreating(true)
    try {
      const res = await createCanvasProject({
        title: `创造项目 ${new Date().toLocaleDateString()}`,
        user_id: userId || undefined,
      })
      if (res.code === 'success' && res.data?.project_id) {
        openCanvasProject(res.data.project_id)
      } else {
        message.error(res.message || '创建失败')
      }
    } catch {
      message.error('创建失败')
    } finally {
      setCreating(false)
    }
  }

  if (compact) {
    return (
      <button type="button" className="canvas-entry-chip" onClick={handleCreate} disabled={creating}>
        <PlusOutlined />
        <span>{creating ? '创建中…' : '新建创造项目'}</span>
      </button>
    )
  }

  return (
    <div className="canvas-entry-banner">
      <div className="canvas-entry-banner__text">
        <strong>无限画布</strong>
        <span>节点连接 · 独立运行 · 结果回显</span>
        {recentProjects.length > 0 && (
          <div className="canvas-entry-recent">
            <span className="canvas-entry-recent__label">最近项目：</span>
            {recentProjects.slice(0, 4).map((p) => (
              <Link
                key={p.project_id}
                to={canvasProjectPath(p.project_id)}
                {...canvasProjectLinkProps}
                className="canvas-entry-recent__item"
              >
                {p.title}
              </Link>
            ))}
          </div>
        )}
      </div>
      <div className="canvas-entry-banner__actions">
        <Button type="primary" icon={<PlusOutlined />} loading={creating} onClick={handleCreate}>
          新建创造项目
        </Button>
        <Link to="/canvas">
          <Button>我的项目</Button>
        </Link>
      </div>
    </div>
  )
}
