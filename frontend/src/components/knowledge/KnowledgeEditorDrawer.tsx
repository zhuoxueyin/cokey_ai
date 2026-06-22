import { useEffect, useRef, useState } from 'react'
import {
  Alert,
  Button,
  Drawer,
  Form,
  Input,
  Select,
  Space,
  Tabs,
  Tag,
  Upload,
  message,
} from 'antd'
import {
  CloudUploadOutlined,
  EditOutlined,
  FileMarkdownOutlined,
  LinkOutlined,
  SaveOutlined,
  SendOutlined,
} from '@ant-design/icons'
import type { UploadProps } from 'antd'
import MarkdownEditor from '@/components/knowledge/MarkdownEditor'
import {
  createKnowledgeAdmin,
  getKnowledgeAdmin,
  importKnowledgeAdmin,
  listKnowledgeTags,
  previewFeishuKnowledge,
  publishKnowledgeAdmin,
  updateKnowledgeAdmin,
  type KnowledgeCategory,
  type KnowledgeEntry,
} from '@/api/dramaKnowledge'

const { TextArea } = Input

export type KnowledgeEditorMode = 'create' | 'edit'

interface KnowledgeEditorDrawerProps {
  open: boolean
  mode: KnowledgeEditorMode
  entryId?: string
  defaultCategory?: string
  categories: KnowledgeCategory[]
  onClose: () => void
  onSaved: () => void
}

type ImportTab = 'write' | 'file' | 'feishu'

function parseTags(raw: unknown): string[] {
  const items = Array.isArray(raw)
    ? raw
    : typeof raw === 'string'
      ? raw.split(/[,，]/)
      : []
  const seen = new Set<string>()
  const out: string[] = []
  for (const item of items) {
    const tag = String(item || '').trim()
    if (!tag || seen.has(tag)) continue
    seen.add(tag)
    out.push(tag)
  }
  return out
}

