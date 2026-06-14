import { useState } from 'react'
import { Layout, Tabs, ConfigProvider } from 'antd'
import type { TabsProps } from 'antd'
import {
  FileTextOutlined,
  PictureOutlined,
  VideoCameraOutlined,
} from '@ant-design/icons'
import { useGenerationStore } from '@/store/generation'
import ParamPanel from '../components/ParamPanel'
import ChatArea from '../components/ChatArea'

const { Header, Sider, Content } = Layout

const tabItems: TabsProps['items'] = [
  { key: 'text', label: <span><FileTextOutlined /> 文本创作</span> },
  { key: 'image', label: <span><PictureOutlined /> 图像生成</span> },
  { key: 'video', label: <span><VideoCameraOutlined /> 视频生成</span> },
]

export default function Workspace() {
  const { activeCategory, setCategory } = useGenerationStore()
  const [collapsed, setCollapsed] = useState(false)

  const handleTabChange = (key: string) => {
    setCategory(key as 'text' | 'image' | 'video')
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
          <Tabs
            activeKey={activeCategory}
            onChange={handleTabChange}
            items={tabItems}
            size="large"
          />
        </div>
        <div style={{ color: '#888', fontSize: 13 }}>v1.0.0</div>
      </Header>

      <Layout>
        <Sider
          width={400}
          collapsible
          collapsed={collapsed}
          onCollapse={setCollapsed}
          collapsedWidth={0}
          trigger={null}
          style={{
            background: '#fff',
            borderRight: '1px solid #f0f0f0',
            overflow: 'auto',
          }}
        >
          {!collapsed && (
            <div style={{ padding: 20, height: 'calc(100vh - 64px)', overflowY: 'auto' }}>
              <ParamPanel />
            </div>
          )}
        </Sider>

        <Content
          style={{
            padding: 0,
            background: '#f5f5f5',
            overflow: 'hidden',
          }}
        >
          <div style={{ height: 'calc(100vh - 64px)', overflowY: 'auto' }}>
            <ChatArea />
          </div>
        </Content>
      </Layout>
    </Layout>
  )
}
