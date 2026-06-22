import { useMemo, useState } from 'react'
import { Empty, Input, Modal } from 'antd'
import { CheckOutlined, SearchOutlined } from '@ant-design/icons'
import type { DramaStylePreset } from '@/types/drama'
import { RENDER_CLASS_LABELS } from '@/types/drama'
import { getStyleDisplayTags } from '@/utils/styleDisplay'
import { getStyleDescriptionExcerpt } from '@/utils/styleDescription'
import { resolveStylePreview } from '@/utils/stylePreview'

interface StylePickerGridProps {
  open: boolean
  onClose: () => void
  styles: DramaStylePreset[]
  value?: string
  onChange: (styleId?: string) => void
  title?: string
  /** 须高于创作助手侧栏（1201）与模型下拉（1405） */
  zIndex?: number
}

function normalizeSearchText(text: string): string {
  return text.trim().toLowerCase()
}

function matchesStyleSearch(style: DramaStylePreset, query: string): boolean {
  if (!query) return true
  const q = normalizeSearchText(query)
  const fields = [
    style.name,
    style.style_id,
    style.description,
    style.style_description_md,
    getStyleDescriptionExcerpt(style),
    RENDER_CLASS_LABELS[style.render_class],
    ...(style.genre_tags || []),
    ...(style.visual?.reference_films || []),
    ...(style.model_protocol?.trait_tags || []),
  ]
  return fields.some((field) => field && normalizeSearchText(String(field)).includes(q))
}

export default function StylePickerGrid({
  open,
  onClose,
  styles,
  value,
  onChange,
  title = '选择视觉风格',
  zIndex = 3000,
}: StylePickerGridProps) {
  const [searchText, setSearchText] = useState('')

  const filteredStyles = useMemo(
    () => styles.filter((s) => matchesStyleSearch(s, searchText)),
    [styles, searchText],
  )

  return (
    <Modal
      title={title}
      open={open}
      onCancel={onClose}
      footer={null}
      width={720}
      zIndex={zIndex}
      className="style-picker-grid-modal"
      destroyOnClose
      afterOpenChange={(visible) => {
        if (!visible) setSearchText('')
      }}
    >
      {styles.length === 0 ? (
        <Empty description="暂无已发布风格，请前往风格广场创建" />
      ) : (
        <>
          <div className="style-picker-grid__search">
            <Input
              placeholder="搜索风格名称、标签、描述…"
              prefix={<SearchOutlined />}
              allowClear
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              autoFocus
            />
            <span className="style-picker-grid__search-meta">
              {searchText.trim()
                ? `匹配 ${filteredStyles.length} / ${styles.length}`
                : `共 ${styles.length} 项`}
            </span>
          </div>
          {filteredStyles.length === 0 ? (
            <Empty description="没有匹配的风格" style={{ margin: '24px 0' }} />
          ) : (
            <div className="style-picker-grid">
              {!searchText.trim() && (
                <button
                  type="button"
                  className={`style-picker-grid__item${!value ? ' style-picker-grid__item--active' : ''}`}
                  onClick={() => {
                    onChange(undefined)
                    onClose()
                  }}
                >
                  <div className="style-picker-grid__thumb style-picker-grid__thumb--none">无</div>
                  <div className="style-picker-grid__name">不选风格</div>
                </button>
              )}
              {filteredStyles.map((s) => {
                const preview = resolveStylePreview(s)
                const active = value === s.style_id
                return (
                  <button
                    key={s.style_id}
                    type="button"
                    className={`style-picker-grid__item${active ? ' style-picker-grid__item--active' : ''}`}
                    onClick={() => {
                      onChange(s.style_id)
                      onClose()
                    }}
                  >
                    <div className="style-picker-grid__thumb">
                      {preview.coverUrl ? (
                        <img src={preview.coverUrl} alt="" className="style-cover-img" />
                      ) : (
                        <div
                          className="style-picker-grid__thumb-fallback"
                          style={{ background: preview.gradient }}
                        />
                      )}
                      {active && (
                        <span className="style-picker-grid__check">
                          <CheckOutlined />
                        </span>
                      )}
                    </div>
                    <div className="style-picker-grid__name" title={s.name}>
                      {s.name}
                    </div>
                    <div className="style-picker-grid__tags">
                      <span className="style-picker-grid__chip">
                        {RENDER_CLASS_LABELS[s.render_class]}
                      </span>
                      {getStyleDisplayTags(s, 2).map((t) => (
                        <span key={t} className="style-picker-grid__chip">
                          {t}
                        </span>
                      ))}
                    </div>
                  </button>
                )
              })}
            </div>
          )}
        </>
      )}
    </Modal>
  )
}
