import { useState, useEffect, useRef } from 'react'
import { Button, Dropdown, message, Tooltip } from 'antd'
import {
  ClockCircleOutlined,
  DeleteOutlined,
  FilterOutlined,
  ReloadOutlined,
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
    setModel,
    setAvailableModels,
    setTasks,
  } = useGenerationStore()
  const [filterType, setFilterType] = useState<'image' | 'video' | 'text' | 'all'>('all')
  const [timeRange, setTimeRange] = useState<number>(24)
  const [timeRangeLabel, setTimeRangeLabel] = useState('最近 1 天')
  const [isFilterApplied, setIsFilterApplied] = useState(false)
  const loadedSessionIds = useRef<Set<string>>(new Set())

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

  const loadTasksWithFilter = async (forceRefresh = false) => {
    if (!sessionId) return
    if (!forceRefresh && loadedSessionIds.current.has(sessionId)) return

    try {
      const effectiveCategory = filterType === 'all' ? undefined : filterType
      const effectiveTimeRange = timeRange === 0 ? undefined : timeRange

      const res = await getSessionTasks(sessionId, effectiveCategory, effectiveTimeRange)
      if (res.code === 'success' && res.data) {
        setTasks(res.data)
        loadedSessionIds.current.add(sessionId)
      }
    } catch (e) {
      console.error('加载历史任务失败', e)
    }
  }

  useEffect(() => {
    loadTasksWithFilter()
  }, [sessionId])

  const handleTypeFilterChange = (type: 'image' | 'video' | 'text' | 'all') => {
    setFilterType(type)
    setIsFilterApplied(type !== 'all' || timeRange !== 0)
    loadedSessionIds.current.delete(sessionId!)
    loadTasksWithFilter(true)
  }

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
    image: '图片',
    video: '视频',
    text: '文本',
  }

  return (
    <div className="workspace-root">
      <div className="workspace-stream">
        <div className="workspace-filter-float">
          {isFilterApplied && (
            <Tooltip title="重置筛选">
              <Button type="text" size="small" icon={<ReloadOutlined />} onClick={handleResetFilter} />
            </Tooltip>
          )}
          <Dropdown
            menu={{
              items: [
                { key: 'all', label: '全部类型', onClick: () => handleTypeFilterChange('all') },
                { key: 'image', label: '图片生成', onClick: () => handleTypeFilterChange('image') },
                { key: 'video', label: '视频生成', onClick: () => handleTypeFilterChange('video') },
                { key: 'text', label: '文本创作', onClick: () => handleTypeFilterChange('text') },
              ],
            }}
          >
            <Button type="text" size="small" icon={<FilterOutlined />}>
              {filterType === 'all' ? '类型' : labelMap[filterType]}
            </Button>
          </Dropdown>
          <Dropdown
            menu={{
              items: [
                { key: '0.5', label: '最近 30 分钟', onClick: () => handleTimeFilterChange(0.5, '30分钟') },
                { key: '1', label: '最近 1 小时', onClick: () => handleTimeFilterChange(1, '1小时') },
                { key: '24', label: '最近 1 天', onClick: () => handleTimeFilterChange(24, '1天') },
                { key: '168', label: '最近 1 周', onClick: () => handleTimeFilterChange(168, '1周') },
                { key: '720', label: '最近 1 个月', onClick: () => handleTimeFilterChange(720, '1月') },
                { key: '0', label: '全部时间', onClick: () => handleTimeFilterChange(0, '全部') },
              ],
            }}
          >
            <Button type="text" size="small" icon={<ClockCircleOutlined />}>
              {timeRangeLabel}
            </Button>
          </Dropdown>
          <Tooltip title="清空历史">
            <Button type="text" size="small" danger icon={<DeleteOutlined />} onClick={handleClearHistory} />
          </Tooltip>
        </div>

        <div className="workspace-stream-scroll">
          <ChatArea tasks={tasks as TaskItem[]} />
        </div>
      </div>

      <div className="workspace-composer">
        <div className="workspace-composer-inner">
          <ComposerArea />
        </div>
      </div>
    </div>
  )
}
