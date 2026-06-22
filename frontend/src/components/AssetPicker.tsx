import { useState, useEffect, useCallback } from 'react'
import { Modal, Tabs, Upload, Button, Space, Image, Empty, message, Pagination, Tag, Input, Spin } from 'antd'
import { UploadOutlined, PictureOutlined, SearchOutlined, CheckOutlined, AppstoreOutlined } from '@ant-design/icons'
import { listAssets, uploadAsset } from '@/api'
import { getCanvasProject } from '@/api/canvas'
import type { AssetItem } from '@/types'
import type { DramaAgentRef } from '@/types/dramaAgent'
import { assetDisplayUrl, isAssetCdnReady, isCdnUrl, pickCdnUrl } from '@/utils/cdnUrl'
import { assetToAgentRef, collectCanvasAgentRefs } from '@/utils/dramaAgentRefs'

interface AssetPickerProps {
  open: boolean
  onClose: () => void
  onSelect?: (assets: AssetItem[]) => void
  /** 创作助手：返回 DramaAgentRef（含画布节点） */
  onSelectRefs?: (refs: DramaAgentRef[]) => void
  multiple?: boolean
  category?: 'image' | 'video' | 'file'
  maxCount?: number
  /** 单选模式下上传成功后立即选中并关闭（如风格封面） */
  autoApplyOnUpload?: boolean
  /** 画布项目 ID：开启「当前画布」标签页 */
  canvasProjectId?: string
  /** 侧栏内打开时提高层级，避免被画布遮挡 */
  zIndex?: number
}

