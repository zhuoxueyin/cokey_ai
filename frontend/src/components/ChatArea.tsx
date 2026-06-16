import { useState, useEffect, useRef } from 'react'
import {
  Empty,
  Space,
  Tag,
  Button,
  Card,
  message,
  Image,
  Tooltip,
  Modal,
} from 'antd'
import {
  CopyOutlined,
  DownloadOutlined,
  EditOutlined,
  ReloadOutlined,
  FileTextOutlined,
  PictureOutlined,
  VideoCameraOutlined,
  ThunderboltOutlined,
  ClockCircleOutlined,
  RobotOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { useGenerationStore } from '@/store/generation'
import { generate } from '@/api'
import type { TaskItem } from '@/types'

export default function ChatArea({ tasks: tasksProp }: { tasks?: TaskItem[] }) {
  const { currentModel, activeCategory, sessionId, setSessionId } = useGenerationStore()
  const tasksToRender = tasksProp !== undefined ? tasksProp : useGenerationStore((s) => s.tasks)
  const bottomRef = useRef<HTMLDivElement>(null)
  
  // 图片预览状态
  const [previewImageUrl, setPreviewImageUrl] = useState<string | null>(null)
  const [previewImageName, setPreviewImageName] = useState<string>('')

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [tasksToRender.length])

  const handleRegenerate = async (task: TaskItem) => {
    if (!currentModel) {
      message.warning('请先选择模型')
      return
    }

    const taskId = `task_${Date.now()}`
    const tempTask: any = {
      id: taskId,
      task_id: taskId,
      session_id: sessionId,
      model_code: task.model_code,
      category: task.category,
      status: 'processing',
      params: { ...task.params },
      params_summary: (task.params?.prompt || '').substring(0, 60) || '再次生成中...',
      created_at: new Date().toISOString(),
    }
    const store = useGenerationStore.getState()
    // 新任务添加到数组末尾，符合聊天对话习惯（最新的在底部）
    store.setTasks([...store.tasks, tempTask])

    try {
      const res = await generate({
        model_code: task.model_code,
        category: task.category,
        session_id: sessionId ?? undefined,
        user_id: useGenerationStore.getState().userId ?? undefined,
        params: { ...task.params },
      })
      if (res.code === 'success' && res.data) {
        if (!sessionId && (res.data as any).session_id) setSessionId((res.data as any).session_id)
        const s = useGenerationStore.getState()
        const updated = s.tasks.map((t) =>
          t.task_id === taskId
            ? {
                ...t,
                status: 'success',
                result: (res.data as any).result,
                duration_ms: (res.data as any).duration_ms,
              }
            : t
        )
        s.setTasks(updated as any)
        message.success('再次生成完成')
      } else {
        const s = useGenerationStore.getState()
        const updated = s.tasks.map((t) =>
          t.task_id === taskId ? { ...t, status: 'failed', error_message: res.message || '生成失败' } : t
        )
        s.setTasks(updated as any)
      }
    } catch (err: any) {
      const s = useGenerationStore.getState()
      const updated = s.tasks.map((t) =>
        t.task_id === taskId ? { ...t, status: 'failed', error_message: err.message || '生成失败' } : t
      )
      s.setTasks(updated as any)
    }
  }

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text).then(() => {
      message.success('已复制到剪贴板')
    })
  }

  const handleDownload = (url: string, filename?: string) => {
    const link = document.createElement('a')
    link.href = url
    link.download = filename || `aigc_${Date.now()}`
    link.target = '_blank'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  // 图片预览
  const handlePreview = (url: string, name?: string) => {
    setPreviewImageUrl(url)
    setPreviewImageName(name || '图片预览')
  }

  const handleDownloadAll = (images: { url: string }[]) => {
    images.forEach((img, idx) => {
      setTimeout(() => handleDownload(img.url, `image_${idx + 1}.png`), idx * 500)
    })
  }

  const handleEdit = (task: TaskItem) => {
    const store = useGenerationStore.getState()
    if (task.params) {
      // 需求1: 点击再次编辑后，带回到对应类型的任务提交区域，同时带回模型
      store.setParamsWithCategory(task.category as any, { ...task.params }, task.model_code)
      message.info(`已切换到${task.category === 'text' ? '文本创作' : task.category === 'image' ? '图片生成' : '视频生成'}，参数和模型已回填`)
    }
  }

  const renderParamImages = (images: any[]) => (
    <div
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: 6,
        marginTop: 8,
      }}
    >
      {images.map((img, idx) => (
        <div
          key={idx}
          style={{
            width: 50,
            height: 50,
            borderRadius: 4,
            overflow: 'hidden',
            border: '1px solid #e8e8e8',
          }}
        >
          <img src={img.url} alt={`图片 ${idx + 1}`} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
        </div>
      ))}
    </div>
  )

  // 用户消息（右对齐）
  const renderUserMessage = (task: TaskItem) => {
    const icon = {
      text: <FileTextOutlined />,
      image: <PictureOutlined />,
      video: <VideoCameraOutlined />,
    }[task.category]

    return (
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
        <div style={{ maxWidth: '75%' }}>
          <Card
            style={{
              background: '#fff',
              border: '1px solid #e8e8e8',
              borderRadius: 14,
              boxShadow: '0 1px 2px rgba(0,0,0,0.03)',
            }}
            styles={{ body: { padding: 14 } }}
          >
            <div style={{ display: 'flex', gap: 6, marginBottom: 6 }}>
              <div style={{ color: '#1677ff', fontSize: 12 }}>{icon}</div>
              <Tag color="blue" style={{ fontSize: 10, padding: '0 6px', height: 18, lineHeight: '16px' }}>
                {task.model_code}
              </Tag>
              <Tag color="green" style={{ fontSize: 10, padding: '0 6px', height: 18, lineHeight: '16px' }}>
                {task.category === 'text' ? '文本' : task.category === 'image' ? '图片' : '视频'}
              </Tag>
            </div>
            {task.params?.prompt && (
              <div style={{ whiteSpace: 'pre-wrap', fontSize: 13, lineHeight: 1.6, color: '#333' }}>
                {task.params.prompt}
              </div>
            )}
            {task.params?.images && task.params.images.length > 0 && renderParamImages(task.params.images)}
            <div style={{ marginTop: 6, fontSize: 10, color: '#999', textAlign: 'right' }}>
              {new Date(task.created_at).toLocaleString('zh-CN')}
            </div>
          </Card>
        </div>
      </div>
    )
  }

  // AI响应（左对齐）
  const renderAIMessage = (task: TaskItem) => {
    const isProcessing = task.status === 'processing'
    const isFailed = task.status === 'failed'
    const isSuccess = task.status === 'success'

    const result: any = task.result || {}
    const images = result.images || []
    const videos = result.videos || []
    const text = result.text || ''

    return (
      <div style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: 16 }}>
        <div style={{ maxWidth: '85%', width: '100%' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
            <div
              style={{
                width: 24,
                height: 24,
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#fff',
                fontSize: 12,
              }}
            >
              <RobotOutlined />
            </div>
            <span style={{ fontSize: 12, fontWeight: 500 }}>AI 助手</span>
            {task.duration_ms && (
              <span style={{ fontSize: 10, color: '#999' }}>
                <ClockCircleOutlined /> {(task.duration_ms / 1000).toFixed(1)}s
              </span>
            )}
          </div>

          <div style={{ paddingLeft: 30 }}>
            <Card
              style={{
                background: '#fafbff',
                border: '1px solid #e8e8f0',
                borderRadius: 12,
              }}
              styles={{ body: { padding: 16 } }}
            >
              {isProcessing && (
                <div style={{ padding: '16px 0' }}>
                  <Space>
                    <span style={{ color: '#666' }}>
                      <ThunderboltOutlined /> 生成中，请稍候...
                    </span>
                  </Space>
                </div>
              )}

              {isFailed && (
                <div style={{ padding: '8px 0' }}>
                  <div style={{ color: '#ff4d4f', marginBottom: 12 }}>❌ {task.error_message || '生成失败'}</div>
                  <Space>
                    <Button size="small" icon={<ReloadOutlined />} onClick={() => handleRegenerate(task)}>
                      再次生成
                    </Button>
                    <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(task)}>
                      再次编辑
                    </Button>
                  </Space>
                </div>
              )}

              {isSuccess && (
                <div>
                  {text && (
                    <div>
                      <div style={{ whiteSpace: 'pre-wrap', fontSize: 14, lineHeight: 1.8, color: '#333' }}>
                        {text}
                      </div>
                      <Space style={{ marginTop: 12 }}>
                        <Tooltip title="复制">
                          <Button size="small" icon={<CopyOutlined />} onClick={() => handleCopy(text)}>
                            复制
                          </Button>
                        </Tooltip>
                        <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(task)}>
                          再次编辑
                        </Button>
                        <Button size="small" icon={<ReloadOutlined />} onClick={() => handleRegenerate(task)}>
                          再次生成
                        </Button>
                      </Space>
                    </div>
                  )}

                  {images.length > 0 && (
                    <div>
                      <div
                        style={{
                          display: 'grid',
                          gridTemplateColumns: `repeat(${Math.min(images.length, 2)}, 1fr)`,
                          gap: 12,
                        }}
                      >
                        {images.map((img: any, idx: number) => (
                          <div
                            key={idx}
                            style={{
                              borderRadius: 8,
                              overflow: 'hidden',
                              border: '1px solid #f0f0f0',
                              background: '#fff',
                              cursor: 'zoom-in',
                            }}
                            onClick={() => handlePreview(img.url, `生成图片 ${idx + 1}`)}
                          >
                            <Image
                              src={img.url}
                              alt={`生成图片 ${idx + 1}`}
                              width="100%"
                              height={300}
                              style={{ objectFit: 'cover', display: 'block' }}
                              preview={false}
                            />
                          </div>
                        ))}
                      </div>
                      <Space style={{ marginTop: 12 }} wrap>
                        {images.length === 1 ? (
                          <Button size="small" icon={<DownloadOutlined />} onClick={() => handleDownload(images[0].url, 'image.png')}>
                            下载
                          </Button>
                        ) : (
                          <Button size="small" icon={<DownloadOutlined />} onClick={() => handleDownloadAll(images)}>
                            下载全部
                          </Button>
                        )}
                        <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(task)}>
                          再次编辑
                        </Button>
                        <Button size="small" icon={<ReloadOutlined />} onClick={() => handleRegenerate(task)}>
                          再次生成
                        </Button>
                      </Space>
                    </div>
                  )}

                  {videos.length > 0 && (
                    <div>
                      {videos.map((video: any, idx: number) => (
                        <div key={idx} style={{ marginBottom: idx < videos.length - 1 ? 12 : 0 }}>
                          <video src={video.url} controls style={{ width: '100%', maxWidth: 600, borderRadius: 6 }} />
                        </div>
                      ))}
                      <Space style={{ marginTop: 12 }}>
                        {videos.map((video: any, idx: number) => (
                          <Button key={idx} size="small" icon={<DownloadOutlined />} onClick={() => handleDownload(video.url, `video_${idx + 1}.mp4`)}>
                            下载视频 {idx + 1}
                          </Button>
                        ))}
                        <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(task)}>
                          再次编辑
                        </Button>
                        <Button size="small" icon={<ReloadOutlined />} onClick={() => handleRegenerate(task)}>
                          再次生成
                        </Button>
                      </Space>
                    </div>
                  )}

                  {!text && images.length === 0 && videos.length === 0 && (
                    <div style={{ color: '#999', padding: '8px 0' }}>
                      生成完成（无输出内容）
                    </div>
                  )}
                </div>
              )}
            </Card>
          </div>
        </div>
      </div>
    )
  }

  if (tasksToRender.length === 0) {
    return (
      <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 48 }}>
        <Empty
          description={
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 18, marginBottom: 8, color: '#333', fontWeight: 500 }}>
                {activeCategory === 'image' ? '开始你的AI图片创作' : activeCategory === 'video' ? '开始你的AI视频创作' : '开始你的AI文本创作'}
              </div>
              <div style={{ fontSize: 13, color: '#999' }}>在下方输入描述，或上传图片，点击"立即生成"开始创作</div>
            </div>
          }
        />
      </div>
    )
  }

  return (
    <div style={{ padding: '24px 48px 0' }}>
      {tasksToRender.map((task) => (
        <div key={task.task_id}>
          {renderUserMessage(task)}
          {renderAIMessage(task)}
        </div>
      ))}
      <div ref={bottomRef} />

      {/* 图片预览 Modal */}
      <Modal
        open={!!previewImageUrl}
        onCancel={() => setPreviewImageUrl(null)}
        footer={
          <Space>
            <Button icon={<DownloadOutlined />} onClick={() => previewImageUrl && handleDownload(previewImageUrl, previewImageName)}>
              下载
            </Button>
            <Button onClick={() => setPreviewImageUrl(null)}>关闭</Button>
          </Space>
        }
        centered
        width={900}
      >
        {previewImageUrl && (
          <div>
            <div style={{ marginBottom: 12, fontSize: 14, fontWeight: 500 }}>{previewImageName}</div>
            <div style={{ textAlign: 'center', background: '#f5f5f5', padding: 16, borderRadius: 6 }}>
              <Image
                src={previewImageUrl}
                preview={false}
                style={{ maxWidth: '100%', maxHeight: 600 }}
              />
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
