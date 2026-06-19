import { BUILTIN_PROFILE_OPTIONS } from '@/constants/onboarding'

export interface OnboardingBinding {
  channel_code?: string
  channel_model_id?: string
  priority?: number
  fallback?: boolean
  mode_profiles?: Record<string, string>
  use_custom_profile?: Record<string, boolean>
  custom_profiles?: Record<string, {
    profile_id?: string
    name?: string
    protocol_slot?: string
    endpoint_type?: string
    http_path?: string
    builder?: string
    parser?: string
    size_strategy?: string
  }>
}

export interface OnboardingFormValues {
  ticket_title?: string
  priority?: string
  owner?: string
  expected_date?: string
  model_code?: string
  model_name?: string
  category?: string
  description?: string
  allow_channel_fallback?: boolean
  supported_modes?: string[]
  channel_mode?: 'reuse' | 'new'
  channel_code?: string
  channel_name?: string
  channel_provider?: string
  channel_type?: string
  base_url?: string
  api_key?: string
  endpoints?: Array<{ protocol_slot?: string; type?: string; endpoint?: string; method?: string; content_type?: string }>
  bindings?: OnboardingBinding[]
  official_curl?: string
  official_response_success?: string
  official_response_error?: string
  reference_image_rule?: string
  notes?: string
}

export interface RequiredFieldIssue {
  step: number
  stepTitle: string
  field: string
  label: string
}

const BUILTIN_IDS = new Set(BUILTIN_PROFILE_OPTIONS.map((p) => p.value))

export function modesForCategory(category?: string): string[] {
  const map: Record<string, string[]> = {
    text: ['text_chat'],
    image: ['text_to_image', 'image_to_image'],
    video: ['text_to_video', 'image_to_video'],
  }
  return map[category || ''] || []
}

export function collectRequiredIssues(values: OnboardingFormValues): RequiredFieldIssue[] {
  const issues: RequiredFieldIssue[] = []
  const push = (step: number, stepTitle: string, field: string, label: string, missing: boolean) => {
    if (missing) issues.push({ step, stepTitle, field, label })
  }

  push(0, '概述', 'ticket_title', '工单标题', !values.ticket_title?.trim())
  push(1, '产品模型', 'model_code', '模型编码 model_code', !values.model_code?.trim())
  push(1, '产品模型', 'model_name', '显示名称 model_name', !values.model_name?.trim())
  push(1, '产品模型', 'category', '分类 category', !values.category)
  push(2, '任务模式', 'supported_modes', '至少勾选一种任务模式', !values.supported_modes?.length)

  const channelMode = values.channel_mode || 'reuse'
  if (channelMode === 'reuse') {
    push(3, '渠道', 'channel_code', '复用渠道 channel_code', !values.channel_code?.trim())
  } else {
    push(3, '渠道', 'channel_code', '渠道编码 channel_code', !values.channel_code?.trim())
    push(3, '渠道', 'channel_name', '渠道名称', !values.channel_name?.trim())
    push(3, '渠道', 'channel_provider', '渠道提供商', !values.channel_provider)
    push(3, '渠道', 'base_url', '接口根地址 base_url', !values.base_url?.trim())
  }

  const bindings = values.bindings || []
  push(4, '绑定与协议', 'bindings', '至少一条渠道绑定', bindings.length === 0)

  const modes = values.supported_modes || []
  bindings.forEach((b, i) => {
    const prefix = `绑定 ${i + 1}`
    push(4, '绑定与协议', `bindings.${i}.channel_code`, `${prefix} · 渠道编码`, !b.channel_code?.trim())
    push(4, '绑定与协议', `bindings.${i}.channel_model_id`, `${prefix} · 渠道模型 ID`, !b.channel_model_id?.trim())
    push(4, '绑定与协议', `bindings.${i}.priority`, `${prefix} · 优先级 priority`, b.priority === undefined || b.priority === null)

    modes.forEach((mode) => {
      const profileId = b.mode_profiles?.[mode]
      const isCustom = b.use_custom_profile?.[mode]
      push(
        4,
        '绑定与协议',
        `bindings.${i}.mode_profiles.${mode}`,
        `${prefix} · 模式 ${mode} 的 profile_id`,
        !profileId?.trim(),
      )
      if (isCustom && profileId && !BUILTIN_IDS.has(profileId)) {
        const cp = b.custom_profiles?.[mode]
        push(4, '绑定与协议', `bindings.${i}.custom.${mode}.protocol_slot`, `${prefix} · ${mode} 协议槽位`, !cp?.protocol_slot?.trim())
        push(4, '绑定与协议', `bindings.${i}.custom.${mode}.http_path`, `${prefix} · ${mode} HTTP 路径`, !cp?.http_path?.trim())
        push(4, '绑定与协议', `bindings.${i}.custom.${mode}.builder`, `${prefix} · ${mode} request.builder`, !cp?.builder)
        push(4, '绑定与协议', `bindings.${i}.custom.${mode}.parser`, `${prefix} · ${mode} response.parser`, !cp?.parser)
      }
    })
  })

  const needsDoc = bindings.some((b) =>
    modes.some((mode) => {
      const pid = b.mode_profiles?.[mode]
      return pid && (b.use_custom_profile?.[mode] || !BUILTIN_IDS.has(pid))
    }),
  )
  if (needsDoc) {
    push(5, '官方文档', 'official_curl', '官方请求 curl 示例', !values.official_curl?.trim())
    push(5, '官方文档', 'official_response_success', '官方成功响应 JSON', !values.official_response_success?.trim())
  }

  return issues
}

