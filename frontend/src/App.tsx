import { useState } from 'react'
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom'
import { Layout, Menu, ConfigProvider } from 'antd'
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
} from '@ant-design/icons'
import Workspace from './pages/Workspace'
import ModelAdmin from './pages/ModelAdmin'
import ChannelAdmin from './pages/ChannelAdmin'
import TaskAdmin from './pages/TaskAdmin'

const { Header, Sider, Content } = Layout

type MenuItem = Required<MenuProps>['items'][number]

const mainMenuItems: MenuItem[] = [
  {
    key: '/',
    icon: <DesktopOutlined />,
    label: <Link to="/">创作工作台</Link>,
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

function AppContent() {
  const location = useLocation()
  const [collapsed, setCollapsed] = useState(false)

  const isAdmin = location.pathname.startsWith('/admin')

  const getSelectedKeys = () => {
    if (location.pathname.startsWith('/admin/models')) return ['/admin', '/admin/models']
    if (location.pathname.startsWith('/admin/channels')) return ['/admin', '/admin/channels']
    if (location.pathname.startsWith('/admin/tasks')) return ['/admin', '/admin/tasks']
    return ['/']
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header
        style={{
          background: '#fff',
          padding: '0 24px',
          borderBottom: '1px solid #f0f0f0',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 600 }}>AIGC 创作平台</h2>
        </div>
        <div style={{ color: '#888', fontSize: 13 }}>v1.0.0</div>
      </Header>

      <Layout>
        <Sider
          width={220}
          collapsible
          collapsed={collapsed}
          onCollapse={setCollapsed}
          trigger={null}
          style={{
            background: '#fff',
            borderRight: '1px solid #f0f0f0',
          }}
        >
          <div style={{ padding: '16px 0', height: 'calc(100vh - 64px)', overflowY: 'auto' }}>
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
            padding: 24,
            background: '#f5f5f5',
            minHeight: 'calc(100vh - 64px)',
          }}
        >
          <Routes>
            <Route path="/" element={<Workspace />} />
            <Route path="/admin/models" element={<ModelAdmin />} />
            <Route path="/admin/channels" element={<ChannelAdmin />} />
            <Route path="/admin/tasks" element={<TaskAdmin />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  )
}
