import { useState } from 'react'
import { Modal, Upload } from 'antd'
import {
  FileTextOutlined,
  PictureOutlined,
  VideoCameraOutlined,
  UploadOutlined,
  AppstoreOutlined,
  EditOutlined,
  RobotOutlined,
  ArrowLeftOutlined,
  FontSizeOutlined,
} from '@ant-design/icons'
import type { CanvasNodeType } from '@/types/canvas'

export interface AddNodePickerModalProps {
  open: boolean
  onClose: () => void
  onAddNode: (type: CanvasNodeType, options?: { text_mode?: 'manual' | 'generate' }) => void
  onUpload: (file: File) => void
  onPickLibrary: () => void
}

export default function AddNodePickerModal({
  open,
  onClose,
  onAddNode,
  onUpload,
  onPickLibrary,
}: AddNodePickerModalProps) {
  const [textPickerOpen, setTextPickerOpen] = useState(false)

  const pickNode = (type: CanvasNodeType, options?: { text_mode?: 'manual' | 'generate' }) => {
    onAddNode(type, options)
    setTextPickerOpen(false)
    onClose()
  }

  const handleClose = () => {
    setTextPickerOpen(false)
    onClose()
  }

  if (textPickerOpen) {
    return (
      <Modal
        open={open}
        onCancel={handleClose}
        footer={null}
        width={320}
        centered
        className="canvas-add-modal"
        title={null}
        closable
      >
        <button type="button" className="canvas-add-modal__back" onClick={() => setTextPickerOpen(false)}>
          <ArrowLeftOutlined />
          <span>文本</span>
        </button>
        <div className="canvas-add-modal__hint">可以尝试以下操作：</div>
        <button type="button" className="canvas-add-modal__item" onClick={() => pickNode('text', { text_mode: 'manual' })}>
          <EditOutlined />
          <span>直接输入你的文本</span>
        </button>
        <button type="button" className="canvas-add-modal__item" onClick={() => pickNode('text', { text_mode: 'generate' })}>
          <RobotOutlined />
          <span>生成文本</span>
        </button>
      </Modal>
    )
  }

  return (
    <Modal
      open={open}
      onCancel={handleClose}
      footer={null}
      width={320}
      centered
      className="canvas-add-modal"
      title={null}
      closable
    >
      <div className="canvas-add-modal__section">
        <div className="canvas-add-modal__label">添加节点</div>
        <button type="button" className="canvas-add-modal__item" onClick={() => setTextPickerOpen(true)}>
          <FileTextOutlined />
          <span>文本</span>
        </button>
        <button type="button" className="canvas-add-modal__item" onClick={() => pickNode('title')}>
          <FontSizeOutlined />
          <span>标题</span>
        </button>
        <button type="button" className="canvas-add-modal__item" onClick={() => pickNode('image')}>
          <PictureOutlined />
          <span>图片</span>
        </button>
        <button type="button" className="canvas-add-modal__item" onClick={() => pickNode('video')}>
          <VideoCameraOutlined />
          <span>视频</span>
        </button>
      </div>
      <div className="canvas-add-modal__divider" />
      <div className="canvas-add-modal__section">
        <div className="canvas-add-modal__label">添加资源</div>
        <Upload
          accept="image/*,video/*"
          showUploadList={false}
          beforeUpload={(file) => {
            onUpload(file)
            handleClose()
            return false
          }}
        >
          <button type="button" className="canvas-add-modal__item">
            <UploadOutlined />
            <span>上传</span>
          </button>
        </Upload>
        <button
          type="button"
          className="canvas-add-modal__item"
          onClick={() => {
            onPickLibrary()
            handleClose()
          }}
        >
          <AppstoreOutlined />
          <span>资源库</span>
        </button>
      </div>
    </Modal>
  )
}
