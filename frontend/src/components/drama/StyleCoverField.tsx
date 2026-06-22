import { useEffect, useState } from 'react'
import { Button, Form, Image, Input, Space, Upload, message } from 'antd'
import type { FormInstance } from 'antd'
import { DeleteOutlined, PictureOutlined, UploadOutlined } from '@ant-design/icons'
import { uploadAsset } from '@/api'
import AssetPicker from '@/components/AssetPicker'
import type { AssetItem } from '@/types'
import { pickCdnUrl } from '@/utils/cdnUrl'

interface StyleCoverFieldProps {
  form: FormInstance
}

export default function StyleCoverField({ form }: StyleCoverFieldProps) {
  const [pickerOpen, setPickerOpen] = useState(false)
  const [uploading, setUploading] = useState(false)
  const watchedCover = Form.useWatch('cover_url', form)
  const [previewUrl, setPreviewUrl] = useState<string>(() => {
    const v = form.getFieldValue('cover_url')
    return typeof v === 'string' ? v : ''
  })

  useEffect(() => {
    const v = typeof watchedCover === 'string' ? watchedCover : ''
    setPreviewUrl(v)
  }, [watchedCover])

  const applyCoverUrl = (url: string) => {
    const next = url.trim() || undefined
    form.setFieldValue('cover_url', next)
    setPreviewUrl(next || '')
  }

  const applyFromAsset = (asset: AssetItem) => {
    try {
      const cdnUrl = pickCdnUrl(asset, '封面图')
      applyCoverUrl(cdnUrl)
      message.success('已设置封面')
    } catch (e) {
      message.error(e instanceof Error ? e.message : '该资源无法用作封面')
    }
  }

  const handleAssetSelect = (assets: AssetItem[]) => {
    if (assets[0]) applyFromAsset(assets[0])
  }

  const handleBeforeUpload = async (file: File) => {
    if (!file.type.startsWith('image/')) {
      message.warning('请选择图片文件')
      return Upload.LIST_IGNORE
    }
    setUploading(true)
    try {
      const res = await uploadAsset(file, { category: 'image', source_type: 'upload' })
      if (res.code === 'success' && res.data) {
        applyFromAsset(res.data as AssetItem)
      } else {
        message.error(res.message || '上传失败')
      }
    } catch {
      message.error('上传失败，请重试')
    } finally {
      setUploading(false)
    }
    return false
  }

  return (
    <div className="style-form-cover">
      <Form.Item
        name="cover_url"
        label="封面图"
        extra="支持本地上传、从资源库选择，或直接粘贴图片链接"
      >
        <Input placeholder="https:// 或点击下方上传 / 选择" allowClear />
      </Form.Item>

      <Space wrap className="style-form-cover__actions">
        <Upload
          accept="image/*"
          showUploadList={false}
          beforeUpload={handleBeforeUpload}
          disabled={uploading}
        >
          <Button icon={<UploadOutlined />} loading={uploading}>
            本地上传
          </Button>
        </Upload>
        <Button icon={<PictureOutlined />} onClick={() => setPickerOpen(true)}>
          从资源库选择
        </Button>
        {previewUrl ? (
          <Button type="text" danger icon={<DeleteOutlined />} onClick={() => applyCoverUrl('')}>
            清除封面
          </Button>
        ) : null}
      </Space>

      {previewUrl ? (
        <div className="style-form-cover-preview">
          <Image
            src={previewUrl}
            alt="封面预览"
            className="style-form-cover-preview__img"
            preview={{ src: previewUrl }}
            fallback="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'/%3E"
          />
        </div>
      ) : (
        <div className="style-form-cover-preview style-form-cover-preview--empty">
          <PictureOutlined />
          <span>封面预览</span>
        </div>
      )}

      <AssetPicker
        open={pickerOpen}
        onClose={() => setPickerOpen(false)}
        onSelect={handleAssetSelect}
        multiple={false}
        category="image"
        maxCount={1}
        autoApplyOnUpload
      />
    </div>
  )
}
