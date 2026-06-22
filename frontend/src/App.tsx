import { SITE_NAME, SITE_SLOGAN } from '@/constants/branding'
import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Link, useLocation, Navigate } from 'react-router-dom'
import { useGenerationStore, validateProcessingTasks, syncTasksFromBackend } from './store/generation'
import { Layout, Menu, Button, Dropdown, Avatar, Modal, Form, Input, Upload } from 'antd'
import type { MenuProps } from 'antd'
import type { UploadProps } from 'antd'
import {
  DesktopOutlined,
  SettingOutlined,
  AppstoreOutlined,
  ClusterOutlined,
  HistoryOutlined,
  FileSearchOutlined,
  FormOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  MessageOutlined,
  UserOutlined,
  LogoutOutlined,
  EditOutlined,
  DownOutlined,
  FolderOutlined,
  BlockOutlined,
  RocketOutlined,
  InboxOutlined,
  SkinOutlined,
  BookOutlined,
  ThunderboltOutlined,
  ApiOutlined,
} from '@ant-design/icons'
import Workspace from './pages/Workspace'
import AssetManager from './pages/AssetManager'
import ModelAdmin from './pages/ModelAdmin'
import ChannelAdmin from './pages/ChannelAdmin'
import TaskAdmin from './pages/TaskAdmin'
import TraceLogAdmin from './pages/TraceLogAdmin'
import OnboardingAdmin from './pages/OnboardingAdmin'
import ProtocolProfileAdmin from './pages/ProtocolProfileAdmin'
import PromptManager from './pages/PromptManager'
import CanvasEntryPage from './pages/CanvasEntryPage'
import CanvasEditor from './pages/CanvasEditor'
import MySpacePage from './pages/MySpacePage'
import Login from './pages/Login'
import { logout, uploadImage, updateProfile } from './api'
import { message } from 'antd'
import StylePlazaPage from './pages/StylePlazaPage'
import DramaStyleAdmin from './pages/DramaStyleAdmin'
import DramaSuperAgentPage from './pages/DramaSuperAgentPage'
import SkillAdminPage from './pages/SkillAdminPage'
import KnowledgeAdminPage from './pages/KnowledgeAdminPage'
import AvatarCropModal from './components/AvatarCropModal'
import ThemeSwitcher from './components/ThemeSwitcher'
import { useSiteTheme } from './hooks/useSiteTheme'

const { Header, Sider, Content } = Layout

type MenuItem = Required<MenuProps>['items'][number]

