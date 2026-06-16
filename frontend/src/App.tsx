import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Link, useLocation, Navigate } from 'react-router-dom'
import { useGenerationStore, validateProcessingTasks, syncTasksFromBackend } from './store/generation'
import { Layout, Menu, ConfigProvider, Button, Dropdown } from 'antd'
import type { MenuProps } from 'antd'
import {
  FileTextOutlined,
  PictureOutlined,
  VideoCameraOutlined,
  DesktopOutlined,
  SettingOutlined,
  AppstoreOutlined,
  ClusterOutlined,
  HistoryOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  MessageOutlined,
  UserOutlined,
  LogoutOutlined,
} from '@ant-design/icons'
import Workspace from './pages/Workspace'
import AssetManager from './pages/AssetManager'
import ModelAdmin from './pages/ModelAdmin'
import ChannelAdmin from './pages/ChannelAdmin'
import TaskAdmin from './pages/TaskAdmin'
import PromptManager from './pages/PromptManager'
import Login from './pages/Login'
import { logout } from './api'
import { message } from 'antd'

const { Header, Sider, Content } = Layout

type MenuItem = Required<MenuProps>['items'][number]

const mainMenuItems: MenuItem[] = [
  {
    key: '/',
    icon: <DesktopOutlined />,
    label: <Link to="/">创作工作台</Link>,
  },
  {
    key: '/assets',
    icon: <PictureOutlined />,
    label: <Link to="/assets">资源管理</Link>,
  },
  {
    key: '/prompts',
    icon: <MessageOutlined />,
    label: <Link to="/prompts">Prompt管理</Link>,
  },
  {
    key: '/admin',
    icon: <SettingOutlined />,
    label: '系统管理',
    children: [
      {
        key: '/admin/models',
        icon: <AppstoreOutlined />,
        label: <Link to="/admin/models">模型管理</Link>,
      },
      {
        key: '/admin/channels',
        icon: <ClusterOutlined />,
        label: <Link to="/admin/channels">渠道管理</Link>,
      },
      {
        key: '/admin/tasks',
        icon: <HistoryOutlined />,
        label: <Link to="/admin/tasks">任务管理</Link>,
      },
    ],
  },
]

// 检查是否已登录
const isLoggedIn = () => {
  return !!localStorage.getItem('token')
}

// 公共页面（无需登录）
const publicRoutes = ['/login']

function AppContent() {
  const location = useLocation()
  const [collapsed, setCollapsed] = useState(false)
  const { tasks, setTasks, setUserId } = useGenerationStore()

  // 页面加载时初始化
  useEffect(() => {
    // 从localStorage恢复用户信息
    const userStr = localStorage.getItem('user')
    if (userStr) {
      try {
        const user = JSON.parse(userStr)
        setUserId(user.userId)
      } catch (e) {
        console.error('解析用户信息失败', e)
      }
    }

    // 如果已登录，同步任务
    if (isLoggedIn()) {
      const initTasks = async () => {
        const currentUserId = useGenerationStore.getState().userId
        const syncedTasks = await syncTasksFromBackend(currentUserId)
        setTasks(syncedTasks)
        
        const updatedTasks = await validateProcessingTasks(syncedTasks)
        const hasChanges = updatedTasks.some((t, i) => t.status !== syncedTasks[i]?.status)
        if (hasChanges) {
          setTasks(updatedTasks)
        }
      }
      initTasks()
    }
  }, [])

  const handleLogout = async () => {
    if (confirm('确定要登出吗？')) {
      try {
        await logout()
      } catch (e) {
        // 忽略登出失败（可能是token已过期）
      } finally {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        setUserId('default_user')
        setTasks([])
        message.success('已登出')
        window.location.href = '/login'
      }
    }
  }

  const isAdmin = location.pathname.startsWith('/admin')
  const isAssets = location.pathname === '/assets'

  const getSelectedKeys = () => {
    if (location.pathname.startsWith('/admin/models')) return ['/admin', '/admin/models']
    if (location.pathname.startsWith('/admin/channels')) return ['/admin', '/admin/channels']
    if (location.pathname.startsWith('/admin/tasks')) return ['/admin', '/admin/tasks']
    if (location.pathname === '/assets') return ['/assets']
    if (location.pathname === '/prompts') return ['/prompts']
    return ['/']
  }

  // 获取当前用户信息
  const getUserInfo = () => {
    const userStr = localStorage.getItem('user')
    if (userStr) {
      try {
        return JSON.parse(userStr)
      } catch (e) {
        return null
      }
    }
    return null
  }

  const userInfo = getUserInfo()

  return (
    <Layout style={{ height: '100vh', overflow: 'hidden' }}>
      <Header
        style={{
          background: '#fff',
          padding: '0 24px',
          borderBottom: '1px solid #f0f0f0',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          height: 64,
          lineHeight: '64px',
          flexShrink: 0,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
            style={{ fontSize: 16, width: 40, height: 40 }}
          />
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 600 }}>AIGC 创作平台</h2>
        </div>
        
        {userInfo && (
          <Dropdown
            menu={{
              items: [
                {
                  key: 'logout',
                  icon: <LogoutOutlined />,
                  label: '登出',
                  onClick: handleLogout,
                },
              ],
            }}
          >
            <Button type="text" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <UserOutlined />
              <span>{userInfo.nickname || userInfo.username}</span>
            </Button>
          </Dropdown>
        )}
      </Header>

      <Layout style={{ height: 'calc(100vh - 64px)', overflow: 'hidden' }}>
        <Sider
          width={220}
          collapsible
          collapsed={collapsed}
          onCollapse={setCollapsed}
          trigger={null}
          style={{
            background: '#fff',
            borderRight: '1px solid #f0f0f0',
            height: '100%',
            flexShrink: 0,
          }}
        >
          <div style={{ padding: '16px 0', height: '100%', overflowY: 'auto' }}>
            <Menu
              mode="inline"
              selectedKeys={getSelectedKeys()}
              defaultOpenKeys={['/admin']}
              items={mainMenuItems}
              style={{ borderRight: 0 }}
            />
          </div>
        </Sider>

        <Content
          style={{
            background: '#f5f5f5',
            height: '100%',
            overflow: 'hidden',
          }}
        >
          <Routes>
            <Route path="/" element={<Workspace />} />
            <Route path="/assets" element={<AssetManager />} />
            <Route path="/admin/models" element={<ModelAdmin />} />
            <Route path="/admin/channels" element={<ChannelAdmin />} />
            <Route path="/admin/tasks" element={<TaskAdmin />} />
            <Route path="/prompts" element={<PromptManager />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  )
}

// 路由守卫组件
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  if (!isLoggedIn()) {
    return <Navigate to="/login" />
  }
  return <>{children}</>
}

// 登录页面路由组件
function LoginRoute({ children }: { children: React.ReactNode }) {
  if (isLoggedIn()) {
    return <Navigate to="/" />
  }
  return <>{children}</>
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route 
          path="/login" 
          element={
            <LoginRoute>
              <Login />
            </LoginRoute>
          } 
        />
        <Route 
          path="/*" 
          element={
            <ProtectedRoute>
              <AppContent />
            </ProtectedRoute>
          } 
        />
      </Routes>
    </BrowserRouter>
  )
}