export default function KnowledgeEditorDrawer({
  open,
  mode,
  entryId,
  defaultCategory,
  categories,
  onClose,
  onSaved,
}: KnowledgeEditorDrawerProps) {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [importTab, setImportTab] = useState<ImportTab>('write')
  const [content, setContent] = useState('')
  const [feishuUrl, setFeishuUrl] = useState('')
  const [importHint, setImportHint] = useState<string>()
  const [uploadName, setUploadName] = useState<string>()
  const [tagOptions, setTagOptions] = useState<string[]>([])
  const loadedRef = useRef<string>()

  useEffect(() => {
    if (!open) return
    listKnowledgeTags().then((res) => {
      setTagOptions((res.data as string[]) || [])
    })
  }, [open])

  useEffect(() => {
    if (!open) return
    setImportHint(undefined)
    setFeishuUrl('')
    setUploadName(undefined)
    setImportTab('write')

    if (mode === 'edit' && entryId) {
      if (loadedRef.current === entryId) return
      setLoading(true)
      getKnowledgeAdmin(entryId)
        .then((res) => {
          const entry = res.data as KnowledgeEntry
          form.setFieldsValue({
            category: entry.category,
            title: entry.title,
            summary: entry.summary,
            tags: entry.tags || [],
          })
          setContent(entry.content_markdown || '')
          if (entry.source?.type === 'feishu' && entry.source.url) {
            setFeishuUrl(entry.source.url)
          }
          loadedRef.current = entryId
        })
        .finally(() => setLoading(false))
    } else {
      loadedRef.current = undefined
      form.resetFields()
      form.setFieldsValue({ category: defaultCategory || categories[0]?.code })
      setContent('')
    }
  }, [open, mode, entryId, defaultCategory, categories, form])

  const categoryOptions = categories.map((c) => ({
    value: c.code,
    label: `${c.name} (${c.code})`,
  }))

  const handleFileUpload: UploadProps['beforeUpload'] = (file) => {
    const reader = new FileReader()
    reader.onload = () => {
      const text = String(reader.result || '')
      setContent(text)
      setUploadName(file.name)
      if (!form.getFieldValue('title')) {
        form.setFieldValue('title', file.name.replace(/\.(md|markdown|txt)$/i, ''))
      }
      message.success(`已载入 ${file.name}`)
    }
    reader.readAsText(file)
    return false
  }

  const handleFetchFeishu = async () => {
    const category = form.getFieldValue('category')
    if (!category) {
      message.warning('请先选择分类')
      return
    }
    if (!feishuUrl.trim()) {
      message.warning('请填写飞书文档链接')
      return
    }
    setLoading(true)
    try {
      const res = await previewFeishuKnowledge(feishuUrl.trim())
      const fetched = res.data
      if (fetched?.title && !form.getFieldValue('title')) {
        form.setFieldValue('title', fetched.title)
      }
      if (fetched?.content_markdown) setContent(fetched.content_markdown)
      const hint = fetched?.message
      setImportHint(hint)
      if (fetched?.status === 'ok') message.success('飞书内容已拉取到编辑器')
      else if (hint) message.info(hint)
      else message.info('请手动粘贴正文到编辑器')
    } catch (e: unknown) {
      message.error((e as { message?: string })?.message || '拉取失败')
    } finally {
      setLoading(false)
    }
  }

  const saveEntry = async (publish = false) => {
    const values = await form.validateFields()
    const payload = {
      category: values.category as string,
      title: values.title as string,
      summary: (values.summary as string) || '',
      content_markdown: content,
      tags: parseTags(values.tags),
    }

    setLoading(true)
    try {
      if (mode === 'edit' && entryId) {
        await updateKnowledgeAdmin(entryId, payload)
        if (publish) await publishKnowledgeAdmin(entryId)
        message.success(publish ? '已保存并发布' : '已保存')
      } else if (importTab === 'file' && uploadName) {
        await importKnowledgeAdmin({
          source_type: 'file',
          filename: uploadName,
          publish,
          ...payload,
        })
        message.success(publish ? '文件导入并发布成功' : '文件导入成功')
      } else if (importTab === 'feishu' && feishuUrl.trim()) {
        await importKnowledgeAdmin({
          source_type: 'feishu',
          feishu_url: feishuUrl.trim(),
          publish,
          ...payload,
        })
        message.success(publish ? '飞书导入并发布成功' : '飞书导入成功')
      } else {
        const res = await createKnowledgeAdmin(payload)
        if (publish && res.data?.entry_id) {
          await publishKnowledgeAdmin(res.data.entry_id)
        }
        message.success(publish ? '已创建并发布' : '已创建草稿')
      }
      onSaved()
      onClose()
    } catch (e: unknown) {
      message.error((e as { message?: string })?.message || '保存失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Drawer
      title={
        <Space>
          <FileMarkdownOutlined />
          {mode === 'edit' ? '编辑知识条目' : '新建知识条目'}
        </Space>
      }
      width={920}
      open={open}
      onClose={onClose}
      destroyOnClose
      className="knowledge-editor-drawer"
      extra={
        <Space>
          <Button onClick={onClose}>取消</Button>
          <Button icon={<SaveOutlined />} loading={loading} onClick={() => saveEntry(false)}>
            保存草稿
          </Button>
          <Button
            type="primary"
            icon={<SendOutlined />}
            loading={loading}
            onClick={() => saveEntry(true)}
          >
            保存并发布
          </Button>
        </Space>
      }
    >
      <Form form={form} layout="vertical" className="knowledge-editor-form">
        <div className="knowledge-editor-form__meta">
          <Form.Item name="category" label="知识分类" rules={[{ required: true }]}>
            <Select options={categoryOptions} placeholder="选择专业分类" />
          </Form.Item>
          <Form.Item name="title" label="标题" rules={[{ required: true, message: '请输入标题' }]}>
            <Input placeholder="如：竖屏短剧前三秒钩子写法" />
          </Form.Item>
          <Form.Item name="summary" label="摘要">
            <TextArea rows={2} placeholder="一句话说明该知识适用场景与价值" />
          </Form.Item>
          <Form.Item name="tags" label="标签">
            <Select
              mode="tags"
              placeholder="选择已有标签，或直接输入新标签后回车"
              tokenSeparators={[',', '，']}
              options={tagOptions.map((tag) => ({ value: tag, label: tag }))}
              maxTagCount="responsive"
            />
          </Form.Item>
        </div>

        {mode === 'create' && (
          <Tabs
            activeKey={importTab}
            onChange={(k) => setImportTab(k as ImportTab)}
            className="knowledge-editor-tabs"
            items={[
              {
                key: 'write',
                label: (
                  <span>
                    <EditOutlined /> 在线编写
                  </span>
                ),
                children: (
                  <Alert
                    type="info"
                    showIcon
                    message="支持 Markdown 语法：标题、列表、表格、代码块等，右侧实时预览"
                    style={{ marginBottom: 12 }}
                  />
                ),
              },
              {
                key: 'file',
                label: (
                  <span>
                    <CloudUploadOutlined /> 本地文件
                  </span>
                ),
                children: (
                  <div className="knowledge-import-panel">
                    <Upload.Dragger
                      accept=".md,.markdown,.txt"
                      maxCount={1}
                      beforeUpload={handleFileUpload}
                      showUploadList={false}
                    >
                      <p className="ant-upload-drag-icon">
                        <CloudUploadOutlined />
                      </p>
                      <p className="ant-upload-text">拖拽或点击上传 .md / .txt 文件</p>
                      <p className="ant-upload-hint">上传后自动填入下方编辑器，可继续修改</p>
                    </Upload.Dragger>
                    {uploadName && (
                      <Tag color="blue" style={{ marginTop: 12 }}>
                        已载入：{uploadName}
                      </Tag>
                    )}
                  </div>
                ),
              },
              {
                key: 'feishu',
                label: (
                  <span>
                    <LinkOutlined /> 飞书链接
                  </span>
                ),
                children: (
                  <div className="knowledge-import-panel">
                    <Input
                      prefix={<LinkOutlined />}
                      placeholder="https://xxx.feishu.cn/docx/..."
                      value={feishuUrl}
                      onChange={(e) => setFeishuUrl(e.target.value)}
                    />
                    <Space style={{ marginTop: 12 }}>
                      <Button loading={loading} onClick={handleFetchFeishu}>
                        解析链接
                      </Button>
                      <span className="knowledge-import-hint">
                        公开文档可自动拉取；私有文档请解析后粘贴到编辑器
                      </span>
                    </Space>
                    {importHint && (
                      <Alert type="warning" showIcon message={importHint} style={{ marginTop: 12 }} />
                    )}
                  </div>
                ),
              },
            ]}
          />
        )}

        <div className="knowledge-editor-form__body">
          <div className="knowledge-editor-form__body-label">正文（Markdown）</div>
          <MarkdownEditor value={content} onChange={setContent} height={460} />
        </div>
      </Form>
    </Drawer>
  )
}
