import { useState, useRef } from 'react'
import { Card, Button, List, Tag, Input, Space, Empty, message, Upload, Image } from 'antd'
import {
  RobotOutlined,
  SearchOutlined,
  PictureOutlined,
  DeleteOutlined,
} from '@ant-design/icons'
import { useGenerationStore } from '@/store/generation'
import DynamicForm from './DynamicForm'
import { getModels, uploadImage } from '@/api'
import type { ModelItem } from '@/types'
import { useEffect } from 'react'
import { type ImageRef, normalizeImageRef, pickCdnUrl } from '@/utils/cdnUrl'

const { TextArea } = Input

export default function ParamPanel() {
  const { activeCategory, currentModel, setModel, params, updateParam } = useGenerationStore()
  const [models, setModelsList] = useState<ModelItem[]>([])
  const [searchText, setSearchText] = useState('')
  const [loadingModels, setLoadingModels] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadImages, setUploadImages] = useState<ImageRef[]>(
    (params.images || [])
      .map((img: any) => normalizeImageRef(img))
      .filter((ref): ref is ImageRef => ref !== null),
  )

  const setImages = (images: ImageRef[]) => {
    setUploadImages(images)
    updateParam('images', images.map((img) => img.cdn_url))
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
    const categoryImages = (params.images || [])
      .map((img: any) => normalizeImageRef(img))
      .filter((ref): ref is ImageRef => ref !== null)
    if (JSON.stringify(categoryImages.map((i) => i.cdn_url)) !== JSON.stringify(uploadImages.map((i) => i.cdn_url))) {
      setUploadImages(categoryImages)
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
          try {
            const cdnUrl = pickCdnUrl(res.data)
            setImages([...uploadImages, { cdn_url: cdnUrl }])
            message.success('上传成功')
          } catch {
            message.error('上传成功但未获得有效 CDN 地址，请检查存储配置')
          }
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

  const renderImageGrid = () => {
    if (uploadImages.length === 0) return null
    return (
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
            <Image
              src={img.cdn_url}
              alt="上传图片"
              width="100%"
              height={70}
              preview={false}
              style={{ objectFit: 'cover', display: 'block' }}
            />
            <Button
              size="small"
              danger
              type="text"
              icon={<DeleteOutlined />}
              onClick={() => handleRemoveImage(idx)}
              style={{
                position: 'absolute',
                top: 2,
                right: 2,
                padding: '0 4px',
                fontSize: 12,
                height: 22,
              }}
            />
          </div>
        ))}
      </div>
    )
  }

  const renderUploadButton = (label = '上传图片') => (
    <Space>
      <Upload {...handleUploadChange}>
        <Button size="small" icon={<PictureOutlined />} loading={uploading}>
          {label}
        </Button>
      </Upload>
      <span style={{ fontSize: 12, color: '#888' }}>
        支持多图上传
      </span>
    </Space>
  )

  return (
    <div>
      <Card
        size="small"
        style={{ marginBottom: 16 }}
        title={
          <Space>
            <RobotOutlined /> 选择{categoryLabel}模型
          </Space>
        }
      >
        <Input
          placeholder="搜索模型名称/编码/标签"
          prefix={<SearchOutlined />}
          allowClear
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          style={{ marginBottom: 12 }}
        />
        <List
          size="small"
          loading={loadingModels}
          dataSource={filteredModels}
          renderItem={(item) => {
            const isActive = currentModel && currentModel.model_code === item.model_code
            return (
              <List.Item
                key={item.id}
                style={{
                  cursor: 'pointer',
                  borderBottom: '1px solid #f0f0f0',
                  background: isActive ? '#e6f4ff' : 'transparent',
                  padding: '10px 12px',
                }}
                onClick={() => {
                  setModel(item)
                  message.success(`已选择: ${item.model_name}`)
                }}
              >
                <List.Item.Meta
                  title={
                    <Space>
                      <span style={{ fontWeight: 600 }}>{item.model_name}</span>
                      {item.is_default && <Tag color="green">默认</Tag>}
                      {isActive && <Tag color="blue">已选</Tag>}
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
                            <Tag key={t}>
                              {t}
                            </Tag>
                          ))}
                        </div>
                      )}
                    </div>
                  }
                />
              </List.Item>
            )
          }}
          locale={{
            emptyText: <Empty description="暂无匹配模型" />,
          }}
        />
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
          {renderImageGrid()}
          {renderUploadButton()}
        </Card>
      )}

      {activeCategory === 'image' && currentModel && (
        <Card
          size="small"
          style={{ marginBottom: 16 }}
          title="图像描述"
        >
          <TextArea
            rows={5}
            placeholder="请输入图像描述，例如：一只白色的猫坐在沙发上，光线柔和..."
            value={params.prompt || ''}
            onChange={(e) => updateParam('prompt', e.target.value)}
            style={{ marginBottom: 12 }}
          />
          <div style={{ marginBottom: 8, fontSize: 12, color: '#666' }}>
            图片（可选，用于图像生成/图生图）
          </div>
          {renderImageGrid()}
          {renderUploadButton('上传图片')}
        </Card>
      )}

      {currentModel && <DynamicForm />}
    </div>
  )
}
