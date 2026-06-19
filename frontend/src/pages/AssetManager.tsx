import { useState, useEffect, useRef } from 'react'
import { Card, Tabs, Pagination, Empty, Image, Button, Space, Tag, message, Upload, Modal, Input, DatePicker, Dropdown } from 'antd'
import type { MenuProps } from 'antd'
import { DeleteOutlined, UploadOutlined, DownloadOutlined, PictureOutlined, VideoCameraOutlined, FileOutlined, FilterOutlined, SearchOutlined, EyeOutlined } from '@ant-design/icons'
import { listAssets, uploadAsset, deleteAsset } from '@/api'
import type { AssetItem } from '@/types'
import { downloadRemoteFile } from '@/utils/download'
import { formatServerDateTime, parseServerDateTime } from '@/utils/formatDateTime'

const { RangePicker } = DatePicker

export default function AssetManager() {
  const [activeTab, setActiveTab] = useState<'all' | 'upload' | 'generated'>('all')
  const [items, setItems] = useState<AssetItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(24)
  const [loading, setLoading] = useState(false)
  const [searchText, setSearchText] = useState('')
  const [previewItem, setPreviewItem] = useState<AssetItem | null>(null)
  const [previewOpen, setPreviewOpen] = useState(false)

  const loadList = async () => {
    setLoading(true)
    try {
      const res = await listAssets({
        page,
        page_size: pageSize,
        source_type: activeTab === 'all' ? undefined : activeTab,
      })
      if (res.code === 'success' && res.data) {
        let list = res.data.items
        if (searchText) {
          list = list.filter(it => it.file_name.toLowerCase().includes(searchText.toLowerCase()))
        }
        setItems(list)
        setTotal(res.data.total)
      }
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadList()
  }, [activeTab, page, pageSize])

  const handleSearch = () => {
    setPage(1)
    loadList()
  }

  const handleUploadChange: any = {
    beforeUpload: async (file: File) => {
      try {
        const res = await uploadAsset(file, {
          category: file.type.startsWith('image') ? 'image' : file.type.startsWith('video') ? 'video' : 'file',
          source_type: 'upload',
        })
        if (res.code === 'success') {
          message.success(`上传成功: ${file.name}`)
          setPage(1)
          loadList()
        }
      } catch (e) {
        message.error(`上传失败: ${file.name}`)
      }
      return false
    },
    multiple: true,
    showUploadList: false,
  }

  const handleDelete = async (asset: AssetItem) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定删除 "${asset.file_name}" 吗？`,
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          const res = await deleteAsset(asset.id)
          if (res.code === 'success') {
            message.success('已删除')
            loadList()
          }
        } catch (e) {
          message.error('删除失败')
        }
      },
    })
  }

  const handlePreview = (asset: AssetItem) => {
    setPreviewItem(asset)
    setPreviewOpen(true)
  }

  const handleDownload = async (asset: AssetItem) => {
    const hide = message.loading('正在下载...', 0)
    try {
      await downloadRemoteFile(asset.url, asset.file_name)
      message.success('下载成功')
    } catch {
      window.open(asset.url, '_blank', 'noopener,noreferrer')
      message.warning('无法直接保存，已在新标签页打开，请右键另存为')
    } finally {
      hide()
    }
  }

  const renderIcon = (item: AssetItem) => {
    if (item.category === 'image') return <PictureOutlined />
    if (item.category === 'video') return <VideoCameraOutlined />
    return <FileOutlined />
  }

  const renderCard = (item: AssetItem) => (
    <Card
      key={item.id}
      size="small"
      hoverable
      style={{ marginBottom: 8 }}
      styles={{ body: { padding: 8 } }}
      cover={
        item.category === 'image' ? (
          <div
            style={{
              height: 180,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: '#f5f5f5',
              cursor: 'pointer',
              overflow: 'hidden',
            }}
            onClick={() => handlePreview(item)}
          >
            <Image
              src={item.url}
              alt={item.file_name}
              preview={false}
              style={{ maxWidth: '100%', maxHeight: 180, objectFit: 'contain' }}
            />
          </div>
        ) : item.category === 'video' ? (
          <div
            style={{
              height: 180,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: '#000',
              cursor: 'pointer',
            }}
            onClick={() => handlePreview(item)}
          >
            <video src={item.url} style={{ maxWidth: '100%', maxHeight: 180 }} />
          </div>
        ) : (
          <div
            style={{
              height: 180,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              background: '#f5f5f5',
              fontSize: 40,
              color: '#999',
              cursor: 'pointer',
            }}
            onClick={() => handleDownload(item)}
          >
            {renderIcon(item)}
            <div style={{ fontSize: 12, marginTop: 8, color: '#666' }}>{item.file_name}</div>
          </div>
        )
      }
    >
      <div style={{ fontSize: 12, color: '#333', marginBottom: 4, overflow: 'hidden', whiteSpace: 'nowrap', textOverflow: 'ellipsis' }}>
        {item.file_name}
      </div>
      <div style={{ marginBottom: 6 }}>
        <Tag color={item.source_type === 'generated' ? 'purple' : 'blue'} style={{ fontSize: 11, padding: '0 6px', height: 20, lineHeight: '18px' }}>
          {item.source_type === 'generated' ? 'AI生成' : '用户上传'}
        </Tag>
        {item.category === 'image' && <Tag color="green" style={{ fontSize: 11, padding: '0 6px', height: 20, lineHeight: '18px' }}>图片</Tag>}
        {item.category === 'video' && <Tag color="cyan" style={{ fontSize: 11, padding: '0 6px', height: 20, lineHeight: '18px' }}>视频</Tag>}
        {item.category === 'file' && <Tag color="orange" style={{ fontSize: 11, padding: '0 6px', height: 20, lineHeight: '18px' }}>文件</Tag>}
      </div>
      <div style={{ fontSize: 11, color: '#999', marginBottom: 8 }}>
        {formatServerDateTime(item.created_at)}
      </div>
      <Space size={4}>
        <Button size="small" type="text" icon={<EyeOutlined />} onClick={() => handlePreview(item)}>
          预览
        </Button>
        <Button size="small" type="text" icon={<DownloadOutlined />} onClick={() => handleDownload(item)}>
          下载
        </Button>
        <Button size="small" type="text" danger icon={<DeleteOutlined />} onClick={() => handleDelete(item)}>
          删除
        </Button>
      </Space>
    </Card>
  )

  const tabItems = [
    { key: 'all', label: <span>全部资源 ({total})</span> },
    { key: 'upload', label: <span>我的上传</span> },
    { key: 'generated', label: <span>AI生成资源</span> },
  ]

  return (
    <div style={{ padding: 24, height: '100%', overflowY: 'auto', boxSizing: 'border-box' }}>
      <Card
        style={{ marginBottom: 16 }}
        title={<Space><PictureOutlined /><span>资源管理</span></Space>}
        extra={
          <Space>
            <Input
              placeholder="搜索文件名"
              prefix={<SearchOutlined />}
              allowClear
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              onPressEnter={handleSearch}
              style={{ width: 220 }}
            />
            <Upload {...handleUploadChange}>
              <Button type="primary" icon={<UploadOutlined />}>
                上传资源
              </Button>
            </Upload>
          </Space>
        }
      >
        <Tabs
          activeKey={activeTab}
          onChange={(k) => {
            setActiveTab(k as any)
            setPage(1)
          }}
          items={tabItems}
          style={{ marginBottom: 16 }}
        />

        {items.length === 0 && !loading ? (
          <Empty description="暂无资源，可点击右上角上传">
            <Upload {...handleUploadChange}>
              <Button type="primary" icon={<UploadOutlined />}>
                上传资源
              </Button>
            </Upload>
          </Empty>
        ) : (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
              gap: 16,
            }}
          >
            {items.map((item) => renderCard(item))}
          </div>
        )}

        {total > 0 && (
          <div style={{ marginTop: 24, textAlign: 'center' }}>
            <Pagination
              current={page}
              pageSize={pageSize}
              total={total}
              onChange={(p, ps) => {
                setPage(p)
                setPageSize(ps)
              }}
              showSizeChanger
              showTotal={(t) => `共 ${t} 项资源`}
            />
          </div>
        )}
      </Card>

      <Modal
        open={previewOpen}
        onCancel={() => setPreviewOpen(false)}
        footer={
          <Space>
            <Button icon={<DownloadOutlined />} onClick={() => previewItem && handleDownload(previewItem)}>
              下载
            </Button>
            <Button onClick={() => setPreviewOpen(false)}>关闭</Button>
          </Space>
        }
        centered
        width={800}
      >
        {previewItem && (
          <div>
            <div style={{ marginBottom: 12, fontSize: 14, fontWeight: 500 }}>{previewItem.file_name}</div>
            {previewItem.category === 'image' && (
              <div style={{ textAlign: 'center', background: '#f5f5f5', padding: 16, borderRadius: 6 }}>
                <Image
                  src={previewItem.url}
                  preview={false}
                  style={{ maxWidth: '100%', maxHeight: 500 }}
                />
              </div>
            )}
            {previewItem.category === 'video' && (
              <video src={previewItem.url} controls style={{ width: '100%', maxHeight: 500 }} />
            )}
            {previewItem.category === 'file' && (
              <div style={{ textAlign: 'center', padding: 48, fontSize: 14 }}>
                <FileOutlined style={{ fontSize: 64, color: '#999' }} />
                <div style={{ marginTop: 12 }}>{previewItem.file_name}</div>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}
