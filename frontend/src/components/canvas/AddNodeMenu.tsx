import { Dropdown, Upload, message } from 'antd'
import type { MenuProps } from 'antd'
import {
  PlusOutlined,
  FileTextOutlined,
  PictureOutlined,
  VideoCameraOutlined,
  UploadOutlined,
  CloudUploadOutlined,
} from '@ant-design/icons'
import type { CanvasNodeType } from '@/types/canvas'

interface AddNodeMenuProps {
  onAddNode: (type: CanvasNodeType, position?: { x: number; y: number }) => void
  onUploadResource: (file: File) => void
  loading?: boolean
}

export default function AddNodeMenu({ onAddNode, onUploadResource, loading }: AddNodeMenuProps) {
  const handleUpload = (file: File) => {
    onUploadResource(file)
    return false
  }

  const nodeItems: MenuProps['items'] = [
    {
      key: 'text',
      icon: <FileTextOutlined />,
      label: '文本',
      onClick: () => onAddNode('text'),
    },
    {
      key: 'image',
      icon: <PictureOutlined />,
      label: '图片',
      onClick: () => onAddNode('image'),
    },
    {
      key: 'video',
      icon: <VideoCameraOutlined />,
      label: '视频',
      onClick: () => onAddNode('video'),
    },
  ]

  const resourceItems: MenuProps['items'] = [
    {
      key: 'upload-image',
      icon: <UploadOutlined />,
      label: (
        <Upload accept="image/*" showUploadList={false} beforeUpload={handleUpload}>
          <span>上传图片</span>
        </Upload>
      ),
    },
    {
      key: 'upload-video',
      icon: <CloudUploadOutlined />,
      label: (
        <Upload accept="video/*" showUploadList={false} beforeUpload={handleUpload}>
          <span>上传视频</span>
        </Upload>
      ),
    },
  ]

  const menuItems: MenuProps['items'] = [
    { type: 'group', label: '添加节点', children: nodeItems },
    { type: 'divider' },
    { type: 'group', label: '添加资源', children: resourceItems },
  ]

  return (
    <Dropdown menu={{ items: menuItems }} trigger={['click']} placement="top">
      <button type="button" className="canvas-toolbar__add" disabled={loading}>
        <PlusOutlined />
      </button>
    </Dropdown>
  )
}