export function isOnboardingComplete(values: OnboardingFormValues): boolean {
  return collectRequiredIssues(values).length === 0
}

function mdRow(label: string, value: string | number | boolean | undefined | null): string {
  const v = value === undefined || value === null || value === '' ? '（未填）' : String(value)
  return `| ${label} | ${v} |`
}

export function buildOnboardingMarkdown(values: OnboardingFormValues): string {
  const modes = values.supported_modes || []
  const bindings = values.bindings || []
  const lines: string[] = [
    '## 接入工单',
    '',
    '### 0. 元信息',
    `- 工单标题：${values.ticket_title || '（未填）'}`,
    `- 优先级：${values.priority || 'P1'}`,
    `- 期望上线：${values.expected_date || '（未填）'}`,
    `- 负责人：${values.owner || '（未填）'}`,
    '',
    '### 1. 产品模型',
    '',
    '| 项 | 值 |',
    '|----|-----|',
    mdRow('model_code', values.model_code),
    mdRow('model_name', values.model_name),
    mdRow('category', values.category),
    mdRow('description', values.description),
    mdRow('allow_channel_fallback', values.allow_channel_fallback ?? true),
    '',
    '### 2. 任务模式矩阵',
    '',
    '| invocation_mode | 需要 |',
    '|-----------------|------|',
    ...['text_chat', 'text_to_image', 'image_to_image', 'text_to_video', 'image_to_video'].map(
      (m) => `| ${m} | ${modes.includes(m) ? '☑' : '☐'} |`,
    ),
    '',
    '### 3. 渠道',
    '',
  ]

  if (values.channel_mode === 'new') {
    lines.push(
      '**新建渠道**',
      '',
      '| 项 | 值 |',
      '|----|-----|',
      mdRow('channel_code', values.channel_code),
      mdRow('channel_name', values.channel_name),
      mdRow('channel_type', values.channel_type || 'aggregator'),
      mdRow('channel_provider', values.channel_provider),
      mdRow('base_url', values.base_url),
      mdRow('api_key', values.api_key ? '***已提供***' : undefined),
      '',
    )
    if (values.endpoints?.length) {
      lines.push(
        '#### endpoints',
        '',
        '| protocol_slot | type | endpoint | method | content_type |',
        '|---------------|------|----------|--------|--------------|',
        ...values.endpoints.map(
          (ep) =>
            `| ${ep.protocol_slot || ''} | ${ep.type || ''} | ${ep.endpoint || ''} | ${ep.method || 'POST'} | ${ep.content_type || ''} |`,
        ),
        '',
      )
    }
  } else {
    lines.push(`- 复用已有渠道：**${values.channel_code || '（未填）'}**`, '')
  }

  lines.push('### 4. 协议画像与绑定', '')

  bindings.forEach((b, idx) => {
    lines.push(
      `#### 绑定 ${idx + 1}`,
      '',
      '| 项 | 值 |',
      '|----|-----|',
      mdRow('channel_code', b.channel_code),
      mdRow('channel_model_id', b.channel_model_id),
      mdRow('priority', b.priority),
      mdRow('fallback', b.fallback ?? '沿用模型级'),
      '',
      '**mode_profiles：**',
      '',
      '| invocation_mode | profile_id | 类型 |',
      '|-----------------|------------|------|',
    )
    modes.forEach((mode) => {
      const pid = b.mode_profiles?.[mode] || ''
      const kind = pid && BUILTIN_IDS.has(pid) ? '内置' : '自定义'
      lines.push(`| ${mode} | ${pid || '（未填）'} | ${kind} |`)
    })
    lines.push('')

    modes.forEach((mode) => {
      if (!b.use_custom_profile?.[mode]) return
      const cp = b.custom_profiles?.[mode]
      if (!cp) return
      lines.push(
        `##### 自定义画像 · ${mode}`,
        '',
        '| 项 | 值 |',
        '|----|-----|',
        mdRow('profile_id', cp.profile_id || b.mode_profiles?.[mode]),
        mdRow('protocol_slot', cp.protocol_slot),
        mdRow('endpoint_type', cp.endpoint_type),
        mdRow('http.path', cp.http_path),
        mdRow('request.builder', cp.builder),
        mdRow('request.size_strategy', cp.size_strategy),
        mdRow('response.parser', cp.parser),
        '',
      )
    })
  })

  if (values.official_curl || values.official_response_success) {
    lines.push(
      '### 5. 官方文档佐证',
      '',
      '#### 请求 curl',
      '```bash',
      values.official_curl || '# 未提供',
      '```',
      '',
      '#### 成功响应',
      '```json',
      values.official_response_success || '{}',
      '```',
      '',
    )
    if (values.official_response_error) {
      lines.push(
        '#### 失败响应',
        '```json',
        values.official_response_error,
        '```',
        '',
      )
    }
  }

  if (values.reference_image_rule || values.notes) {
    lines.push(
      '### 6. 补充说明',
      '',
      values.reference_image_rule ? `- 参考图要求：${values.reference_image_rule}` : '',
      values.notes ? `- 备注：${values.notes}` : '',
      '',
    )
  }

  lines.push(
    '### 7. 验收（待执行）',
    '',
    '- [ ] 各模式冒烟通过',
    '- [ ] 链路日志含 invocation_mode / profile_id / protocol_slot',
    '- [ ] channel_request 在 HTTP 前落库',
    '',
  )

  return lines.filter((l) => l !== undefined).join('\n')
}
