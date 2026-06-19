import { Tooltip } from 'antd'
import { FileTextOutlined } from '@ant-design/icons'
import type { CanvasUpstreamPreview } from '@/utils/canvasUpstream'

interface NodeReferenceStripProps {
  upstream: CanvasUpstreamPreview
  /** node=节点顶栏小方块；panel=编辑面板顶栏 */
  variant?: 'node' | 'panel'
}

function previewText(text: string, max = 6) {
  const oneLine = text.replace(/\s+/g, ' ').trim()
  if (oneLine.length <= max) return oneLine
  return `${oneLine.slice(0, max)}…`
}

export default function NodeReferenceStrip({ upstream, variant = 'node' }: NodeReferenceStripProps) {
  if (upstream.texts.length === 0 && upstream.images.length === 0) return null

  const isNode = variant === 'node'

  return (
    <div className={`canvas-ref-strip${isNode ? ' canvas-ref-strip--node' : ' canvas-ref-strip--panel'}`}>
      {upstream.texts.map((text, i) => (
        <Tooltip
          key={`t-${i}`}
          title={isNode ? previewText(text, 6) : text}
          placement="top"
          overlayClassName="canvas-ref-tooltip"
        >
          <div className="canvas-ref-chip canvas-ref-chip--text">
            <FileTextOutlined />
          </div>
        </Tooltip>
      ))}
      {upstream.images.map((url, i) => (
        <Tooltip
          key={`i-${i}`}
          title={
            <img src={url} alt="" className="canvas-ref-tooltip__img" />
          }
          placement="top"
          overlayClassName="canvas-ref-tooltip"
        >
          <div className="canvas-ref-chip canvas-ref-chip--image">
            <img src={url} alt="" />
          </div>
        </Tooltip>
      ))}
    </div>
  )
}
