import { useState, useEffect, useRef } from 'react'
import { Button, Dropdown, message } from 'antd'
import {
  PictureOutlined,
  RobotOutlined,
  ClockCircleOutlined,
  VideoCameraOutlined,
  FileTextOutlined,
  DeleteOutlined,
  FilterOutlined,
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
  const [timeRange, setTimeRange] = useState<number>(24)  // 默认最近1天
  const [timeRangeLabel, setTimeRangeLabel] = useState('最近 1 天')
  const [isFilterApplied, setIsFilterApplied] = useState(false)
  const loadedSessionIds = useRef<Set<string>>(new Set())  // 记录已加载过的 sessionId

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

  // 加载任务列表（带筛选条件）
  const loadTasksWithFilter = async (forceRefresh = false) => {
    if (!sessionId) return
    if (!forceRefresh && loadedSessionIds.current.has(sessionId)) return
    
    try {
      // 调用接口时传入筛选参数
      const effectiveCategory = filterType === 'all' ? undefined : filterType
      const effectiveTimeRange = timeRange === 0 ? undefined : timeRange
      
      const res = await getSessionTasks(sessionId, effectiveCategory, effectiveTimeRange)
      if (res.code === 'success' && res.data) {
        // 后端已经按 created_at 升序排序
        setTasks(res.data)
        loadedSessionIds.current.add(sessionId)
        message.success(`加载成功，共 ${res.data.length} 条记录`)
      }
    } catch (e) {
      console.error('加载历史任务失败', e)
    }
  }

  useEffect(() => {
    loadTasksWithFilter()
  }, [sessionId])

  // 类型筛选变化时重新加载
  const handleTypeFilterChange = (type: 'image' | 'video' | 'text' | 'all') => {
    setFilterType(type)
    setIsFilterApplied(type !== 'all' || timeRange !== 0)
    loadedSessionIds.current.delete(sessionId!)
    loadTasksWithFilter(true)
  }

  // 时间筛选变化时重新加载
  const handleTimeFilterChange = (hours: number, label: string) => {
    setTimeRange(hours)
    setTimeRangeLabel(label)
    setIsFilterApplied(filterType !== 'all' || hours !== 0)
    loadedSessionIds.current.delete(sessionId!)
    loadTasksWithFilter(true)
  }

  const handleClearHistory = () => {
    if (tasks.length === 0) return
    if (confirm('确定清空当前历史记录吗？')) {
      setTasks([])
      if (sessionId) {
        loadedSessionIds.current.delete(sessionId)
      }
      message.success('已清空')
    }
  }

  const handleResetFilter = () => {
    setFilterType('all')
    setTimeRange(24)
    setTimeRangeLabel('最近 1 天')
    setIsFilterApplied(false)
    loadedSessionIds.current.delete(sessionId!)
    loadTasksWithFilter(true)
  }

  const labelMap: Record<string, string> = {
    image: '图片生成',
    video: '视频生成',
    text: '文本创作',
  }

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', background: '#f9fafc' }}>
      {/* 创作区域 - 占满整个空间 */}
      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>
        {/* 对话流区域头部 - 筛选器放在这里 */}
        <div 
          style={{ 
            padding: '12px 16px', 
            background: '#fff', 
            borderBottom: '1px solid #f0f0f0',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <h3 style={{ margin: 0, fontSize: 14, fontWeight: 500, color: '#333' }}>AI 创作流</h3>
            {isFilterApplied && (
              <Button 
                size="small" 
                type="text" 
                onClick={handleResetFilter}
                style={{ color: '#1890ff', fontSize: 12 }}
              >
                重置筛选
              </Button>
            )}
          </div>
          
          {/* 筛选器组 */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Dropdown
              menu={{
                items: [
                  { key: 'all', label: '全部', onClick: () => handleTypeFilterChange('all') },
                  { key: 'image', label: '图片生成', onClick: () => handleTypeFilterChange('image') },
                  { key: 'video', label: '视频生成', onClick: () => handleTypeFilterChange('video') },
                  { key: 'text', label: '文本创作', onClick: () => handleTypeFilterChange('text') },
                ],
              }}
            >
              <Button size="small" style={{ borderRadius: 8, padding: '4px 12px' }}>
                <FilterOutlined style={{ marginRight: 4 }} />
                {filterType === 'all' ? '全部类型' : labelMap[filterType]}
              </Button>
            </Dropdown>

            <Dropdown
              menu={{
                items: [
                  { key: '0.5', label: '最近 30 分钟', onClick: () => handleTimeFilterChange(0.5, '最近 30 分钟') },
                  { key: '1', label: '最近 1 小时', onClick: () => handleTimeFilterChange(1, '最近 1 小时') },
                  { key: '24', label: '最近 1 天', onClick: () => handleTimeFilterChange(24, '最近 1 天') },
                  { key: '168', label: '最近 1 周', onClick: () => handleTimeFilterChange(168, '最近 1 周') },
                  { key: '720', label: '最近 1 个月', onClick: () => handleTimeFilterChange(720, '最近 1 个月') },
                  { key: '0', label: '全部时间', onClick: () => handleTimeFilterChange(0, '全部时间') },
                ],
              }}
            >
              <Button size="small" style={{ borderRadius: 8, padding: '4px 12px' }}>
                <ClockCircleOutlined style={{ marginRight: 4 }} />
                {timeRangeLabel}
              </Button>
            </Dropdown>

            <Button 
              size="small" 
              style={{ borderRadius: 8, padding: '4px 12px' }} 
              onClick={handleClearHistory}
              danger
            >
              <DeleteOutlined /> 清空
            </Button>
          </div>
        </div>

        {/* 聊天内容区域 */}
        <div style={{ flex: 1, overflowY: 'auto' }}>
          <ChatArea tasks={tasks as any} />
        </div>
      </div>

      <div style={{ flexShrink: 0 }}>
        <ComposerArea />
      </div>
    </div>
  )
}
