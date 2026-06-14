import { useState } from 'react'
import { Card, Button, Modal, List, Tag, Input, Space, Empty, message } from 'antd'
import {
  RobotOutlined,
  SearchOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import { useGenerationStore } from '@/store/generation'
import DynamicForm from './DynamicForm'
import { getModels } from '@/api'
import type { ModelItem } from '@/types'
import { useEffect } from 'react'

export default function ParamPanel() {
  const { activeCategory, currentModel, setModel, params } = useGenerationStore()
  const [modelModalOpen, setModelModalOpen] = useState(false)
  const [models, setModelsList] = useState<ModelItem[]>([])
  const [searchText, setSearchText] = useState('')
  const [loadingModels, setLoadingModels] = useState(false)

  const loadModels = async () => {
    setLoadingModels(true)
    try {
      const res = await getModels(activeCategory)
      if (res.code === 'success' && res.data) {
        setModelsList(res.data)
      }
    } catch (e) {
      console.error(e)
    } finally {
      setLoadingModels(false)
    }
  }

  useEffect(() => {
    if (modelModalOpen) {
      loadModels()
    }
  }, [modelModalOpen, activeCategory])

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