const mainMenuItems: MenuItem[] = [
  {
    key: '/',
    icon: <DesktopOutlined />,
    label: <Link to="/">创作工作台</Link>,
  },
  {
    key: '/my-space',
    icon: <FolderOutlined />,
    label: <Link to="/my-space">我的空间</Link>,
  },
  {
    key: '/drama',
    icon: <RocketOutlined />,
    label: <Link to="/drama">创作助手</Link>,
  },
  {
    key: '/canvas',
    icon: <BlockOutlined />,
    label: <Link to="/canvas">无限画布</Link>,
  },
  {
    key: '/assets',
    icon: <InboxOutlined />,
    label: <Link to="/assets">资源仓库</Link>,
  },
  {
    key: '/styles',
    icon: <SkinOutlined />,
    label: <Link to="/styles">风格广场</Link>,
  },
  {
    key: '/prompts',
    icon: <MessageOutlined />,
    label: <Link to="/prompts">Prompt 管理</Link>,
  },
  {
    key: '/skills',
    icon: <ThunderboltOutlined />,
    label: <Link to="/skills">Skill 库</Link>,
  },
  {
    key: '/knowledge',
    icon: <BookOutlined />,
    label: <Link to="/knowledge">知识库</Link>,
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
      {
        key: '/admin/protocol-profiles',
        icon: <ApiOutlined />,
        label: <Link to="/admin/protocol-profiles">协议画像</Link>,
      },
      {
        key: '/admin/onboarding',
        icon: <FormOutlined />,
        label: <Link to="/admin/onboarding">接入工单</Link>,
      },
      {
        key: '/admin/trace-logs',
        icon: <FileSearchOutlined />,
        label: <Link to="/admin/trace-logs">链路日志</Link>,
      },
      {
        key: '/admin/drama/styles',
        icon: <SkinOutlined />,
        label: <Link to="/admin/drama/styles">风格管理</Link>,
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
  const { mode: themeMode, setMode: setThemeMode, effective: themeEffective } = useSiteTheme()

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
        const syncedTasks = await syncTasksFromBackend(currentUserId ?? undefined)
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
  const isCanvas = location.pathname.startsWith('/canvas')
  const isCanvasEditor = /^\/canvas\/[^/]+/.test(location.pathname)

  const getSelectedKeys = () => {
    if (location.pathname.startsWith('/admin/models')) return ['/admin', '/admin/models']
    if (location.pathname.startsWith('/admin/channels')) return ['/admin', '/admin/channels']
    if (location.pathname.startsWith('/admin/tasks')) return ['/admin', '/admin/tasks']
    if (location.pathname.startsWith('/admin/protocol-profiles')) return ['/admin', '/admin/protocol-profiles']
    if (location.pathname.startsWith('/admin/onboarding')) return ['/admin', '/admin/onboarding']
    if (location.pathname.startsWith('/admin/trace-logs')) return ['/admin', '/admin/trace-logs']
    if (location.pathname.startsWith('/admin/drama/styles')) return ['/admin', '/admin/drama/styles']
    if (location.pathname === '/prompts') return ['/prompts']
    if (location.pathname === '/skills') return ['/skills']
    if (location.pathname === '/knowledge') return ['/knowledge']
    if (location.pathname.startsWith('/drama')) return ['/drama']
    if (location.pathname === '/my-space') return ['/my-space']
    if (location.pathname === '/styles') return ['/styles']
    if (location.pathname === '/assets') return ['/assets']
    if (location.pathname.startsWith('/canvas')) return ['/canvas']
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
  const [editModalVisible, setEditModalVisible] = useState(false)
  const [form] = Form.useForm()
  const [avatarFile, setAvatarFile] = useState<File | null>(null)
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null)
  const [savingProfile, setSavingProfile] = useState(false)
  const [cropModalOpen, setCropModalOpen] = useState(false)
  const [cropImageSrc, setCropImageSrc] = useState<string | null>(null)

  const revokePreviewUrl = (url: string | null) => {
    if (url?.startsWith('blob:')) {
      URL.revokeObjectURL(url)
    }
  }

  const handleCloseEditModal = () => {
    revokePreviewUrl(avatarPreview)
    revokePreviewUrl(cropImageSrc)
    setAvatarFile(null)
    setAvatarPreview(null)
    setCropImageSrc(null)
    setCropModalOpen(false)
    setEditModalVisible(false)
  }

  // 打开编辑模态框
  const handleOpenEditModal = () => {
    if (userInfo) {
      form.setFieldsValue({
        nickname: userInfo.nickname || '',
      })
      setAvatarFile(null)
      setAvatarPreview(userInfo.avatar_url || null)
      setEditModalVisible(true)
    }
  }

  const handleBeforeUpload: UploadProps['beforeUpload'] = (file) => {
    if (!file.type.startsWith('image/')) {
      message.error('只能上传图片文件')
      return Upload.LIST_IGNORE
    }
    if (file.size > 5 * 1024 * 1024) {
      message.error('图片不能超过 5MB')
      return Upload.LIST_IGNORE
    }
    revokePreviewUrl(cropImageSrc)
    const url = URL.createObjectURL(file)
    setCropImageSrc(url)
    setCropModalOpen(true)
    return false
  }

  const handleCropConfirm = (file: File) => {
    revokePreviewUrl(avatarPreview)
    setAvatarFile(file)
    setAvatarPreview(URL.createObjectURL(file))
    setCropModalOpen(false)
    revokePreviewUrl(cropImageSrc)
    setCropImageSrc(null)
  }

  const handleOpenCropAdjust = () => {
    const src = avatarPreview
    if (!src) return
    if (!src.startsWith('blob:')) {
      message.info('请重新选择本地图片后再调整可见区域')
      return
    }
    setCropImageSrc(src)
    setCropModalOpen(true)
  }

  // 保存用户信息
  const handleSaveUserInfo = async () => {
    try {
      const values = await form.validateFields()
      setSavingProfile(true)

      const payload: { nickname: string; avatar_url?: string } = {
        nickname: values.nickname,
      }

      if (avatarFile) {
        const uploadRes = await uploadImage(avatarFile)
        if (uploadRes.code !== 'success' || !uploadRes.data?.url) {
          message.error(uploadRes.message || '头像上传失败')
          return
        }
        payload.avatar_url = uploadRes.data.url
      }

      const res = await updateProfile(payload)
      if (res.code === 'success' && res.data) {
        localStorage.setItem('user', JSON.stringify(res.data))
        message.success('保存成功')
        handleCloseEditModal()
        window.location.reload()
        return
      }
      message.error(res.message || '保存失败')
    } catch (e: any) {
      if (!e?.errorFields) {
        const status = e?.response?.status
        if (status === 405) {
          message.error('保存接口不可用，请重启后端服务后重试')
        } else {
          message.error(e?.response?.data?.message || e?.message || '保存失败')
        }
      }
    } finally {
      setSavingProfile(false)
    }
  }

  return (
    <Layout style={{ height: '100vh', overflow: 'hidden' }}>
      <Header className="app-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
            style={{ fontSize: 15, width: 32, height: 32 }}
          />
          <div className="app-header-brand">
            <h2 className="app-header-title">{SITE_NAME}</h2>
            <span className="app-header-slogan">{SITE_SLOGAN}</span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <ThemeSwitcher mode={themeMode} onChange={setThemeMode} />
        {userInfo && (
          <Dropdown
            menu={{
              items: [
                {
                  key: 'info',
                  label: (
                    <div style={{ padding: '4px 0', minWidth: 140 }}>
                      <div style={{ fontSize: 13, fontWeight: 500 }}>{userInfo.nickname || userInfo.username}</div>
                      <div style={{ fontSize: 11, color: '#999', marginTop: 2 }}>{userInfo.username}</div>
                    </div>
                  ),
                  disabled: true,
                },
                { type: 'divider' },
                {
                  key: 'edit',
                  icon: <EditOutlined />,
                  label: '编辑资料',
                  onClick: handleOpenEditModal,
                },
                {
                  key: 'logout',
                  icon: <LogoutOutlined />,
                  label: '登出',
                  onClick: handleLogout,
                },
              ],
            }}
            trigger={['click']}
            placement="bottomRight"
          >
            <div className="app-user-chip">
              <Avatar
                size={28}
                src={userInfo.avatar_url || undefined}
                style={{
                  background: userInfo.avatar_url ? undefined : 'linear-gradient(135deg, #7c5cfc 0%, #a78bfa 100%)',
                  flexShrink: 0,
                }}
              >
                {!userInfo.avatar_url && (userInfo.nickname || userInfo.username || '?')[0]?.toUpperCase()}
              </Avatar>
              <span className="app-user-name">{userInfo.nickname || userInfo.username}</span>
              <DownOutlined className="app-user-chip__arrow" />
            </div>
          </Dropdown>
        )}
        </div>
      </Header>

      {/* 编辑用户信息模态框 */}
      <Modal
        title="编辑个人资料"
        open={editModalVisible}
        onCancel={handleCloseEditModal}
        onOk={handleSaveUserInfo}
        confirmLoading={savingProfile}
        okText="保存"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Form.Item label="头像">
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <Avatar
                size={64}
                src={avatarPreview || undefined}
                icon={!avatarPreview ? <UserOutlined /> : undefined}
                style={{
                  background: avatarPreview ? undefined : 'linear-gradient(135deg, #7c5cfc 0%, #a78bfa 100%)',
                }}
              />
              <div>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  <Upload accept="image/*" showUploadList={false} beforeUpload={handleBeforeUpload}>
                    <Button size="small" type="primary">
                      选择图片
                    </Button>
                  </Upload>
                  {avatarPreview && (
                    <Button size="small" onClick={handleOpenCropAdjust}>
                      调整可见区域
                    </Button>
                  )}
                </div>
                {avatarFile && (
                  <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
                    已选择: {avatarFile.name}
                  </div>
                )}
                <div style={{ marginTop: 4, fontSize: 11, color: '#999' }}>
                  支持 JPG/PNG/WebP，不超过 5MB，可拖动缩放裁剪
                </div>
              </div>
            </div>
          </Form.Item>
          <Form.Item 
            label="昵称" 
            name="nickname"
            rules={[{ required: true, message: '请输入昵称' }]}
          >
            <Input placeholder="请输入昵称" />
          </Form.Item>
          <Form.Item label="用户名">
            <Input disabled value={userInfo?.username} />
          </Form.Item>
        </Form>
      </Modal>

      <AvatarCropModal
        open={cropModalOpen}
        imageSrc={cropImageSrc}
        onCancel={() => {
          setCropModalOpen(false)
          revokePreviewUrl(cropImageSrc)
          setCropImageSrc(null)
        }}
        onConfirm={handleCropConfirm}
      />

      <Layout style={{ height: 'calc(100vh - 48px)', overflow: 'hidden' }}>
        <Sider
          width={220}
          collapsible
          collapsed={collapsed}
          onCollapse={setCollapsed}
          trigger={null}
          className="app-sider"
          style={{
            height: '100%',
            flexShrink: 0,
          }}
        >
          <div style={{ padding: '16px 0', height: '100%', overflowY: 'auto' }}>
            <Menu
              mode="inline"
              theme={themeEffective === 'dark' ? 'dark' : 'light'}
              selectedKeys={getSelectedKeys()}
              defaultOpenKeys={['/admin']}
              items={mainMenuItems}
              style={{ borderRight: 0 }}
            />
          </div>
        </Sider>

        <Content
          className={`app-main-content${isCanvasEditor ? ' app-main-content--canvas' : ''}`}
          style={{
            height: '100%',
            overflow: isCanvasEditor ? 'hidden' : 'auto',
          }}
        >
          <Routes>
            <Route path="/" element={<Workspace />} />
            <Route path="/my-space" element={<MySpacePage />} />
            <Route path="/drama" element={<DramaSuperAgentPage />} />
            <Route path="/drama/:threadId" element={<DramaSuperAgentPage />} />
            <Route path="/canvas" element={<CanvasEntryPage />} />
            <Route path="/assets" element={<AssetManager />} />
            <Route path="/styles" element={<StylePlazaPage />} />
            <Route path="/prompts" element={<PromptManager />} />
            <Route path="/skills" element={<SkillAdminPage />} />
            <Route path="/knowledge" element={<KnowledgeAdminPage />} />
            <Route path="/admin/drama/styles" element={<DramaStyleAdmin />} />
            <Route path="/admin/channels" element={<ChannelAdmin />} />
            <Route path="/admin/tasks" element={<TaskAdmin />} />
            <Route path="/admin/protocol-profiles" element={<ProtocolProfileAdmin />} />
            <Route path="/admin/onboarding" element={<OnboardingAdmin />} />
            <Route path="/admin/trace-logs" element={<TraceLogAdmin />} />
            <Route path="/admin/models" element={<ModelAdmin />} />
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
          path="/canvas/:projectId" 
          element={
            <ProtectedRoute>
              <CanvasEditor />
            </ProtectedRoute>
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