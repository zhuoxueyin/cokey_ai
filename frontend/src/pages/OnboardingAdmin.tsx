import { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Button,
  Card,
  Checkbox,
  Col,
  DatePicker,
  Divider,
  Form,
  Input,
  InputNumber,
  Radio,
  Row,
  Select,
  Space,
  Steps,
  Switch,
  Tag,
  Typography,
  message,
} from 'antd'
import {
  CopyOutlined,
  DownloadOutlined,
  SaveOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import { listChannelsAdmin, listProtocolProfilesAdmin } from '@/api'
import {
  BUILTIN_PROFILE_OPTIONS,
  BUILDER_OPTIONS,
  CATEGORY_OPTIONS,
  CHANNEL_PROVIDER_OPTIONS,
  DEFAULT_ENDPOINTS_BY_MODE,
  INVOCATION_MODES,
  PARSER_OPTIONS,
  SIZE_STRATEGY_OPTIONS,
} from '@/constants/onboarding'
import {
  collectRequiredIssues,
  buildOnboardingMarkdown,
  modesForCategory,
  type OnboardingFormValues,
} from '@/utils/onboardingExport'

const { TextArea } = Input
const { Title, Text, Paragraph } = Typography
const DRAFT_KEY = 'onboarding_work_order_draft'

const STEP_TITLES = ['概述', '产品模型', '任务模式', '渠道', '绑定与协议', '官方文档', '导出工单']

const defaultBinding = () => ({
  channel_code: '',
  channel_model_id: '',
  priority: 20,
  fallback: true,
  mode_profiles: {} as Record<string, string>,
  use_custom_profile: {} as Record<string, boolean>,
  custom_profiles: {} as Record<string, object>,
})

export default function OnboardingAdmin() {
  const [form] = Form.useForm<OnboardingFormValues>()
  const [step, setStep] = useState(0)
  const [channels, setChannels] = useState<{ channel_code: string; channel_name: string }[]>([])
  const [profileOptions, setProfileOptions] = useState(BUILTIN_PROFILE_OPTIONS)
  const [exportedMd, setExportedMd] = useState('')
  const watched = Form.useWatch([], form)

  useEffect(() => {
    listChannelsAdmin({ page: 1, page_size: 100, status: 'active' }).then((res) => {
      if (res.code === 'success' && res.data) {
        setChannels(res.data.map((c: { channel_code: string; channel_name: string }) => ({
          channel_code: c.channel_code,
          channel_name: c.channel_name,
        })))
      }
    })
    listProtocolProfilesAdmin({ page: 1, page_size: 100 }).then((res) => {
      if (res.code === 'success' && res.data?.length) {
        const fromApi = res.data.map((p: { profile_id: string; name: string; invocation_mode: string }) => ({
          value: p.profile_id,
          label: `${p.name} (${p.profile_id})`,
          mode: p.invocation_mode,
        }))
        const seen = new Set(fromApi.map((x: { value: string }) => x.value))
        const merged = [...fromApi, ...BUILTIN_PROFILE_OPTIONS.filter((b) => !seen.has(b.value))]
        setProfileOptions(merged)
      }
    }).catch(() => {})
  }, [])

  useEffect(() => {
    try {
      const raw = localStorage.getItem(DRAFT_KEY)
      if (raw) {
        const draft = JSON.parse(raw)
        if (draft.expected_date) draft.expected_date = dayjs(draft.expected_date)
        form.setFieldsValue(draft)
      }
    } catch {
      /* ignore */
    }
  }, [form])

  const values = (watched || form.getFieldsValue()) as OnboardingFormValues
  const requiredIssues = useMemo(() => collectRequiredIssues(values), [values])
  const complete = requiredIssues.length === 0

  const category = Form.useWatch('category', form)
  const supportedModes = Form.useWatch('supported_modes', form) || []
  const channelMode = Form.useWatch('channel_mode', form) || 'reuse'

  useEffect(() => {
    if (!category) return
    const suggested = modesForCategory(category)
    const current = form.getFieldValue('supported_modes') as string[] | undefined
    if (!current?.length) {
      form.setFieldValue('supported_modes', suggested)
    }
  }, [category, form])

  const saveDraft = () => {
    const v = form.getFieldsValue()
    const payload = {
      ...v,
      expected_date: v.expected_date ? dayjs(v.expected_date).format('YYYY-MM-DD') : undefined,
    }
    localStorage.setItem(DRAFT_KEY, JSON.stringify(payload))
    message.success('草稿已保存到浏览器')
  }

  const handleExport = () => {
    const v = form.getFieldsValue()
    const issues = collectRequiredIssues(v)
    if (issues.length) {
      message.warning(`还有 ${issues.length} 项必填未填，请先在左侧清单补全`)
      return
    }
    const md = buildOnboardingMarkdown({
      ...v,
      expected_date: v.expected_date ? dayjs(v.expected_date).format('YYYY-MM-DD') : undefined,
    })
    setExportedMd(md)
    setStep(6)
  }

  const copyMarkdown = async () => {
    const md = exportedMd || buildOnboardingMarkdown(form.getFieldsValue())
    try {
      await navigator.clipboard.writeText(md)
      message.success('已复制到剪贴板，可直接发给 AI 配置')
    } catch {
      message.error('复制失败，请手动全选复制')
    }
  }

  const downloadMarkdown = () => {
    const md = exportedMd || buildOnboardingMarkdown(form.getFieldsValue())
    const code = values.model_code || 'model'
    const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `onboarding-${code}-${dayjs().format('YYYYMMDD-HHmm')}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  const issuesByStep = useMemo(() => {
    const map: Record<number, typeof requiredIssues> = {}
    requiredIssues.forEach((i) => {
      if (!map[i.step]) map[i.step] = []
      map[i.step].push(i)
    })
    return map
  }, [requiredIssues])

  const profileOptionsForMode = (mode: string) =>
    profileOptions.filter((p) => p.mode === mode)

  const renderRequiredSidebar = () => (
    <Card
      size="small"
      title={
        <Space>
          {complete ? (
            <CheckCircleOutlined style={{ color: '#52c41a' }} />
          ) : (
            <ExclamationCircleOutlined style={{ color: '#faad14' }} />
          )}
          <span>必填项检查</span>
          {!complete && <Tag color="warning">{requiredIssues.length} 项待填</Tag>}
          {complete && <Tag color="success">已全部填写</Tag>}
        </Space>
      }
      style={{ position: 'sticky', top: 16 }}
    >
      {complete ? (
        <Text type="success">所有必填项已填写，可导出工单发给 AI 落库配置。</Text>
      ) : (
        <div style={{ maxHeight: 'calc(100vh - 220px)', overflowY: 'auto' }}>
          {STEP_TITLES.map((title, idx) => {
            const items = issuesByStep[idx]
            if (!items?.length) return null
            return (
              <div key={idx} style={{ marginBottom: 12 }}>
                <Text strong style={{ fontSize: 12, color: '#666' }}>
                  步骤 {idx + 1} · {title}
                </Text>
                <ul style={{ margin: '4px 0 0', paddingLeft: 18, fontSize: 13 }}>
                  {items.map((it) => (
                    <li key={it.field}>
                      <a
                        onClick={() => setStep(idx)}
                        style={{ color: '#d48806', cursor: 'pointer' }}
                      >
                        {it.label}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            )
          })}
        </div>
      )}
      <Divider style={{ margin: '12px 0' }} />
      <Paragraph type="secondary" style={{ fontSize: 12, marginBottom: 8 }}>
        带 <Text type="danger">*</Text> 为必填。使用内置协议画像可跳过官方 curl。
      </Paragraph>
      <Button block icon={<SaveOutlined />} onClick={saveDraft}>
        保存草稿
      </Button>
    </Card>
  )

  return (
    <div style={{ height: '100%', overflow: 'auto', padding: 24 }}>
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        <Title level={4} style={{ marginBottom: 4 }}>
          模型 / 渠道接入工单
        </Title>
        <Paragraph type="secondary" style={{ marginBottom: 20 }}>
          按步骤填写必填项，导出 Markdown 工单后发给 AI，即可按 SOP 自动落库配置。
        </Paragraph>

        <Steps
          current={step}
          onChange={setStep}
          size="small"
          style={{ marginBottom: 24 }}
          items={STEP_TITLES.map((t, i) => ({
            title: t,
            status: issuesByStep[i]?.length ? 'error' : undefined,
          }))}
        />

        <Row gutter={24}>
          <Col xs={24} lg={17}>
            <Form
              form={form}
              layout="vertical"
              initialValues={{
                priority: 'P1',
                channel_mode: 'reuse',
                channel_type: 'aggregator',
                allow_channel_fallback: true,
                bindings: [defaultBinding()],
                endpoints: [],
              }}
            >
              {step === 0 && (
                <Card title="0. 概述">
                  <Form.Item
                    label="工单标题"
                    name="ticket_title"
                    rules={[{ required: true, message: '请填写工单标题' }]}
                    extra="例：接入 Banana 文生图 @ APIYI"
                  >
                    <Input placeholder="简要描述本次接入" />
                  </Form.Item>
                  <Row gutter={16}>
                    <Col span={8}>
                      <Form.Item label="优先级" name="priority">
                        <Select options={[
                          { value: 'P0', label: 'P0 紧急' },
                          { value: 'P1', label: 'P1 正常' },
                          { value: 'P2', label: 'P2 低优' },
                        ]} />
                      </Form.Item>
                    </Col>
                    <Col span={8}>
                      <Form.Item label="期望上线" name="expected_date">
                        <DatePicker style={{ width: '100%' }} />
                      </Form.Item>
                    </Col>
                    <Col span={8}>
                      <Form.Item label="负责人" name="owner">
                        <Input placeholder="姓名" />
                      </Form.Item>
                    </Col>
                  </Row>
                </Card>
              )}

              {step === 1 && (
                <Card title="1. 产品模型">
                  <Row gutter={16}>
                    <Col span={12}>
                      <Form.Item
                        label="模型编码 model_code"
                        name="model_code"
                        rules={[
                          { required: true, message: '必填' },
                          { pattern: /^[a-z0-9][a-z0-9-_]*$/i, message: '字母数字、-、_' },
                        ]}
                      >
                        <Input placeholder="banana-image-1" />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item
                        label="显示名称 model_name"
                        name="model_name"
                        rules={[{ required: true, message: '必填' }]}
                      >
                        <Input placeholder="Banana 文生图" />
                      </Form.Item>
                    </Col>
                  </Row>
                  <Form.Item
                    label="分类 category"
                    name="category"
                    rules={[{ required: true, message: '请选择分类' }]}
                  >
                    <Select options={CATEGORY_OPTIONS} placeholder="text / image / video" />
                  </Form.Item>
                  <Form.Item label="描述" name="description">
                    <TextArea rows={2} placeholder="面向用户的模型说明" />
                  </Form.Item>
                  <Form.Item label="主渠道失败时降级" name="allow_channel_fallback" valuePropName="checked">
                    <Switch checkedChildren="允许" unCheckedChildren="禁止" />
                  </Form.Item>
                </Card>
              )}

              {step === 2 && (
                <Card title="2. 任务模式（至少选一项）">
                  <Alert
                    type="info"
                    showIcon
                    style={{ marginBottom: 16 }}
                    message="根据 category 已预选常见模式，请确认或调整"
                  />
                  <Form.Item
                    name="supported_modes"
                    rules={[{ required: true, type: 'array', min: 1, message: '至少选择一种任务模式' }]}
                  >
                    <Checkbox.Group style={{ width: '100%' }}>
                      <Row>
                        {INVOCATION_MODES.map((m) => (
                          <Col span={24} key={m.value} style={{ marginBottom: 8 }}>
                            <Checkbox value={m.value}>
                              {m.label}
                              <Text type="secondary" style={{ marginLeft: 8, fontSize: 12 }}>
                                适用 category={m.category}
                              </Text>
                            </Checkbox>
                          </Col>
                        ))}
                      </Row>
                    </Checkbox.Group>
                  </Form.Item>
                </Card>
              )}

              {step === 3 && (
                <Card title="3. 渠道">
                  <Form.Item label="渠道方式" name="channel_mode" rules={[{ required: true }]}>
                    <Radio.Group>
                      <Radio value="reuse">复用已有渠道</Radio>
                      <Radio value="new">新建渠道</Radio>
                    </Radio.Group>
                  </Form.Item>

                  {channelMode === 'reuse' ? (
                    <Form.Item
                      label="渠道编码 channel_code"
                      name="channel_code"
                      rules={[{ required: true, message: '请选择或填写渠道编码' }]}
                    >
                      <Select
                        showSearch
                        placeholder="选择已有渠道"
                        options={channels.map((c) => ({
                          value: c.channel_code,
                          label: `${c.channel_name} (${c.channel_code})`,
                        }))}
                        optionFilterProp="label"
                      />
                    </Form.Item>
                  ) : (
                    <>
                      <Row gutter={16}>
                        <Col span={12}>
                          <Form.Item label="渠道编码" name="channel_code" rules={[{ required: true }]}>
                            <Input placeholder="channel_xxx" />
                          </Form.Item>
                        </Col>
                        <Col span={12}>
                          <Form.Item label="渠道名称" name="channel_name" rules={[{ required: true }]}>
                            <Input />
                          </Form.Item>
                        </Col>
                      </Row>
                      <Row gutter={16}>
                        <Col span={12}>
                          <Form.Item label="提供商" name="channel_provider" rules={[{ required: true }]}>
                            <Select options={CHANNEL_PROVIDER_OPTIONS} />
                          </Form.Item>
                        </Col>
                        <Col span={12}>
                          <Form.Item label="类型" name="channel_type">
                            <Select options={[
                              { value: 'aggregator', label: '聚合 aggregator' },
                              { value: 'direct', label: '直连 direct' },
                            ]} />
                          </Form.Item>
                        </Col>
                      </Row>
                      <Form.Item
                        label="base_url"
                        name="base_url"
                        rules={[{ required: true, message: '必填' }, { type: 'url', warningOnly: true }]}
                      >
                        <Input placeholder="https://api.example.com/v1" />
                      </Form.Item>
                      <Form.Item label="api_key" name="api_key" extra="导出工单时会脱敏显示">
                        <Input.Password placeholder="渠道 API Key" />
                      </Form.Item>
                      <Divider orientation="left" plain>HTTP 端点（按已选模式预填）</Divider>
                      <Form.List name="endpoints">
                        {(fields, { add, remove }) => (
                          <>
                            {fields.map((field) => (
                              <Row key={field.key} gutter={8} align="middle" style={{ marginBottom: 8 }}>
                                <Col span={6}>
                                  <Form.Item {...field} name={[field.name, 'protocol_slot']} noStyle>
                                    <Input placeholder="protocol_slot" />
                                  </Form.Item>
                                </Col>
                                <Col span={4}>
                                  <Form.Item {...field} name={[field.name, 'type']} noStyle>
                                    <Input placeholder="type" />
                                  </Form.Item>
                                </Col>
                                <Col span={6}>
                                  <Form.Item {...field} name={[field.name, 'endpoint']} noStyle>
                                    <Input placeholder="path" />
                                  </Form.Item>
                                </Col>
                                <Col span={4}>
                                  <Form.Item {...field} name={[field.name, 'content_type']} noStyle>
                                    <Input placeholder="content-type" />
                                  </Form.Item>
                                </Col>
                                <Col span={2}>
                                  <Button type="link" danger onClick={() => remove(field.name)}>删</Button>
                                </Col>
                              </Row>
                            ))}
                            <Space>
                              <Button
                                type="dashed"
                                onClick={() => {
                                  const modes = form.getFieldValue('supported_modes') as string[] || []
                                  const mode = modes[0]
                                  const def = mode ? DEFAULT_ENDPOINTS_BY_MODE[mode] : undefined
                                  add(def ? { ...def, method: 'POST' } : { method: 'POST' })
                                }}
                              >
                                添加端点
                              </Button>
                              <Button
                                type="link"
                                onClick={() => {
                                  const modes = form.getFieldValue('supported_modes') as string[] || []
                                  const eps = modes
                                    .map((m) => DEFAULT_ENDPOINTS_BY_MODE[m])
                                    .filter(Boolean)
                                  const unique = Array.from(
                                    new Map(eps.map((e) => [e.protocol_slot, { ...e, method: 'POST' }])).values(),
                                  )
                                  form.setFieldValue('endpoints', unique)
                                }}
                              >
                                按任务模式一键填充
                              </Button>
                            </Space>
                          </>
                        )}
                      </Form.List>
                    </>
                  )}
                </Card>
              )}

              {step === 4 && (
                <Card title="4. 渠道绑定与协议画像">
                  <Alert
                    type="warning"
                    showIcon
                    style={{ marginBottom: 16 }}
                    message="每个已选任务模式都必须指定 profile_id（可选用内置画像）"
                  />
                  <Form.List name="bindings">
                    {(fields, { add, remove }) => (
                      <>
                        {fields.map((field, bindIdx) => (
                          <Card
                            key={field.key}
                            size="small"
                            type="inner"
                            title={`绑定 ${bindIdx + 1}${bindIdx === 0 ? '（主渠道，priority 最高）' : '（备用）'}`}
                            style={{ marginBottom: 16 }}
                            extra={
                              fields.length > 1 ? (
                                <Button type="link" danger onClick={() => remove(field.name)}>删除</Button>
                              ) : null
                            }
                          >
                            <Row gutter={16}>
                              <Col span={8}>
                                <Form.Item
                                  {...field}
                                  label="渠道编码"
                                  name={[field.name, 'channel_code']}
                                  rules={[{ required: true, message: '必填' }]}
                                >
                                  <Select
                                    showSearch
                                    placeholder="channel_code"
                                    options={channels.map((c) => ({
                                      value: c.channel_code,
                                      label: c.channel_code,
                                    }))}
                                  />
                                </Form.Item>
                              </Col>
                              <Col span={8}>
                                <Form.Item
                                  {...field}
                                  label="渠道模型 ID"
                                  name={[field.name, 'channel_model_id']}
                                  rules={[{ required: true, message: '必填' }]}
                                  extra="渠道侧模型名，可与 model_code 不同"
                                >
                                  <Input placeholder="gpt-image-2-vip" />
                                </Form.Item>
                              </Col>
                              <Col span={4}>
                                <Form.Item
                                  {...field}
                                  label="priority"
                                  name={[field.name, 'priority']}
                                  rules={[{ required: true, message: '必填' }]}
                                >
                                  <InputNumber min={1} max={100} style={{ width: '100%' }} />
                                </Form.Item>
                              </Col>
                              <Col span={4}>
                                <Form.Item
                                  {...field}
                                  label="参与降级"
                                  name={[field.name, 'fallback']}
                                  valuePropName="checked"
                                >
                                  <Switch />
                                </Form.Item>
                              </Col>
                            </Row>

                            <Divider plain style={{ margin: '8px 0 16px' }}>mode_profiles 映射</Divider>
                            {supportedModes.map((mode: string) => {
                              const modeLabel = INVOCATION_MODES.find((m) => m.value === mode)?.label || mode
                              return (
                                <div key={mode} style={{ marginBottom: 16, padding: 12, background: '#fafafa', borderRadius: 8 }}>
                                  <Text strong>{modeLabel}</Text>
                                  <Row gutter={12} style={{ marginTop: 8 }}>
                                    <Col span={16}>
                                      <Form.Item
                                        {...field}
                                        name={[field.name, 'mode_profiles', mode]}
                                        rules={[{ required: true, message: '请选择 profile_id' }]}
                                        style={{ marginBottom: 8 }}
                                      >
                                        <Select
                                          showSearch
                                          placeholder="选择内置或输入自定义 profile_id"
                                          options={profileOptionsForMode(mode)}
                                          optionFilterProp="label"
                                          allowClear
                                        />
                                      </Form.Item>
                                    </Col>
                                    <Col span={8}>
                                      <Form.Item
                                        {...field}
                                        name={[field.name, 'use_custom_profile', mode]}
                                        valuePropName="checked"
                                        style={{ marginBottom: 8 }}
                                      >
                                        <Checkbox>自定义协议详情</Checkbox>
                                      </Form.Item>
                                    </Col>
                                  </Row>
                                  <Form.Item noStyle shouldUpdate>
                                    {() => {
                                      const useCustom = form.getFieldValue([
                                        'bindings',
                                        field.name,
                                        'use_custom_profile',
                                        mode,
                                      ])
                                      if (!useCustom) return null
                                      return (
                                        <Row gutter={12}>
                                          <Col span={12}>
                                            <Form.Item
                                              {...field}
                                              label="protocol_slot"
                                              name={[field.name, 'custom_profiles', mode, 'protocol_slot']}
                                              rules={[{ required: true }]}
                                            >
                                              <Input placeholder="openai.images.generations" />
                                            </Form.Item>
                                          </Col>
                                          <Col span={12}>
                                            <Form.Item
                                              {...field}
                                              label="http.path"
                                              name={[field.name, 'custom_profiles', mode, 'http_path']}
                                              rules={[{ required: true }]}
                                            >
                                              <Input placeholder="images/generations" />
                                            </Form.Item>
                                          </Col>
                                          <Col span={8}>
                                            <Form.Item
                                              {...field}
                                              label="endpoint_type"
                                              name={[field.name, 'custom_profiles', mode, 'endpoint_type']}
                                            >
                                              <Select options={[
                                                'chat', 'image', 'image_edits', 'video', 'video_image', 'text',
                                              ].map((v) => ({ value: v, label: v }))} />
                                            </Form.Item>
                                          </Col>
                                          <Col span={8}>
                                            <Form.Item
                                              {...field}
                                              label="builder"
                                              name={[field.name, 'custom_profiles', mode, 'builder']}
                                              rules={[{ required: true }]}
                                            >
                                              <Select options={BUILDER_OPTIONS} />
                                            </Form.Item>
                                          </Col>
                                          <Col span={8}>
                                            <Form.Item
                                              {...field}
                                              label="parser"
                                              name={[field.name, 'custom_profiles', mode, 'parser']}
                                              rules={[{ required: true }]}
                                            >
                                              <Select options={PARSER_OPTIONS} />
                                            </Form.Item>
                                          </Col>
                                          <Col span={8}>
                                            <Form.Item
                                              {...field}
                                              label="size_strategy"
                                              name={[field.name, 'custom_profiles', mode, 'size_strategy']}
                                            >
                                              <Select options={SIZE_STRATEGY_OPTIONS} allowClear />
                                            </Form.Item>
                                          </Col>
                                        </Row>
                                      )
                                    }}
                                  </Form.Item>
                                </div>
                              )
                            })}
                          </Card>
                        ))}
                        <Button type="dashed" block onClick={() => add({ ...defaultBinding(), priority: 10 })}>
                          添加备用渠道绑定
                        </Button>
                      </>
                    )}
                  </Form.List>
                </Card>
              )}

              {step === 5 && (
                <Card title="5. 官方文档佐证">
                  <Alert
                    type="info"
                    showIcon
                    style={{ marginBottom: 16 }}
                    message="仅在使用自定义协议画像时必填；全部使用内置画像可跳过"
                  />
                  <Form.Item
                    label="官方请求 curl"
                    name="official_curl"
                    extra="从厂商文档粘贴完整 curl"
                  >
                    <TextArea rows={6} placeholder="curl -X POST https://..." style={{ fontFamily: 'monospace' }} />
                  </Form.Item>
                  <Form.Item label="成功响应 JSON" name="official_response_success">
                    <TextArea rows={5} placeholder='{"data":[{"url":"..."}]}' style={{ fontFamily: 'monospace' }} />
                  </Form.Item>
                  <Form.Item label="失败响应 JSON（选填）" name="official_response_error">
                    <TextArea rows={3} style={{ fontFamily: 'monospace' }} />
                  </Form.Item>
                  <Form.Item label="参考图要求" name="reference_image_rule">
                    <Input placeholder="必须 CDN URL / 支持 base64 / 不支持" />
                  </Form.Item>
                  <Form.Item label="备注" name="notes">
                    <TextArea rows={2} />
                  </Form.Item>
                </Card>
              )}

              {step === 6 && (
                <Card
                  title="6. 导出工单"
                  extra={
                    <Space>
                      <Button icon={<CopyOutlined />} type="primary" onClick={copyMarkdown} disabled={!complete}>
                        复制发给 AI
                      </Button>
                      <Button icon={<DownloadOutlined />} onClick={downloadMarkdown} disabled={!complete}>
                        下载 .md
                      </Button>
                    </Space>
                  }
                >
                  {!complete ? (
                    <Alert
                      type="error"
                      showIcon
                      message={`仍有 ${requiredIssues.length} 项必填未填，请返回对应步骤补全`}
                    />
                  ) : (
                    <Alert type="success" showIcon message="必填项已全部完成，可复制工单发给 AI 执行落库" style={{ marginBottom: 16 }} />
                  )}
                  <TextArea
                    value={exportedMd || (complete ? buildOnboardingMarkdown(form.getFieldsValue()) : '')}
                    readOnly
                    rows={22}
                    style={{ fontFamily: 'monospace', fontSize: 12 }}
                  />
                </Card>
              )}

              <div style={{ marginTop: 24, display: 'flex', justifyContent: 'space-between' }}>
                <Button disabled={step === 0} onClick={() => setStep((s) => s - 1)}>
                  上一步
                </Button>
                <Space>
                  {step < 6 && (
                    <Button type="primary" onClick={() => setStep((s) => s + 1)}>
                      下一步
                    </Button>
                  )}
                  {step === 5 && (
                    <Button type="primary" icon={<CheckCircleOutlined />} onClick={handleExport}>
                      校验并生成工单
                    </Button>
                  )}
                </Space>
              </div>
            </Form>
          </Col>

          <Col xs={24} lg={7}>
            {renderRequiredSidebar()}
          </Col>
        </Row>
      </div>
    </div>
  )
}
