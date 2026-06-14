import { useState, useEffect, useRef } from 'react'
import {
  Empty,
  Space,
  Tag,
  Button,
  Card,
  message,
  Modal,
  Image,
  Input,
  Tooltip,
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
} from '@ant-design/icons'
import { useGenerationStore } from '@/store/generation'
import { generate } from '@/api'
import type { TaskItem } from '@/types'

const { TextArea } = Input

export default function ChatArea() {
  const { tasks, setTasks, currentModel, params, setParams, activeCategory, sessionId, setSessionId } = useGenerationStore()
  const [previewVisible, setPreviewVisible] = useState(false)
  const [previewImages, setPreviewImages] = useState<string[]>([])
  const [previewIndex, setPreviewIndex] = useState(0)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [tasks.length])

  const handleEdit = (task: TaskItem) => {
    if (task.params) {
      setParams({ ...task.params })
      message.info('已将参数回填到左侧表单，可修改后重新生成')
    }
  }

  const handleRegenerate = async (task: TaskItem) => {
    if (!currentModel) {
      message.warning('请先选择模型')
      return
    }

    const regenerateParams = task.params || params
    const taskId = `task_${Date.now()}`
    const tempTask: any = {
      id: taskId,
      task_id: taskId,
      session_id: sessionId,
      model_code: task.model_code,
      category: task.category,
      status: 'processing',
      params: { ...regenerateParams },
      params_summary: regenerateParams.prompt || regenerateParams.positive_prompt || '重新生成中...',
      created_at: new Date().toISOString(),
    }
    const store = useGenerationStore.getState()
    store.setTasks([...store.tasks, tempTask])

    try {
      const res = await generate({
        model_code: task.model_code,
        category: task.category,
        session_id: sessionId,
        params: { ...regenerateParams },
      })
      if (res.code === 'success' && res.data) {
        if (!sessionId && res.data.session_id) setSessionId(res.data.session_id)
        const s = useGenerationStore.getState()
        const updated = s.tasks.map((t) =>
          t.task_id === taskId
            ? {
                ...t,
                status: 'success',
                result: res.data.result,
                duration_ms: res.data.duration_ms,
              }
            : t
        )
        s.setTasks(updated)
        message.success('重新生成完成')
      } else {
        const s = useGenerationStore.getState()
        const updated = s.tasks.map((t) =>
          t.task_id === taskId
            ? { ...t, status: 'failed', error_message: res.message || '生成失败' }
            : t
        )
        s.setTasks(updated)
      }
    } catch (err: any) {
      const s = useGenerationStore.getState()
      const updated = s.tasks.map((t) =>
        t.task_id === taskId
          ? { ...t, status: 'failed', error_message: err.message || '生成失败' }
          : t
      )
      s.setTasks(updated)
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

  const handleDownloadAll = (images: { url: string }[]) => {
    images.forEach((img, idx) => {
      setTimeout(() => handleDownload(img.url, `image_${idx + 1}.png`), idx * 500)
    })
  }

  const handlePreview = (urls: string[], index: number) => {
    setPreviewImages(urls)
    setPreviewIndex(index)
    setPreviewVisible(true)
  }

  const renderUserMessage = (task: TaskItem) => {
    const icon = {
      text: <FileTextOutlined />,
      image: <PictureOutlined />,
      video: <VideoCameraOutlined />,
    }[task.category]

    return (
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
        <div style={{ maxWidth: '70%' }}>
          <div style={{ textAlign: 'right', marginBottom: 6, fontSize: 12, color: '#888' }}>
            <Space>
              <Tag color="blue">{task.model_code}</Tag>
              <span>{new Date(task.created_at).toLocaleString('zh-CN')}</span>
            </Space>
          </div>
          <Card
            size="small"
            style={{
              background: '#e6f4ff',
              border: '1px solid #91caff',
              borderRadius: 8,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
              <span style={{ color: '#1677ff' }}>{icon}</span>
              <div style={{ flex: 1 }}>
                {task.params?.prompt && (
                  <div style={{ whiteSpace: 'pre-wrap' }}>{task.params.prompt}</div>
                )}
                {!task.params?.prompt && task.params?.positive_prompt && (
                  <div style={{ whiteSpace: 'pre-wrap' }}>{task.params.positive_prompt}</div>
                )}
                {!task.params?.prompt && !task.params?.positive_prompt && (
                  <div style={{ color: '#666' }}>{task.params_summary}</div>
                )}
                {Object.keys(task.params || {})
                  .filter((k) => !['prompt', 'positive_prompt', 'negative_prompt'].includes(k))
                  .slice(0, 3)
                  .map((k) => (
                    <Tag key={k} style={{ marginTop: 6 }} color="geekblue" size="small">
                      {k}: {String(task.params?.[k]).slice(0, 20)}
                    </Tag>
                  ))}
              </div>
            </div>
          </Card>
        </div>
      </div>
    )
  }

  const renderAIMessage = (task: TaskItem) => {
    const isProcessing = task.status === 'processing'
    const isFailed = task.status === 'failed'
    const isSuccess = task.status === 'success'

    return (
      <div style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: 24 }}>
        <div style={{ maxWidth: '80%', width: '100%' }}>
          <div style={{ marginBottom: 6, fontSize: 12, color: '#888' }}>
            <Space>
              <Tag color="purple">AI</Tag>
              {task.duration_ms && <span><ClockCircleOutlined /> {(task.duration_ms / 1000).toFixed(1)}s</span>}
            </Space>
          </div>
          <Card
            size="small"
            style={{
              background: '#fff',
              border: '1px solid #d9d9d9',
              borderRadius: 8,
            }}
          >
            {isProcessing && (
              <div style={{ padding: '16px 0' }}>
                <Space>
                  <span className="animate-pulse">
                    <ThunderboltOutlined /> 生成中，请稍候...
                  </span>
                </Space>
              </div>
            )}

            {isFailed && (
              <div style={{ padding: '8px 0' }}>
                <div style={{ color: '#ff4d4f', marginBottom: 12 }}>
                  ❌ {task.error_message || '生成失败'}
                </div>
                <Space>
                  <Button size="small" icon={<ReloadOutlined />} onClick={() => handleRegenerate(task)}>
                    重新生成
                  </Button>
                  <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(task)}>
                    编辑参数
                  </Button>
                </Space>
              </div>
            )}

            {isSuccess && task.result && (
              <div>
                {task.result.type === 'text' && task.result.text && (
                  <div>
                    <div
                      style={{
                        whiteSpace: 'pre-wrap',
                        lineHeight: 1.8,
                        padding: '8px 0',
                      }}
                    >
                      {task.result.text}
                    </div>
                    <Space style={{ marginTop: 8 }}>
                      <Tooltip title="复制">
                        <Button size="small" icon={<CopyOutlined />} onClick={() => handleCopy(task.result.text!)}>
                          复制
                        </Button>
                      </Tooltip>
                      <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(task)}>
                        编辑参数
                      </Button>
                      <Button size="small" icon={<ReloadOutlined />} onClick={() => handleRegenerate(task)}>
                        重新生成
                      </Button>
                    </Space>
                  </div>
                )}

                {task.result.type === 'image' && task.result.images && task.result.images.length > 0 && (
                  <div>
                    <div
                      style={{
                        display: 'grid',
                        gridTemplateColumns: `repeat(${Math.min(task.result.images.length, 2)}, 1fr)`,
                        gap: 8,
                        padding: '8px 0',
                      }}
                    >
                      {task.result.images.map((img, idx) => (
                        <div
                          key={idx}
                          style={{
                            cursor: 'pointer',
                            borderRadius: 6,
                            overflow: 'hidden',
                            border: '1px solid #f0f0f0',
                          }}
                          onClick={() =>
                            handlePreview(
                              task.result.images!.map((i) => i.url),
                              idx
                            )
                          }
                        >
                          <Image
                            src={img.url}
                            alt={`生成图片 ${idx + 1}`}
                            width="100%"
                            height={200}
                            style={{ objectFit: 'cover', display: 'block' }}
                            preview={false}
                          />
                        </div>
                      ))}
                    </div>
                    <Space style={{ marginTop: 8 }} wrap>
                      {task.result.images.length === 1 ? (
                        <Button
                          size="small"
                          icon={<DownloadOutlined />}
                          onClick={() => handleDownload(task.result.images![0].url, 'image.png')}
                        >
                          下载
                        </Button>
                      ) : (
                        <Button
                          size="small"
                          icon={<DownloadOutlined />}
                          onClick={() => handleDownloadAll(task.result.images!)}
                        >
                          下载全部
                        </Button>
                      )}
                      <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(task)}>
                        编辑参数
                      </Button>
                      <Button size="small" icon={<ReloadOutlined />} onClick={() => handleRegenerate(task)}>
                        重新生成
                      </Button>
                    </Space>
                  </div>
                )}

                {task.result.type === 'video' && task.result.videos && task.result.videos.length > 0 && (
                  <div>
                    {task.result.videos.map((video, idx) => (
                      <div key={idx} style={{ marginBottom: idx < task.result.videos!.length - 1 ? 12 : 0 }}>
                        <video
                          src={video.url}
                          controls
                          style={{ width: '100%', maxWidth: 600, borderRadius: 6 }}
                        />
                      </div>
                    ))}
                    <Space style={{ marginTop: 8 }}>
                      {task.result.videos.map((video, idx) => (
                        <Button
                          key={idx}
                          size="small"
                          icon={<DownloadOutlined />}
                          onClick={() => handleDownload(video.url, `video_${idx + 1}.mp4`)}
                        >
                          下载视频 {idx + 1}
                        </Button>
                      ))}
                      <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(task)}>
                        编辑参数
                      </Button>
                      <Button size="small" icon={<ReloadOutlined />} onClick={() => handleRegenerate(task)}>
                        重新生成
                      </Button>
                    </Space>
                  </div>
                )}
              </div>
            )}
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div style={{ padding: 24, minHeight: '100%' }}>
      {tasks.length === 0 ? (
        <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Empty
            description={
              <div>
                <div style={{ fontSize: 16, marginBottom: 8 }}>开始你的AIGC创作之旅</div>
                <div style={{ fontSize: 13, color: '#999' }}>在左侧填写参数，点击"立即生成"开始创作</div>
              </div>
            }
            style={{ padding: 40 }}
          />
        </div>
      ) : (
        <div>
          {tasks.map((task) => (
            <div key={task.task_id}>
              {renderUserMessage(task)}
              {renderAIMessage(task)}
            </div>
          ))}
          <div ref={bottomRef} />
        </div>
      )}

      <Modal
        title="图片预览"
        open={previewVisible}
        onCancel={() => setPreviewVisible(false)}
        footer={null}
        width={800}
        destroyOnClose
      >
        <Image.PreviewGroup
          preview={{
            current: previewIndex,
            onChange: (current) => setPreviewIndex(current),
            visible: previewVisible,
            onVisibleChange: (visible) => setPreviewVisible(visible),
          }}
        >
          {previewImages.map((url, idx) => (
            <Image key={idx} src={url} style={{ display: 'none' }} />
          ))}
        </Image.PreviewGroup>
        <div style={{ textAlign: 'center', padding: 20 }}>
          <Image src={previewImages[previewIndex]} alt="预览" style={{ maxWidth: '100%', maxHeight: 500 }} preview={false} />
        </div>
      </Modal>
    </div>
  )
}
