import { useState, useEffect, useRef, useCallback } from 'react'
import { Button, Dropdown, message, Tooltip } from 'antd'
import type { MenuProps } from 'antd'
import {
  ClockCircleOutlined,
  DeleteOutlined,
  FilterOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import { getModels, getSessionTasks, listTasks } from '@/api'
import { useGenerationStore } from '@/store/generation'
import type { ModelItem, TaskItem } from '@/types'
import ChatArea from '@/components/ChatArea'
import ComposerArea from '@/components/ComposerArea'
import { CanvasProjectEntry } from '@/pages/CanvasHome'

type FilterType = 'image' | 'video' | 'text' | 'all'

const labelMap: Record<string, string> = {
  image: '图片',
  video: '视频',
  text: '文本',
}

/** 工作台时间（小时）→ listTasks 的 time_range 字符串 */
function hoursToListTimeRange(hours: number): string {
  if (hours <= 0) return 'all'
  if (hours <= 0.5) return '1h'
  if (hours <= 1) return '1h'
  if (hours <= 6) return '6h'
  if (hours <= 24) return '24h'
  if (hours <= 168) return '7d'
  return '30d'
}

export default function Workspace() {
  const {
    activeCategory,
    currentModel,
    tasks,
    sessionId,
    userId,
    setModel,
    setAvailableModels,
    setTasks,
  } = useGenerationStore()
  const [filterType, setFilterType] = useState<FilterType>('all')
  const [timeRange, setTimeRange] = useState<number>(24)
  const [timeRangeLabel, setTimeRangeLabel] = useState('最近 1 天')
  const [isFilterApplied, setIsFilterApplied] = useState(false)
  const [filterLoading, setFilterLoading] = useState(false)
  const loadedCacheKey = useRef<string | null>(null)

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

  const loadTasksWithFilter = useCallback(
    async (
      forceRefresh = false,
      overrides?: { type?: FilterType; hours?: number },
    ) => {
      const type = overrides?.type ?? filterType
      const hours = overrides?.hours ?? timeRange
      const effectiveCategory = type === 'all' ? undefined : type
      const cacheKey = `${sessionId ?? ''}|${userId ?? ''}|${type}|${hours}`

      if (!forceRefresh && loadedCacheKey.current === cacheKey) return

      setFilterLoading(true)
      try {
        let nextTasks: TaskItem[] = []

        // 优先按 session 拉取（创作流同会话）；无 session 时按 user 拉取
        if (sessionId) {
          const res = await getSessionTasks(sessionId, effectiveCategory, hours)
          if (res.code === 'success' && res.data) {
            nextTasks = res.data
          }
        } else if (userId) {
          const res = await listTasks({
            page: 1,
            page_size: 100,
            user_id: userId,
            category: effectiveCategory,
            time_range: hoursToListTimeRange(hours),
          })
          if (res.code === 'success' && res.data?.data) {
            nextTasks = res.data.data as TaskItem[]
          }
        } else {
          const current = useGenerationStore.getState().tasks
          nextTasks = current.filter((t) => {
            if (type !== 'all' && t.category !== type) return false
            if (hours > 0) {
              const cutoff = Date.now() - hours * 3600 * 1000
              if (new Date(t.created_at).getTime() < cutoff) return false
            }
            return true
          })
        }

        setTasks(nextTasks)
        loadedCacheKey.current = cacheKey
      } catch (e) {
        console.error('加载历史任务失败', e)
        message.error('筛选加载失败')
      } finally {
        setFilterLoading(false)
      }
    },
    [filterType, timeRange, sessionId, userId, setTasks],
  )

  useEffect(() => {
    loadTasksWithFilter()
  }, [sessionId, userId])

  const handleTypeFilterChange = (type: FilterType) => {
    setFilterType(type)
    setIsFilterApplied(type !== 'all' || timeRange !== 0)
    loadedCacheKey.current = null
    loadTasksWithFilter(true, { type, hours: timeRange })
  }

  const handleTimeFilterChange = (hours: number, label: string) => {
    setTimeRange(hours)
    setTimeRangeLabel(label)
    setIsFilterApplied(filterType !== 'all' || hours !== 0)
    loadedCacheKey.current = null
    loadTasksWithFilter(true, { type: filterType, hours })
  }

  const handleClearHistory = () => {
    if (tasks.length === 0) return
    if (confirm('确定清空当前历史记录吗？')) {
      setTasks([])
      loadedCacheKey.current = null
      message.success('已清空')
    }
  }

  const handleResetFilter = () => {
    setFilterType('all')
    setTimeRange(24)
    setTimeRangeLabel('最近 1 天')
    setIsFilterApplied(false)
    loadedCacheKey.current = null
    loadTasksWithFilter(true, { type: 'all', hours: 24 })
  }

  const typeMenuItems: MenuProps['items'] = [
    { key: 'all', label: '全部类型' },
    { key: 'image', label: '图片生成' },
    { key: 'video', label: '视频生成' },
    { key: 'text', label: '文本创作' },
  ]

  const timeMenuItems: MenuProps['items'] = [
    { key: '0.5', label: '最近 30 分钟' },
    { key: '1', label: '最近 1 小时' },
    { key: '24', label: '最近 1 天' },
    { key: '168', label: '最近 1 周' },
    { key: '720', label: '最近 1 个月' },
    { key: '0', label: '全部时间' },
  ]

  const timeLabelByKey: Record<string, string> = {
    '0.5': '30分钟',
    '1': '1小时',
    '24': '1天',
    '168': '1周',
    '720': '1月',
    '0': '全部',
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
            trigger={['click']}
            menu={{
              items: typeMenuItems,
              selectedKeys: [filterType],
              onClick: ({ key }) => handleTypeFilterChange(key as FilterType),
            }}
          >
            <Button type="text" size="small" icon={<FilterOutlined />} loading={filterLoading}>
              {filterType === 'all' ? '类型' : labelMap[filterType]}
            </Button>
          </Dropdown>
          <Dropdown
            trigger={['click']}
            menu={{
              items: timeMenuItems,
              selectedKeys: [String(timeRange)],
              onClick: ({ key }) => {
                const hours = Number(key)
                handleTimeFilterChange(hours, timeLabelByKey[key] ?? `${key}小时`)
              },
            }}
          >
            <Button type="text" size="small" icon={<ClockCircleOutlined />} loading={filterLoading}>
              {timeRangeLabel}
            </Button>
          </Dropdown>
          <Tooltip title="清空历史">
            <Button type="text" size="small" danger icon={<DeleteOutlined />} onClick={handleClearHistory} />
          </Tooltip>
        </div>

        <div className="workspace-stream-scroll">
          <div className="workspace-canvas-entry">
            <CanvasProjectEntry />
          </div>
          <ChatArea tasks={tasks as TaskItem[]} />
        </div>

        <div className="workspace-stream-fade" />

        <div className="workspace-composer-float">
          <ComposerArea />
        </div>
      </div>
    </div>
  )
}
