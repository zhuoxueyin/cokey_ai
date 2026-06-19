import { useEffect, useState } from 'react'
import { Popover, Tooltip, message } from 'antd'
import {
  HighlightOutlined,
  ClearOutlined,
  ScissorOutlined,
  InfoCircleOutlined,
  DownloadOutlined,
} from '@ant-design/icons'
import { downloadRemoteFile } from '@/utils/download'
import type { ImageMarkTool } from '@/types/imageMark'

interface ResourceImageToolboxProps {
  imageUrl: string
  imageName?: string
  onMark: (initialTool?: ImageMarkTool) => void
}

interface ToolDef {
  key: string
  label: string
  icon: React.ReactNode
  enabled: boolean
  comingSoon?: boolean
  onClick?: () => void
}

function ImageInfoPanel({
  imageUrl,
  imageName,
}: {
  imageUrl: string
  imageName?: string
}) {
  const [size, setSize] = useState<string>('加载中…')

  useEffect(() => {
    const img = new Image()
    img.onload = () => setSize(`${img.naturalWidth} × ${img.naturalHeight}`)
    img.onerror = () => setSize('—')
    img.src = imageUrl
  }, [imageUrl])

  return (
    <div className="canvas-resource-info">
      <div className="canvas-resource-info__row">
        <span className="canvas-resource-info__label">文件名</span>
        <span className="canvas-resource-info__value">{imageName || '未命名'}</span>
      </div>
      <div className="canvas-resource-info__row">
        <span className="canvas-resource-info__label">尺寸</span>
        <span className="canvas-resource-info__value">{size}</span>
      </div>
      <div className="canvas-resource-info__row canvas-resource-info__row--url">
        <span className="canvas-resource-info__label">地址</span>
        <span className="canvas-resource-info__value" title={imageUrl}>
          {imageUrl}
        </span>
      </div>
    </div>
  )
}

export default function ResourceImageToolbox({ imageUrl, imageName, onMark }: ResourceImageToolboxProps) {
  const [infoOpen, setInfoOpen] = useState(false)
  const [downloading, setDownloading] = useState(false)

  const handleDownload = async () => {
    if (downloading) return
    setDownloading(true)
    try {
      await downloadRemoteFile(imageUrl, imageName || undefined)
      message.success('下载成功')
    } catch {
      window.open(imageUrl, '_blank', 'noopener,noreferrer')
      message.warning('无法直接保存，已在新标签页打开')
    } finally {
      setDownloading(false)
    }
  }

  const tools: ToolDef[] = [
    {
      key: 'mark',
      label: '标记',
      icon: <HighlightOutlined />,
      enabled: true,
      onClick: () => onMark('brush'),
    },
    {
      key: 'erase',
      label: '擦除',
      icon: <ClearOutlined />,
      enabled: true,
      onClick: () => onMark('eraser'),
    },
    {
      key: 'crop',
      label: '裁剪',
      icon: <ScissorOutlined />,
      enabled: false,
      comingSoon: true,
    },
    {
      key: 'info',
      label: '信息',
      icon: <InfoCircleOutlined />,
      enabled: true,
    },
    {
      key: 'download',
      label: '下载',
      icon: <DownloadOutlined />,
      enabled: true,
      onClick: () => void handleDownload(),
    },
  ]

  return (
    <div className="canvas-resource-toolbox nodrag nopan" onMouseDown={(e) => e.stopPropagation()}>
      {tools.map((tool) => {
        const btn = (
          <button
            type="button"
            className={`canvas-resource-toolbox__item${!tool.enabled ? ' canvas-resource-toolbox__item--disabled' : ''}${downloading && tool.key === 'download' ? ' canvas-resource-toolbox__item--loading' : ''}`}
            disabled={!tool.enabled || (downloading && tool.key === 'download')}
            onClick={(e) => {
              e.stopPropagation()
              tool.onClick?.()
            }}
          >
            <span className="canvas-resource-toolbox__icon">{tool.icon}</span>
            <span className="canvas-resource-toolbox__label">{tool.label}</span>
          </button>
        )

        if (tool.key === 'info') {
          return (
            <Popover
              key={tool.key}
              open={infoOpen}
              onOpenChange={setInfoOpen}
              trigger="click"
              placement="bottom"
              overlayClassName="canvas-resource-info-popover"
              content={<ImageInfoPanel imageUrl={imageUrl} imageName={imageName} />}
            >
              {btn}
            </Popover>
          )
        }

        if (tool.comingSoon) {
          return (
            <Tooltip key={tool.key} title="即将上线">
              {btn}
            </Tooltip>
          )
        }

        return <span key={tool.key}>{btn}</span>
      })}
    </div>
  )
}
