import { useMemo } from 'react'
import { Button, Drawer, Popconfirm, Space, Tag } from 'antd'
import { DeleteOutlined, EditOutlined } from '@ant-design/icons'
import MarkdownPreview from '@uiw/react-markdown-preview'
import '@uiw/react-markdown-preview/markdown.css'
import type { DramaStylePreset } from '@/types/drama'
import { RENDER_CLASS_LABELS } from '@/types/drama'
import { useSiteTheme } from '@/hooks/useSiteTheme'
import { getStyleDisplayTags } from '@/utils/styleDisplay'
import { legacyStyleToDescriptionMd } from '@/utils/styleDescription'
import { resolveStylePreview } from '@/utils/stylePreview'

interface StylePlazaDetailDrawerProps {
  open: boolean
  style: DramaStylePreset | null
  loading?: boolean
  onClose: () => void
  onEdit?: (styleId: string) => void
  onDelete?: (styleId: string) => Promise<void>
}

export default function StylePlazaDetailDrawer({
  open,
  style,
  loading,
  onClose,
  onEdit,
  onDelete,
}: StylePlazaDetailDrawerProps) {
  const { effective } = useSiteTheme()
  const colorMode = effective === 'dark' ? 'dark' : 'light'

  const descriptionMd = useMemo(
    () => (style ? legacyStyleToDescriptionMd(style) : ''),
    [style],
  )

  if (!style) {
    return (
      <Drawer title="风格详情" open={open} onClose={onClose} width={640} loading={loading}>
        加载中…
      </Drawer>
    )
  }

  const preview = resolveStylePreview(style)
  const tags = getStyleDisplayTags(style)
  const isProtected = style.immutable === true

  return (
    <Drawer
      title={style.name}
      open={open}
      onClose={onClose}
      width={640}
      loading={loading}
      extra={
        onEdit ? (
          <Button type="primary" icon={<EditOutlined />} onClick={() => onEdit(style.style_id)}>
            编辑
          </Button>
        ) : null
      }
      footer={
        onDelete ? (
          <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
            <Popconfirm
              title="删除此风格？"
              description={
                isProtected
                  ? '该风格已锁定，不可删除。'
                  : '软删除后将从风格广场移除，不可恢复。'
              }
              okText="删除"
              cancelText="取消"
              okButtonProps={{ danger: true }}
              disabled={isProtected}
              onConfirm={async () => {
                await onDelete(style.style_id)
              }}
            >
              <Button danger icon={<DeleteOutlined />} disabled={isProtected}>
                删除风格
              </Button>
            </Popconfirm>
          </Space>
        ) : null
      }
    >
      <div className="style-plaza-detail">
        <div className="style-plaza-detail__cover">
          {preview.coverUrl ? (
            <img src={preview.coverUrl} alt="" className="style-cover-img" />
          ) : (
            <div
              className="style-plaza-detail__cover-fallback"
              style={{ background: preview.gradient }}
            />
          )}
        </div>

        <Space wrap size={[4, 8]} className="style-plaza-detail__tags">
          <Tag color="blue">{RENDER_CLASS_LABELS[style.render_class]}</Tag>
          {style.origin === 'seed' && <Tag color="gold">历史导入</Tag>}
          {tags.map((t) => (
            <Tag key={t}>{t}</Tag>
          ))}
        </Space>

        {descriptionMd.trim() && (
          <section className="style-plaza-detail__section">
            <div className="style-plaza-detail__markdown" data-color-mode={colorMode}>
              <MarkdownPreview source={descriptionMd} />
            </div>
          </section>
        )}
      </div>
    </Drawer>
  )
}
