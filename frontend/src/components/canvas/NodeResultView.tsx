import { Button, message, Spin, Tooltip } from 'antd'
import { CopyOutlined, DownloadOutlined, EyeOutlined } from '@ant-design/icons'
import type { TaskResult } from '@/types'
import { downloadRemoteFile } from '@/utils/download'
import { clampPrimaryImageIndex } from '@/utils/canvasPrimaryImage'

interface NodeResultViewProps {
  result?: TaskResult
  status?: string
  errorMessage?: string
  compact?: boolean
  /** 图片完整显示在节点内（object-fit: contain） */
  fitContain?: boolean
  /** 主图索引：大图预览 + 下游唯一引用 */
  primaryImageIndex?: number
  onSelectPrimaryImage?: (index: number) => void
}

function imageUrlAt(images: NonNullable<TaskResult['images']>, index: number): string {
  const img = images[index]
  return typeof img === 'string' ? img : img.url
}

function MultiImageMainView({
  images,
  primaryIndex,
  fitContain,
  onSelectPrimaryImage,
}: {
  images: NonNullable<TaskResult['images']>
  primaryIndex: number
  fitContain?: boolean
  onSelectPrimaryImage?: (index: number) => void
}) {
  const mainIdx = clampPrimaryImageIndex(primaryIndex, images.length)
  const mainUrl = imageUrlAt(images, mainIdx)
  const multi = images.length > 1

  return (
    <div className={`canvas-result canvas-result--images${fitContain ? ' canvas-result--fit-contain' : ''}${multi ? ' canvas-result--with-picker' : ''}`}>
      <div className="canvas-result__media-wrap canvas-result__media-wrap--main">
        {fitContain ? (
          <img src={mainUrl} alt="" className="canvas-result__image canvas-result__image--contain" />
        ) : (
          <img src={mainUrl} alt="" className="canvas-result__image" />
        )}
        {multi && <span className="canvas-result__main-badge">主图</span>}
        <div className="canvas-result__actions">
          <Tooltip title="预览">
            <Button
              size="small"
              type="text"
              icon={<EyeOutlined />}
              className="canvas-result__action-btn"
              onClick={(e) => {
                e.stopPropagation()
                window.open(mainUrl, '_blank')
              }}
            />
          </Tooltip>
          <Tooltip title="下载">
            <Button
              size="small"
              type="text"
              icon={<DownloadOutlined />}
              className="canvas-result__action-btn"
                onClick={(e) => {
                  e.stopPropagation()
                  downloadRemoteFile(mainUrl).catch((err: unknown) => {
                    const msg = err instanceof Error ? err.message : '下载失败'
                    if (msg.includes('新标签页')) message.warning(msg)
                    else message.error(msg || '下载失败')
                  })
                }}
            />
          </Tooltip>
        </div>
      </div>

      {multi && onSelectPrimaryImage && (
        <div className="canvas-output-picker nodrag nopan">
          <span className="canvas-output-picker__label">设为主图</span>
          <div className="canvas-output-picker__list">
            {images.map((item, i) => {
              const thumbUrl = typeof item === 'string' ? item : item.url
              return (
                <button
                  key={`${thumbUrl}-${i}`}
                  type="button"
                  className={`canvas-output-picker__item${i === mainIdx ? ' canvas-output-picker__item--active' : ''}`}
                  title={i === mainIdx ? `第 ${i + 1} 张（当前主图，下游引用此图）` : `将第 ${i + 1} 张设为主图`}
                  onClick={(e) => {
                    e.stopPropagation()
                    if (i !== mainIdx) onSelectPrimaryImage(i)
                  }}
                >
                  <img src={thumbUrl} alt="" />
                  {i === mainIdx && <span className="canvas-output-picker__item-tag">主</span>}
                </button>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

export default function NodeResultView({
  result,
  status,
  errorMessage,
  compact,
  fitContain,
  primaryImageIndex = 0,
  onSelectPrimaryImage,
}: NodeResultViewProps) {
  if (status === 'running') {
    return (
      <div className="canvas-result canvas-result--loading">
        <Spin size="small" />
        <span>生成中…</span>
      </div>
    )
  }
  if (status === 'failed') {
    return <div className="canvas-result canvas-result--error">{errorMessage || '生成失败'}</div>
  }
  if (!result) {
    return <div className="canvas-result canvas-result--empty">{compact ? '暂无结果' : '运行后将在此展示结果'}</div>
  }

  const copyText = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      message.success('已复制')
    } catch {
      message.error('复制失败')
    }
  }

  if (result.type === 'text' || result.text) {
    const text = result.text || ''
    return (
      <div className="canvas-result canvas-result--text">
        <div className="canvas-result__text canvas-run-selectable">{text || '（空文本）'}</div>
        {text && (
          <div className="canvas-result__actions">
            <Tooltip title="复制">
              <Button
                size="small"
                type="text"
                icon={<CopyOutlined />}
                className="canvas-result__action-btn"
                onClick={() => copyText(text)}
              />
            </Tooltip>
          </div>
        )}
      </div>
    )
  }

  if (result.images?.length) {
    return (
      <MultiImageMainView
        images={result.images}
        primaryIndex={primaryImageIndex}
        fitContain={fitContain}
        onSelectPrimaryImage={result.images.length > 1 ? onSelectPrimaryImage : undefined}
      />
    )
  }

  if (result.videos?.length) {
    return (
      <div className={`canvas-result canvas-result--videos${fitContain ? ' canvas-result--fit-contain' : ''}`}>
        {result.videos.map((vid, i) => {
          const url = typeof vid === 'string' ? vid : vid.url
          return (
            <div key={i} className="canvas-result__media-wrap">
              <video
                src={url}
                controls
                playsInline
                preload="metadata"
                className="canvas-result__video"
                onEnded={(e) => {
                  const el = e.currentTarget
                  if (Number.isFinite(el.duration) && el.duration > 0) {
                    el.currentTime = Math.max(0, el.duration - 0.05)
                  }
                  el.pause()
                }}
              />
              <div className="canvas-result__actions">
                <Tooltip title="新窗口预览">
                  <Button
                    size="small"
                    type="text"
                    icon={<EyeOutlined />}
                    className="canvas-result__action-btn"
                    onClick={() => window.open(url, '_blank')}
                  />
                </Tooltip>
                <Tooltip title="下载">
                  <Button
                    size="small"
                    type="text"
                    icon={<DownloadOutlined />}
                    className="canvas-result__action-btn"
                    onClick={() =>
                      downloadRemoteFile(url, `video_${i + 1}.mp4`).catch((err: unknown) => {
                        const msg = err instanceof Error ? err.message : '下载失败'
                        if (msg.includes('新标签页')) message.warning(msg)
                        else message.error(msg || '下载失败')
                      })
                    }
                  />
                </Tooltip>
              </div>
            </div>
          )
        })}
      </div>
    )
  }

  return <div className="canvas-result canvas-result--empty">暂无结果</div>
}
