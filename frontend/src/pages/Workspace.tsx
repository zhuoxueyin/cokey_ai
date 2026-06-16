import { useState, useEffect } from 'react'
import { Button, Dropdown, message } from 'antd'
import {
  PictureOutlined,
  RobotOutlined,
  ClockCircleOutlined,
  VideoCameraOutlined,
  FileTextOutlined,
  DeleteOutlined,
  PictureOutlined as FilterIcon,
} from '@ant-design/icons'
import { getModels, getSessionTasks } from '@/api'
import { useGenerationStore } from '@/store/generation'
import type { ModelItem, TaskItem } from '@/types'
import ChatArea from '@/components/ChatArea'
import ComposerArea from '@/components/ComposerArea'

export default function Workspace() {
  const {
    activeCategory,
    currentModel,
    tasks,
    sessionId,
    setCategory,
    setModel,
    setAvailableModels,
    setTasks,
  } = useGenerationStore()
  const [filterType, setFilterType] = useState<'image' | 'video' | 'text' | 'all'>('all')

  const loadModels = async (category: string) => {
    try {
      const res = await getModels(category)
      if (res.code === 'success' && res.data) {
        setAvailableModels(res.data)
        if (res.data.length > 0 && !currentModel) {
          const def = res.data.find((m: ModelItem) => m.is_default) || res.data[0]
          setModel(def)
        }
      }
    } catch (e) {
      console.error('加载模型失败', e)
    }
  }

  useEffect(() => {
    loadModels(activeCategory)
  }, [activeCategory])

  useEffect(() => {
    const loadHistoryTasks = async () => {
      if (!sessionId || tasks.length > 0) return
      try {
        const res = await getSessionTasks(sessionId)
        if (res.code === 'success' && res.data) {
          setTasks(res.data)
        }
      } catch (e) {
        console.error('加载历史任务失败', e)
      }
    }
    loadHistoryTasks()
  }, [sessionId])

  const handleClearHistory = () => {
    if (tasks.length === 0) return
    if (confirm('确定清空当前历史记录吗？')) {
      setTasks([])
      message.success('已清空')
    }
  }

  const labelMap: Record<string, string> = {
    image: '图片生成',
    video: '视频生成',
    text: '文本创作',
  }

  const filteredTasks = tasks.filter((t: TaskItem) =>
    filterType === 'all' ? true : t.category === filterType,
  )

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', background: '#f9fafc' }}>
      {/* 悬浮筛选器 - 定位在右上角，不占用内容区域 */}
      <div
        style={{
          position: 'absolute',
          top: 16,
          right: 16,
          zIndex: 100,
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          background: 'rgba(255, 255, 255, 0.95)',
          padding: 8,
          borderRadius: 12,
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
        }}
      >
        <Dropdown
          menu={{
            items: [
              { key: 'all', label: '全部', onClick: () => setFilterType('all') },
              { key: 'image', label: '图片生成', onClick: () => setFilterType('image') },
              { key: 'video', label: '视频生成', onClick: () => setFilterType('video') },
              { key: 'text', label: '文本创作', onClick: () => setFilterType('text') },
            ],
          }}
        >
          <Button size="small" style={{ borderRadius: 12, padding: '4px 12px' }}>
            {filterType === 'all' ? '全部类型' : labelMap[filterType]}
          </Button>
        </Dropdown>

        <Dropdown
          menu={{
            items: [
              { key: '0', label: '最近 30 分钟', onClick: () => message.info('时间筛选演示') },
              { key: '1', label: '今天', onClick: () => message.info('时间筛选演示') },
              { key: '2', label: '本周', onClick: () => message.info('时间筛选演示') },
              { key: '3', label: '全部时间', onClick: () => message.info('时间筛选演示') },
            ],
          }}
        >
          <Button size="small" style={{ borderRadius: 12, padding: '4px 12px' }}>
            <ClockCircleOutlined /> 时间筛选
          </Button>
        </Dropdown>

        <Button size="small" style={{ borderRadius: 12, padding: '4px 12px' }} onClick={handleClearHistory}>
          <DeleteOutlined /> 清空对话
        </Button>
      </div>

      {/* 创作区域 - 占满整个空间 */}
      <div style={{ flex: 1, overflowY: 'auto', paddingTop: 60 }}>
        <ChatArea tasks={filteredTasks as any} />
      </div>

      <div style={{ flexShrink: 0 }}>
        <ComposerArea />
      </div>
    </div>
  )
}