export default function AssetPicker({
  open,
  onClose,
  onSelect,
  onSelectRefs,
  multiple = true,
  category = 'image',
  maxCount = 20,
  autoApplyOnUpload = false,
  canvasProjectId,
  zIndex = 3000,
}: AssetPickerProps) {
  const [activeTab, setActiveTab] = useState<'library' | 'upload' | 'canvas'>('library')
  const [items, setItems] = useState<AssetItem[]>([])
  const [canvasRefs, setCanvasRefs] = useState<DramaAgentRef[]>([])
  const [canvasLoading, setCanvasLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(32)
  const [loading, setLoading] = useState(false)
  const [selectedIds, setSelectedIds] = useState<string[]>([])
  const [selectedCanvasKeys, setSelectedCanvasKeys] = useState<string[]>([])
  const [searchText, setSearchText] = useState('')

  const useRefMode = Boolean(onSelectRefs)

  const loadCanvasRefs = useCallback(async () => {
    if (!canvasProjectId) return
    setCanvasLoading(true)
    try {
      const res = await getCanvasProject(canvasProjectId)
      const nodes = res.data?.nodes || []
      setCanvasRefs(collectCanvasAgentRefs(nodes))
    } catch {
      setCanvasRefs([])
    } finally {
      setCanvasLoading(false)
    }
  }, [canvasProjectId])

  const loadList = async () => {
    setLoading(true)
    try {
      const res = await listAssets({ page, page_size: pageSize, category })
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
    if (open) {
      loadList()
      if (canvasProjectId) loadCanvasRefs()
    } else {
      setSelectedIds([])
      setSelectedCanvasKeys([])
    }
  }, [open, page, pageSize, category, canvasProjectId, loadCanvasRefs])

  useEffect(() => {
    if (open && activeTab === 'library') {
      loadList()
    }
    if (open && activeTab === 'canvas' && canvasProjectId) {
      loadCanvasRefs()
    }
  }, [activeTab])

  const toggleSelect = (item: AssetItem) => {
    if (category === 'image' && !isAssetCdnReady(item)) {
      message.warning('该图片无法用于生图（非 CDN 地址）')
      return
    }
    if (selectedIds.includes(item.id)) {
      setSelectedIds(selectedIds.filter(id => id !== item.id))
    } else {
      if (!multiple) {
        setSelectedIds([item.id])
      } else if (selectedIds.length < maxCount) {
        setSelectedIds([...selectedIds, item.id])
      } else {
        message.warning(`最多选择 ${maxCount} 张`)
      }
    }
  }

  const toggleSelectCanvas = (ref: DramaAgentRef) => {
    const key = ref.id || ref.url || ''
    if (!key || !ref.url || !isCdnUrl(ref.url)) {
      message.warning('该图片无法引用（非 CDN 地址）')
      return
    }
    if (selectedCanvasKeys.includes(key)) {
      setSelectedCanvasKeys(selectedCanvasKeys.filter((k) => k !== key))
    } else if (!multiple) {
      setSelectedCanvasKeys([key])
      setSelectedIds([])
    } else if (selectedCanvasKeys.length + selectedIds.length < maxCount) {
      setSelectedCanvasKeys([...selectedCanvasKeys, key])
    } else {
      message.warning(`最多选择 ${maxCount} 张`)
    }
  }

  const handleConfirm = () => {
    if (useRefMode) {
      const fromLibrary = items
        .filter((it) => selectedIds.includes(it.id))
        .map((a) => assetToAgentRef(a))
        .filter((r): r is DramaAgentRef => r !== null)
      const fromCanvas = canvasRefs.filter((r) => selectedCanvasKeys.includes(r.id || r.url || ''))
      const merged = [...fromLibrary, ...fromCanvas]
      if (merged.length === 0) {
        message.warning('请先选择资源')
        return
      }
      onSelectRefs?.(merged)
      setSelectedIds([])
      setSelectedCanvasKeys([])
      onClose()
      return
    }

    if (selectedIds.length === 0) {
      message.warning('请先选择资源')
      return
    }
    const selected = items.filter(it => selectedIds.includes(it.id))
    const valid = selected.filter((a) => category !== 'image' || isAssetCdnReady(a))
    if (valid.length === 0) {
      message.error('所选图片均无法用于生图，请选择已上传至 CDN 的图片')
      return
    }
    if (valid.length < selected.length) {
      message.warning(`已忽略 ${selected.length - valid.length} 张不可用图片`)
    }
    onSelect?.(valid)
    setSelectedIds([])
    onClose()
  }

  const handleUploadChange: any = {
    beforeUpload: async (file: File) => {
      try {
        const res = await uploadAsset(file, { category, source_type: 'upload' })
        if (res.code === 'success' && res.data) {
          try {
            pickCdnUrl(res.data)
            const asset = res.data as AssetItem
            message.success(`上传成功: ${file.name}`)
            setItems((prev) => [asset, ...prev])
            setTotal((prev) => prev + 1)
            if (autoApplyOnUpload && !multiple) {
              const agentRef = assetToAgentRef(asset)
              onSelect?.([asset])
              if (agentRef) onSelectRefs?.([agentRef])
              setSelectedIds([])
              onClose()
            } else {
              setActiveTab('library')
              setSelectedIds([asset.id])
            }
          } catch {
            message.error('上传成功但未获得有效 CDN 地址，请检查存储配置')
          }
        }
      } catch (e) {
        message.error(`上传失败: ${file.name}`)
      }
      return false
    },
    multiple: true,
    showUploadList: false,
    accept: category === 'image' ? 'image/*' : category === 'video' ? 'video/*' : '*/*',
  }

  const selectedCount = selectedIds.length + selectedCanvasKeys.length

  const tabItems = [
    { key: 'library', label: <Space><PictureOutlined />资源库</Space> },
    ...(canvasProjectId
      ? [{ key: 'canvas', label: <Space><AppstoreOutlined />当前画布</Space> }]
      : []),
    { key: 'upload', label: <Space><UploadOutlined />本地上传</Space> },
  ]

  return (
    <Modal
      open={open}
      onCancel={() => {
        setSelectedIds([])
        setSelectedCanvasKeys([])
        onClose()
      }}
      zIndex={zIndex}
      rootClassName="asset-picker-modal"
      title={
        <Space>
          <PictureOutlined />
          <span>选择引用资源</span>
          {selectedCount > 0 && <Tag color="blue">已选 {selectedCount} 项</Tag>}
        </Space>
      }
      width={900}
      footer={
        <Space>
          <Button onClick={() => { setSelectedIds([]); setSelectedCanvasKeys([]); onClose() }}>取消</Button>
          <Button type="primary" onClick={handleConfirm} disabled={selectedCount === 0}>
            确认选择 ({selectedCount})
          </Button>
        </Space>
      }
      styles={{ body: { padding: 0 } }}
    >
      <Tabs
        activeKey={activeTab}
        onChange={(k) => setActiveTab(k as 'library' | 'upload' | 'canvas')}
        style={{ padding: '0 24px' }}
        items={tabItems}
      />

      {activeTab === 'canvas' && canvasProjectId && (
        <div style={{ padding: '0 24px 24px', minHeight: 420 }}>
          {canvasLoading ? (
            <div style={{ textAlign: 'center', padding: 48 }}><Spin /></div>
          ) : canvasRefs.length === 0 ? (
            <Empty description="当前画布暂无可引用的图片（资源节点 / 已出图的图片节点）" />
          ) : (
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))',
                gap: 12,
                maxHeight: 420,
                overflowY: 'auto',
              }}
            >
              {canvasRefs.map((ref) => {
                const key = ref.id || ref.url || ''
                const isSelected = selectedCanvasKeys.includes(key)
                return (
                  <div
                    key={key}
                    onClick={() => toggleSelectCanvas(ref)}
                    style={{
                      position: 'relative',
                      border: isSelected ? '2px solid #1677ff' : '1px solid #f0f0f0',
                      borderRadius: 6,
                      overflow: 'hidden',
                      cursor: 'pointer',
                      background: '#fff',
                    }}
                  >
                    <div style={{ height: 120, background: '#fafafa' }}>
                      <img
                        src={ref.url}
                        alt=""
                        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      />
                    </div>
                    {isSelected && (
                      <div
                        style={{
                          position: 'absolute',
                          top: 4,
                          right: 4,
                          width: 22,
                          height: 22,
                          borderRadius: '50%',
                          background: '#1677ff',
                          color: '#fff',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                        }}
                      >
                        <CheckOutlined />
                      </div>
                    )}
                    <div style={{ padding: '6px 8px', fontSize: 11, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {ref.name || '画布图片'}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}

      {activeTab === 'library' && (
        <div style={{ padding: '0 24px 24px', minHeight: 420 }}>
          <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Input
              placeholder="搜索文件名"
              prefix={<SearchOutlined />}
              allowClear
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              onPressEnter={() => { setPage(1); loadList() }}
              style={{ width: 240 }}
            />
            <span style={{ fontSize: 12, color: '#999' }}>共 {total} 项资源</span>
          </div>

          {items.length === 0 && !loading ? (
            <Empty description={'暂无资源，可切换到"本地上传"标签上传'}>
              <Button type="primary" icon={<UploadOutlined />} onClick={() => setActiveTab('upload')}>
                去上传
              </Button>
            </Empty>
          ) : (
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))',
                gap: 12,
                maxHeight: 420,
                overflowY: 'auto',
              }}
            >
              {items.map((item) => {
                const isSelected = selectedIds.includes(item.id)
                const cdnReady = category !== 'image' || isAssetCdnReady(item)
                return (
                  <div
                    key={item.id}
                    onClick={() => toggleSelect(item)}
                    style={{
                      position: 'relative',
                      border: isSelected ? '2px solid #1677ff' : '1px solid #f0f0f0',
                      borderRadius: 6,
                      overflow: 'hidden',
                      cursor: cdnReady ? 'pointer' : 'not-allowed',
                      background: '#fff',
                      transition: 'all 0.2s',
                      opacity: cdnReady ? 1 : 0.45,
                    }}
                  >
                    <div
                      style={{
                        height: 120,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        background: '#fafafa',
                      }}
                    >
                      {category === 'image' && (
                        <Image
                          src={assetDisplayUrl(item)}
                          preview={false}
                          alt={item.file_name}
                          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                        />
                      )}
                      {category === 'video' && (
                        <video src={item.url} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                      )}
                      {category === 'file' && (
                        <span style={{ fontSize: 32, color: '#999' }}>
                          <PictureOutlined />
                        </span>
                      )}
                    </div>
                    {isSelected && (
                      <div
                        style={{
                          position: 'absolute',
                          top: 4,
                          right: 4,
                          width: 22,
                          height: 22,
                          borderRadius: '50%',
                          background: '#1677ff',
                          color: '#fff',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontSize: 14,
                        }}
                      >
                        <CheckOutlined />
                      </div>
                    )}
                    <div style={{ padding: '6px 8px', fontSize: 11, overflow: 'hidden', whiteSpace: 'nowrap', textOverflow: 'ellipsis' }}>
                      {item.file_name}
                    </div>
                  </div>
                )
              })}
            </div>
          )}

          {total > pageSize && (
            <div style={{ marginTop: 16, textAlign: 'center' }}>
              <Pagination
                current={page}
                pageSize={pageSize}
                total={total}
                onChange={(p, ps) => { setPage(p); setPageSize(ps) }}
                showSizeChanger
              />
            </div>
          )}
        </div>
      )}

      {activeTab === 'upload' && (
        <div style={{ padding: 24, minHeight: 420 }}>
          <Upload.Dragger
            {...handleUploadChange}
            style={{ padding: '48px 0' }}
          >
            <p style={{ fontSize: 48, color: '#1677ff' }}><UploadOutlined /></p>
            <p style={{ fontSize: 16, marginBottom: 8 }}>点击或拖拽文件到此处上传</p>
            <p style={{ fontSize: 12, color: '#999' }}>
              支持{category === 'image' ? '图片' : category === 'video' ? '视频' : '文件'}，单次支持多文件上传
            </p>
          </Upload.Dragger>

          <div style={{ marginTop: 24, fontSize: 12, color: '#666', textAlign: 'center' }}>
            上传完成后，自动加入资源库，可在"从资源库选择"标签页中找到
          </div>
        </div>
      )}
    </Modal>
  )
}
