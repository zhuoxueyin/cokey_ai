import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Avatar, Dropdown, Input, message } from 'antd'
import type { MenuProps } from 'antd'
import {
  MenuOutlined,
  HomeOutlined,
  AppstoreOutlined,
  PlusOutlined,
  DeleteOutlined,
  UserOutlined,
  HistoryOutlined,
} from '@ant-design/icons'
import { deleteCanvasProject, updateCanvasProject } from '@/api/canvas'

interface CanvasEditorHeaderProps {
  projectId: string
  isDraft?: boolean
  title: string
  onTitleChange: (title: string) => void
  userId?: string | null
  onOpenRunHistory?: () => void
}

function getUserInfo() {
  try {
    const raw = localStorage.getItem('user')
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export default function CanvasEditorHeader({ projectId, isDraft, title, onTitleChange, onOpenRunHistory }: CanvasEditorHeaderProps) {
  const navigate = useNavigate()
  const [editingTitle, setEditingTitle] = useState(title)
  const userInfo = getUserInfo()

  useEffect(() => {
    setEditingTitle(title)
  }, [title])

  const saveTitle = async (next: string) => {
    const trimmed = next.trim()
    if (!trimmed) return
    onTitleChange(trimmed)
    if (isDraft || projectId === 'new') return
    const res = await updateCanvasProject(projectId, { title: trimmed })
    if (res.code === 'success') {
      onTitleChange(trimmed)
    }
  }

  const handleNewProject = () => {
    window.location.href = '/canvas/new'
  }

  const handleDeleteProject = async () => {
    if (isDraft || projectId === 'new') {
      navigate('/my-space')
      return
    }
    if (!confirm(`确定删除项目「${title}」？此操作不可恢复`)) return
    const res = await deleteCanvasProject(projectId)
    if (res.code === 'success') {
      message.success('项目已删除')
      navigate('/my-space')
    } else {
      message.error(res.message || '删除失败')
    }
  }

  const menuItems: MenuProps['items'] = [
    { key: 'home', icon: <HomeOutlined />, label: '回到首页', onClick: () => navigate('/') },
    { key: 'projects', icon: <AppstoreOutlined />, label: '我的空间', onClick: () => navigate('/my-space') },
    { key: 'new', icon: <PlusOutlined />, label: '新建项目', onClick: handleNewProject },
    { type: 'divider' },
    { key: 'delete', icon: <DeleteOutlined />, label: '删除项目', danger: true, onClick: handleDeleteProject },
  ]

  return (
    <header className="canvas-header canvas-header--standalone">
      <div className="canvas-header__left">
        <Dropdown menu={{ items: menuItems }} trigger={['click']} placement="bottomLeft">
          <button type="button" className="canvas-header__menu-btn">
            <MenuOutlined />
          </button>
        </Dropdown>
        <Input
          value={editingTitle}
          onChange={(e) => setEditingTitle(e.target.value)}
          onBlur={() => saveTitle(editingTitle)}
          onPressEnter={() => saveTitle(editingTitle)}
          className="canvas-header__title"
          bordered={false}
        />
      </div>
      <div className="canvas-header__right">
        {onOpenRunHistory && (
          <button type="button" className="canvas-header__history-btn" onClick={onOpenRunHistory}>
            <HistoryOutlined />
            <span>运行记录</span>
          </button>
        )}
        <Avatar
          size={32}
          src={userInfo?.avatar_url || undefined}
          icon={!userInfo?.avatar_url ? <UserOutlined /> : undefined}
          style={{
            background: userInfo?.avatar_url ? undefined : 'linear-gradient(135deg, #7c5cfc 0%, #a78bfa 100%)',
          }}
        />
        <span className="canvas-header__username">{userInfo?.nickname || userInfo?.username || '用户'}</span>
      </div>
    </header>
  )
}
