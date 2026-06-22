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
import { downloadRemoteFile } from '@/utils/download'
import { formatServerDateTime, parseServerDateTime } from '@/utils/formatDateTime'

export default function ChatArea({ tasks: tasksProp }: { tasks?: TaskItem[] }) {
  const { currentModel, activeCategory, sessionId, setSessionId } = useGenerationStore()
  const rawTasks = tasksProp !== undefined ? tasksProp : useGenerationStore((s) => s.tasks)
  
  // 🔧 前端按 created_at 升序排序（最早在前，最新在底部）
  // 不依赖后端或 store 的顺序，确保渲染正确
  const tasksToRender = [...rawTasks].sort((a, b) => 
    (parseServerDateTime(a.created_at)?.getTime() ?? 0) - (parseServerDateTime(b.created_at)?.getTime() ?? 0),
  )
  
  const bottomRef = useRef<HTMLDivElement>(null)
  
  // 图片预览状态
  const [previewImageUrl, setPreviewImageUrl] = useState<string | null>(null)
  const [previewImageName, setPreviewImageName] = useState<string>('')
  const [downloading, setDownloading] = useState(false)

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

  const handleDownload = async (url: string, filename?: string) => {
    setDownloading(true)
    const hide = message.loading('正在下载...', 0)
    try {
      await downloadRemoteFile(url, filename)
      message.success('下载成功')
    } catch {
      window.open(url, '_blank', 'noopener,noreferrer')
      message.warning('无法直接保存，已在新标签页打开，请右键另存为')
    } finally {
      hide()
      setDownloading(false)
    }
  }

  const handleDownloadAll = (images: { url: string }[]) => {
    images.forEach((img, idx) => {
      setTimeout(() => {
        void handleDownload(img.url, `image_${idx + 1}.png`)
      }, idx * 600)
    })
  }

  const handlePreview = (url: string, name?: string) => {
    setPreviewImageUrl(url)
    setPreviewImageName(name || '图片预览')
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
      {images.map((img, idx) => {
        const src = typeof img === 'string' ? img : (img.cdn_url ?? img.url)
        return (
        <div
          key={idx}
          className="chat-msg-param-thumb"
          style={{
            width: 50,
            height: 50,
            borderRadius: 4,
            overflow: 'hidden',
          }}
        >
          <img src={src} alt={`图片 ${idx + 1}`} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
        </div>
        )
      })}
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
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 12 }}>
        <div style={{ maxWidth: '78%' }}>
          <Card
            className="chat-msg-card chat-msg-card--user"
            styles={{ body: { padding: '10px 12px' } }}
          >
            <div style={{ display: 'flex', gap: 4, marginBottom: 4 }}>
              <div style={{ color: '#7c5cfc', fontSize: 11 }}>{icon}</div>
              <Tag color="purple" style={{ fontSize: 10, padding: '0 5px', height: 16, lineHeight: '14px', margin: 0 }}>
                {task.model_code}
              </Tag>
              <Tag style={{ fontSize: 10, padding: '0 5px', height: 16, lineHeight: '14px', margin: 0 }}>
                {task.category === 'text' ? '文本' : task.category === 'image' ? '图片' : '视频'}
              </Tag>
            </div>
            {task.params?.prompt && (
              <div className="chat-msg-prompt">{task.params.prompt}</div>
            )}
            {task.params?.images && task.params.images.length > 0 && renderParamImages(task.params.images)}
            <div className="chat-msg-time">{formatServerDateTime(task.created_at)}</div>
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
      <div style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: 12 }}>
        <div style={{ maxWidth: '95%', width: '100%' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 5, marginBottom: 4 }}>
            <div
              style={{
                width: 22,
                height: 22,
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #7c5cfc 0%, #a78bfa 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#fff',
                fontSize: 11,
              }}
            >
              <RobotOutlined />
            </div>
            <span className="chat-msg-ai-label">AI</span>
            {task.duration_ms && (
              <span className="chat-msg-ai-duration">
                <ClockCircleOutlined /> {(task.duration_ms / 1000).toFixed(1)}s
              </span>
            )}
          </div>

          <div style={{ paddingLeft: 28 }}>
            <Card
              className="chat-msg-card chat-msg-card--ai"
              styles={{ body: { padding: '10px 12px' } }}
            >
              {isProcessing && (
                <div style={{ padding: '8px 0' }}>
                  <Space>
                    <span style={{ color: 'var(--ws-text-secondary)' }}>
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
      <div className="workspace-stream-content" style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 200, paddingBottom: 80 }}>
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description={
            <span style={{ fontSize: 13, color: '#aaa' }}>
              在下方输入描述开始创作
            </span>
          }
        />
      </div>
    )
  }

  return (
    <div className="workspace-stream-content">
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
            <Button
              icon={<DownloadOutlined />}
              loading={downloading}
              onClick={() => previewImageUrl && handleDownload(previewImageUrl, previewImageName)}
            >
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
