import { useState } from 'react'
import { Layout, Tabs } from 'antd'
import type { TabsProps } from 'antd'
import {
  FileTextOutlined,
  PictureOutlined,
  VideoCameraOutlined,
} from '@ant-design/icons'
import { useGenerationStore } from '@/store/generation'
import ParamPanel from '../components/ParamPanel'
import ChatArea from '../components/ChatArea'

const { Sider, Content } = Layout

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
    <div style={{ background: '#fff', borderRadius: 8, minHeight: 'calc(100vh - 112px)' }}>
      <div
        style={{
          padding: '16px 24px',
          borderBottom: '1px solid #f0f0f0',
        }}
      >
        <Tabs
          activeKey={activeCategory}
          onChange={handleTabChange}
          items={tabItems}
          size="large"
        />
      </div>

      <Layout style={{ background: 'transparent', minHeight: 'calc(100vh - 190px)' }}>
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
            <div style={{ padding: 20, height: 'calc(100vh - 190px)', overflowY: 'auto' }}>
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
          <div style={{ height: 'calc(100vh - 190px)', overflowY: 'auto' }}>
            <ChatArea />
          </div>
        </Content>
      </Layout>
    </div>
  )
}
