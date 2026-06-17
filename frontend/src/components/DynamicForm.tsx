import { useState } from 'react'
import {
  Form,
  Input,
  InputNumber,
  Slider,
  Select,
  Switch,
  Button,
  Upload,
  Space,
  Card,
  message,
  Tooltip,
  Alert,
} from 'antd'
import {
  ThunderboltOutlined,
  UploadOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import type { UploadProps } from 'antd'
import { useGenerationStore } from '@/store/generation'
import { generate, uploadImage } from '@/api'
import type { ParamField } from '@/types'
import { extractCdnUrls, isCdnUrl, pickCdnUrl } from '@/utils/cdnUrl'

const { TextArea } = Input

export default function DynamicForm() {
  const { currentModel, params, updateParam, setParams, setIsGenerating, addTask, activeCategory, setSessionId, sessionId } = useGenerationStore()
  const [form] = Form.useForm()
  const [submitting, setSubmitting] = useState(false)

  if (!currentModel || !currentModel.param_schema?.fields) {
    return <Alert message="该模型暂无参数配置" type="info" showIcon />
  }

  const fields = currentModel.param_schema.fields

  const isFieldVisible = (field: ParamField): boolean => {
    if (!field.show_when) return true
    for (const [key, value] of Object.entries(field.show_when)) {
      if (params[key] !== value) return false
    }
    return true
  }

  const renderField = (field: ParamField) => {
    const { name, label, field_type, required, placeholder, options, min, max, step, default: def } = field

    const commonProps = {
      placeholder: placeholder || `请输入${label}`,
    }

    const value = params[name] !== undefined ? params[name] : (def !== undefined ? def : undefined)

    switch (field_type) {
      case 'text':
        return (
          <Input
            {...commonProps}
            value={value}
            onChange={(e) => updateParam(name, e.target.value)}
          />
        )
      case 'textarea':
        return (
          <TextArea
            {...commonProps}
            rows={4}
            value={value}
            onChange={(e) => updateParam(name, e.target.value)}
          />
        )
      case 'number':
        return (
          <InputNumber
            style={{ width: '100%' }}
            min={min}
            max={max}
            step={step}
            placeholder={placeholder}
            value={value}
            onChange={(val) => updateParam(name, val)}
          />
        )
      case 'slider':
        return (
          <Space style={{ width: '100%' }}>
            <Slider
              style={{ flex: 1 }}
              min={min}
              max={max}
              step={step}
              value={typeof value === 'number' ? value : (def || 0)}
              onChange={(val) => updateParam(name, val)}
            />
            <InputNumber
              style={{ width: 80 }}
              min={min}
              max={max}
              step={step}
              value={value}
              onChange={(val) => updateParam(name, val)}
            />
          </Space>
        )
      case 'select':
        return (
          <Select
            style={{ width: '100%' }}
            placeholder={placeholder}
            value={value}
            onChange={(val) => updateParam(name, val)}
            options={options?.map((opt) => ({ label: opt.label, value: opt.value })) || []}
          />
        )
      case 'switch':
        return (
          <Switch
            checked={!!value}
            onChange={(val) => updateParam(name, val)}
          />
        )
      case 'image_upload':
        const uploadProps: UploadProps = {
          beforeUpload: async (file) => {
            try {
              const res = await uploadImage(file as File)
              if (res.code === 'success' && res.data) {
                try {
                  const cdnUrl = pickCdnUrl(res.data)
                  updateParam(name, cdnUrl)
                  message.success('上传成功')
                } catch {
                  message.error('上传成功但未获得有效 CDN 地址，请检查存储配置')
                }
              }
            } catch (e) {
              console.error(e)
            }
            return false
          },
          maxCount: 1,
          showUploadList: false,
        }
        return (
          <Space>
            <Upload {...uploadProps}>
              <Button icon={<UploadOutlined />}>上传图片</Button>
            </Upload>
            {value && isCdnUrl(String(value)) && (
              <span style={{ fontSize: 12, color: '#888' }}>
                已上传（CDN）
              </span>
            )}
            {value && !isCdnUrl(String(value)) && (
              <span style={{ fontSize: 12, color: '#ff4d4f' }}>
                地址无效，请重新上传
              </span>
            )}
          </Space>
        )
      default:
        return (
          <Input
            {...commonProps}
            value={value}
            onChange={(e) => updateParam(name, e.target.value)}
          />
        )
    }
  }

  const hasRequired = fields.some((f) => f.required)
  const requiredEmpty = fields.some((f) => f.required && (params[f.name] === undefined || params[f.name] === '' || params[f.name] === null))
  const promptEmptyForText = activeCategory === 'text' && !params.prompt
  const promptEmptyForImage = activeCategory === 'image' && !params.prompt && !params.positive_prompt
  const needPromptEmpty = (activeCategory === 'text' && promptEmptyForText) || (activeCategory === 'image' && promptEmptyForImage)

  const handleSubmit = async () => {
    if (needPromptEmpty) {
      message.warning('请先在"图像描述"或"输入内容"中填写描述')
      return
    }
    if (requiredEmpty) {
      const requiredFields = fields.filter((f) => f.required).map((f) => f.label).join('、')
      message.warning(`请先填写必填项: ${requiredFields}`)
      return
    }

    let submitParams: Record<string, any>
    try {
      submitParams = { ...params }
      if (Array.isArray(submitParams.images) && submitParams.images.length > 0) {
        submitParams.images = extractCdnUrls(submitParams.images)
      }
    } catch (e: any) {
      message.error(e?.message || '参考图须为已上传的 CDN 地址')
      return
    }

    setSubmitting(true)
    setIsGenerating(true)

    const taskId = `task_${Date.now()}`
    const tempTask: any = {
      id: taskId,
      task_id: taskId,
      session_id: sessionId,
      model_code: currentModel.model_code,
      category: activeCategory,
      status: 'processing',
      params: submitParams,
      params_summary: params.prompt || params.positive_prompt || '生成中...',
      created_at: new Date().toISOString(),
    }
    addTask(tempTask)

    try {
      const res = await generate({
        model_code: currentModel.model_code,
        category: activeCategory,
        session_id: sessionId ?? undefined,
        user_id: useGenerationStore.getState().userId ?? undefined,
        params: submitParams,
      })

      if (res.code === 'success' && res.data) {
        if (!sessionId && (res.data as any).session_id) {
          setSessionId((res.data as any).session_id)
        }
        const store = useGenerationStore.getState()
        const updated: any[] = store.tasks.map((t) =>
          t.task_id === taskId
            ? {
                ...t,
                status: 'success',
                result: (res.data as any).result,
                duration_ms: (res.data as any).duration_ms,
                error_message: undefined,
              }
            : t
        )
        store.setTasks(updated)
        message.success('生成完成')
      } else {
        const store = useGenerationStore.getState()
        const updated: any[] = store.tasks.map((t) =>
          t.task_id === taskId
            ? { ...t, status: 'failed', error_message: res.message || '生成失败' }
            : t
        )
        store.setTasks(updated)
      }
    } catch (err: any) {
      const store = useGenerationStore.getState()
      const updated: any[] = store.tasks.map((t) =>
        t.task_id === taskId
          ? { ...t, status: 'failed', error_message: err.message || '生成失败' }
          : t
      )
      store.setTasks(updated)
    } finally {
      setSubmitting(false)
      setIsGenerating(false)
    }
  }

  const handleReset = () => {
    const defaults: Record<string, any> = {}
    fields.forEach((f) => {
      if (f.default !== undefined) defaults[f.name] = f.default
    })
    setParams(defaults)
    form.resetFields()
    message.info('已重置参数')
  }

  return (
    <Card size="small" title="参数配置">
      <Form layout="vertical" form={form}>
        {fields.filter(isFieldVisible).map((field) => (
          <Form.Item
            key={field.name}
            label={
              <Space>
                <span style={{ fontWeight: 500 }}>
                  {field.label}
                  {field.required && <span style={{ color: '#ff4d4f' }}> *</span>}
                </span>
                {field.help_text && (
                  <Tooltip title={field.help_text}>
                    <span style={{ color: '#aaa', fontSize: 12 }}>?</span>
                  </Tooltip>
                )}
              </Space>
            }
          >
            {renderField(field)}
          </Form.Item>
        ))}

        <Form.Item style={{ marginBottom: 0, marginTop: 16 }}>
          <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
            <Button onClick={handleReset} icon={<ReloadOutlined />}>
              重置
            </Button>
            <Button
              type="primary"
              icon={<ThunderboltOutlined />}
              onClick={handleSubmit}
              loading={submitting}
              disabled={needPromptEmpty || requiredEmpty}
            >
              立即生成
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Card>
  )
}
