import { Button, Form, Input, Select, Space } from 'antd'
import type { FormInstance } from 'antd'
import type { DramaRenderClass } from '@/types/drama'
import { RENDER_CLASS_LABELS } from '@/types/drama'
import { buildStyleDescriptionTemplate, legacyStyleToDescriptionMd } from '@/utils/styleDescription'
import StyleCoverField from './StyleCoverField'

const { TextArea } = Input

/** 风格新建/编辑面板宽度（管理端 Drawer、风格广场 Modal 共用） */
export const STYLE_EDIT_PANEL_WIDTH = 840

interface StyleFormFieldsProps {
  form: FormInstance
}

function splitCsv(value: unknown): string[] {
  if (!value) return []
  return String(value)
    .split(/[,，、\n]/)
    .map((s) => s.trim())
    .filter(Boolean)
}

export default function StyleFormFields({ form }: StyleFormFieldsProps) {
  const name = Form.useWatch('name', form)

  const insertTemplate = () => {
    form.setFieldsValue({
      style_description_md: buildStyleDescriptionTemplate(name || '风格名称'),
    })
  }

  return (
    <>
      <Form.Item name="name" label="名称" rules={[{ required: true, message: '必填' }]}>
        <Input placeholder="如：3D 中国奇幻动画" />
      </Form.Item>
      <StyleCoverField form={form} />
      <Form.Item name="render_class" label="渲染类型" rules={[{ required: true, message: '必选' }]}>
        <Select
          options={(['live_action', 'illustration_2d', 'render_3d'] as DramaRenderClass[]).map(
            (v) => ({ value: v, label: RENDER_CLASS_LABELS[v] }),
          )}
        />
      </Form.Item>
      <Form.Item name="genre_tags" label="标签">
        <Input placeholder="科幻, 复古, 国风（逗号分隔）" />
      </Form.Item>

      <Form.Item
        name="style_description_md"
        label="风格描述"
        rules={[{ required: true, message: '请填写风格描述' }]}
        extra={
          <Space size="small" wrap>
            <span>
              Markdown 分段：风格摘要、风格特点、人物角色、场景描述、色彩倾向、代表作品、生图/生视频提示词参考
            </span>
            <Button type="link" size="small" onClick={insertTemplate} style={{ padding: 0 }}>
              插入模板
            </Button>
          </Space>
        }
      >
        <TextArea
          rows={18}
          className="style-form-description"
          placeholder="使用 ## 标题 分段，详见「插入模板」"
          showCount
        />
      </Form.Item>
    </>
  )
}

export function styleFormToPayload(values: Record<string, unknown>) {
  return {
    name: values.name as string,
    render_class: values.render_class as string,
    genre_tags: splitCsv(values.genre_tags),
    cover_url: values.cover_url ? String(values.cover_url) : undefined,
    style_description_md: values.style_description_md
      ? String(values.style_description_md).trim()
      : undefined,
  }
}

export function styleToFormValues(style: {
  name: string
  render_class: string
  genre_tags?: string[]
  style_description_md?: string
  model_prompts?: Record<string, string>
  model_protocol?: {
    preview?: { cover_url?: string }
    visual?: { color_palette?: string[] }
  }
  visual?: {
    reference_films?: string[]
    color_palette?: string[]
  }
  reference_images?: { url?: string }[]
}) {
  const cover =
    style.model_protocol?.preview?.cover_url ||
    style.reference_images?.[0]?.url ||
    ''

  return {
    name: style.name,
    render_class: style.render_class,
    genre_tags: (style.genre_tags || []).join(', '),
    cover_url: cover,
    style_description_md: legacyStyleToDescriptionMd(style),
  }
}

export { splitCsv }
