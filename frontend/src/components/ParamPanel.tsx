import { useState, useRef } from 'react'
import { Card, Button, Modal, List, Tag, Input, Space, Empty, message, Upload, Image } from 'antd'
import {
  RobotOutlined,
  SearchOutlined,
  SettingOutlined,
  PictureOutlined,
  DeleteOutlined,
} from '@ant-design/icons'
import { useGenerationStore } from '@/store/generation'
import DynamicForm from './DynamicForm'
import { getModels, uploadImage } from '@/api'
import type { ModelItem } from '@/types'
import { useEffect } from 'react'

const { TextArea } = Input

export default function ParamPanel() {
  const { activeCategory, currentModel, setModel, params, updateParam } = useGenerationStore()
  const [modelModalOpen, setModelModalOpen] = useState(false)
  const [models, setModelsList] = useState<ModelItem[]>([])
  const [searchText, setSearchText] = useState('')
  const [loadingModels, setLoadingModels] = useState(false)
  const [autoLoaded, setAutoLoaded] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadImages, setUploadImages] = useState<{ url: string }[]>(
    params.images || []
  )
  const promptRef = useRef<string>(params.prompt || '')

  const setImages = (images: { url: string }[]) => {
    setUploadImages(images)
    updateParam('images', images)
  }

  const loadModels = async (autoSelect = false) => {
    setLoadingModels(true)
    try {
      const res = await getModels(activeCategory)
      if (res.code === 'success' && res.data) {
        const list = res.data
        setModelsList(list)
        if (autoSelect && !currentModel && list.length > 0) {
          const defaultModel = list.find((m: ModelItem) => m.is_default) || list[0]
          setModel(defaultModel)
          message.success(`已自动选择: ${defaultModel.model_name}`)
        }
      }
    } catch (e) {
      console.error(e)
    } finally {
      setLoadingModels(false)
    }
  }

  useEffect(() => {
    loadModels(true)
  }, [activeCategory])

  useEffect(() => {
    if (modelModalOpen) {
      loadModels(false)
    }
  }, [modelModalOpen])

  useEffect(() => {
    const categoryImages = params.images || []
    if (JSON.stringify(categoryImages) !== JSON.stringify(uploadImages)) {
      setUploadImages(categoryImages)
    }
    if (params.prompt !== undefined && promptRef.current !== params.prompt) {
      promptRef.current = params.prompt
    }
  }, [])

  const categoryLabel = {
    text: '文本',
    image: '图像',
    video: '视频',
  }[activeCategory]

  const filteredModels = models.filter(
    (m) =>
      !searchText ||
      m.model_name.toLowerCase().includes(searchText.toLowerCase()) ||
      m.model_code.toLowerCase().includes(searchText.toLowerCase()) ||
      (m.tags || []).some((t) => t.toLowerCase().includes(searchText.toLowerCase()))
  )

  const handleUploadChange: any = {
    beforeUpload: async (file: File) => {
      setUploading(true)
      try {
        const res = await uploadImage(file)
        if (res.code === 'success' && res.data) {
          setImages([...uploadImages, { url: res.data.url }])
          message.success('上传成功')
        } else {
          message.error('上传失败')
        }
      } catch (e) {
        console.error(e)
        message.error('上传失败')
      } finally {
        setUploading(false)
      }
      return false
    },
    multiple: true,
    showUploadList: false,
    accept: 'image/*',
  }

  const handleRemoveImage = (idx: number) => {
    const newImages = uploadImages.filter((_, i) => i !== idx)
    setImages(newImages)
  }

  return (
    <div>
      <Card
        size="small"
        style={{ marginBottom: 16 }}
        title={
          <Space>
            <RobotOutlined /> 当前模型
          </Space>
        }
        extra={
          <Button
            type="link"
            size="small"
            icon={<SettingOutlined />}
            onClick={() => setModelModalOpen(true)}
          >
            更换模型
          </Button>
        }
      >
        {currentModel ? (
          <div>
            <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 4 }}>
              {currentModel.model_name}
            </div>
            <div style={{ fontSize: 12, color: '#888', marginBottom: 8 }}>
              {currentModel.model_code}
            </div>
            {currentModel.description && (
              <div style={{ fontSize: 12, color: '#666' }}>
                {currentModel.description}
              </div>
            )}
            {(currentModel.tags || []).length > 0 && (
              <div style={{ marginTop: 8 }}>
                {(currentModel.tags || []).map((tag) => (
                  <Tag key={tag} color="blue" style={{ marginBottom: 4 }}>
                    {tag}
                  </Tag>
                ))}
              </div>
            )}
          </div>
        ) : (
          <Empty description={`暂无${categoryLabel}模型`} image={Empty.PRESENTED_IMAGE_SIMPLE} />
        )}
      </Card>

      {activeCategory === 'text' && currentModel && (
        <Card
          size="small"
          style={{ marginBottom: 16 }}
          title="输入内容"
        >
          <TextArea
            rows={5}
            placeholder="请输入要生成的内容描述，例如：写一段关于春天的散文..."
            value={params.prompt || ''}
            onChange={(e) => updateParam('prompt', e.target.value)}
            style={{ marginBottom: 12 }}
          />
          <div style={{ marginBottom: 8, fontSize: 12, color: '#666' }}>
            图片输入（可选，用于图像理解/图文生成）
          </div>
          {uploadImages.length > 0 && (
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(4, 1fr)',
                gap: 6,
                marginBottom: 10,
              }}
            >
              {uploadImages.map((img, idx) => (
              <div
                key={idx}
                style={{
                  position: 'relative',
                  borderRadius: 6,
                  overflow: 'hidden',
                  border: '1px solid #f0f0f0',
                }}
              >
                <Image src={img.url} alt="上传图片" width="100%" height={70} preview={false} style={{ objectFit: 'cover', display: 'block' }} />
                <Button
                  size="small"
                  danger
                  type="text"
                  icon={<DeleteOutlined />}
                  onClick={() => handleRemoveImage(idx)}
                  style={{ position: 'absolute', top: 2, right: 2, padding: '0 4px', fontSize: 12, height: 22 }}
                />
              </div>
            ))}
            </div>
          )}
          <Space>
            <Upload {...handleUploadChange}>
              <Button size="small" icon={<PictureOutlined />} loading={uploading}>
                上传图片
              </Button>
            </Upload>
            <span style={{ fontSize: 12, color: '#888' }}>
              支持多图上传
            </span>
          </Space>
        </Card>
      )}

      {currentModel && <DynamicForm />}

      <Modal
        title={`选择${categoryLabel}模型`}
        open={modelModalOpen}
        onCancel={() => setModelModalOpen(false)}
        footer={null}
        width={640}
      >
        <Input
          placeholder="搜索模型名称/编码/标签"
          prefix={<SearchOutlined />}
          allowClear
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          style={{ marginBottom: 16 }}
        />
        <List
          loading={loadingModels}
          dataSource={filteredModels}
          renderItem={(item) => (
            <List.Item
              key={item.id}
              style={{ cursor: 'pointer', borderBottom: '1px solid #f0f0f0' }}
              onClick={() => {
                setModel(item)
                setModelModalOpen(false)
                message.success(`已选择: ${item.model_name}`)
              }}
            >
              <List.Item.Meta
                title={
                  <Space>
                    <span style={{ fontWeight: 600 }}>{item.model_name}</span>
                    {item.is_default && <Tag color="green">默认</Tag>}
                  </Space>
                }
                description={
                  <div>
                    <div style={{ color: '#888', fontSize: 12, marginBottom: 4 }}>
                      {item.model_code}
                    </div>
                    {item.description && <div style={{ fontSize: 12 }}>{item.description}</div>}
                    {(item.tags || []).length > 0 && (
                      <div style={{ marginTop: 6 }}>
                        {(item.tags || []).map((t) => (
                          <Tag key={t} size="small">
                            {t}
                          </Tag>
                        ))}
                      </div>
                    )}
                  </div>
                }
              />
            </List.Item>
          )}
          locale={{
            emptyText: <Empty description="暂无匹配模型" />,
          }}
        />
      </Modal>
    </div>
  )
}
