import { Button, Card, Col, Empty, Input, InputNumber, Row, Select, Space, Switch, Tag } from 'antd'
import type { ChannelBinding, ChannelItem } from '@/types'
import { INVOCATION_MODE_LABELS } from '@/constants/protocol'
import { modesForCategory } from '@/utils/onboardingExport'

const { Option } = Select

export interface ProfileOption {
  value: string
  label: string
  mode: string
}

interface Props {
  bindings: ChannelBinding[]
  channelList: ChannelItem[]
  profileOptions: ProfileOption[]
  category: 'text' | 'image' | 'video'
  onChange: (bindings: ChannelBinding[]) => void
}

export default function ChannelBindingEditor({
  bindings,
  channelList,
  profileOptions,
  category,
  onChange,
}: Props) {
  const modes = modesForCategory(category)

  const updateBinding = (idx: number, patch: Partial<ChannelBinding>) => {
    const next = [...bindings]
    next[idx] = { ...next[idx], ...patch }
    onChange(next)
  }

  const updateModeProfile = (idx: number, mode: string, profileId: string) => {
    const b = bindings[idx]
    const mode_profiles = { ...(b.mode_profiles || {}), [mode]: profileId }
    updateBinding(idx, { mode_profiles })
  }

  const addBinding = () => {
    const defaultChannel = channelList.find((c) => c.status === 'active') || channelList[0]
    if (!defaultChannel) return
    onChange([
      ...bindings,
      {
        channel_code: defaultChannel.channel_code,
        channel_model_id: '',
        priority: bindings.length === 0 ? 20 : 10,
        status: 'active',
        fallback: true,
        mode_profiles: {},
      },
    ])
  }

  const profilesForMode = (mode: string) =>
    profileOptions.filter((p) => p.mode === mode)

  return (
    <div>
      <div style={{ marginBottom: 12 }}>
        <Button type="primary" onClick={addBinding} disabled={channelList.length === 0}>
          + 绑定渠道
        </Button>
      </div>

      {bindings.length === 0 && (
        <Empty description="还没有绑定渠道" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      )}

      {bindings.map((b, idx) => (
        <Card
          key={idx}
          size="small"
          style={{ marginBottom: 10 }}
          title={
            <Space>
              <span>绑定 #{idx + 1}</span>
              {idx === 0 && <Tag color="gold">主渠道</Tag>}
              {b.status === 'active' ? <Tag color="green">启用</Tag> : <Tag>禁用</Tag>}
            </Space>
          }
          extra={
            bindings.length > 1 ? (
              <Button
                size="small"
                danger
                type="text"
                onClick={() => onChange(bindings.filter((_, i) => i !== idx))}
              >
                删除
              </Button>
            ) : null
          }
        >
          <Row gutter={12}>
            <Col span={8}>
              <div style={{ fontSize: 12, color: '#666', marginBottom: 4 }}>渠道 *</div>
              <Select
                value={b.channel_code}
                onChange={(val) => updateBinding(idx, { channel_code: val })}
                style={{ width: '100%' }}
              >
                {channelList.map((c) => (
                  <Option key={c.channel_code} value={c.channel_code}>
                    {c.channel_name}
                    {c.status !== 'active' ? ' (已停用)' : ''}
                  </Option>
                ))}
              </Select>
            </Col>
            <Col span={8}>
              <div style={{ fontSize: 12, color: '#666', marginBottom: 4 }}>渠道模型 ID *</div>
              <Input
                placeholder="gpt-image-2-vip"
                value={b.channel_model_id}
                onChange={(e) => updateBinding(idx, { channel_model_id: e.target.value })}
              />
            </Col>
            <Col span={4}>
              <div style={{ fontSize: 12, color: '#666', marginBottom: 4 }}>priority *</div>
              <InputNumber
                min={1}
                max={100}
                style={{ width: '100%' }}
                value={b.priority}
                onChange={(val) => updateBinding(idx, { priority: Number(val) || 10 })}
              />
            </Col>
            <Col span={4}>
              <div style={{ fontSize: 12, color: '#666', marginBottom: 4 }}>状态</div>
              <Select
                value={b.status || 'active'}
                onChange={(val) => updateBinding(idx, { status: val })}
                style={{ width: '100%' }}
              >
                <Option value="active">启用</Option>
                <Option value="inactive">禁用</Option>
              </Select>
            </Col>
          </Row>
          <Row gutter={12} style={{ marginTop: 8 }}>
            <Col span={8}>
              <Space>
                <span style={{ fontSize: 12, color: '#666' }}>参与降级</span>
                <Switch
                  checked={b.fallback !== false}
                  onChange={(checked) => updateBinding(idx, { fallback: checked })}
                  size="small"
                />
              </Space>
            </Col>
          </Row>

          <div style={{ marginTop: 12, padding: 10, background: '#fafafa', borderRadius: 6 }}>
            <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 8, color: '#444' }}>
              协议路由 mode_profiles
            </div>
            {modes.map((mode) => (
              <Row key={mode} gutter={8} align="middle" style={{ marginBottom: 6 }}>
                <Col span={6}>
                  <Tag>{INVOCATION_MODE_LABELS[mode] || mode}</Tag>
                  <code style={{ fontSize: 11, color: '#999' }}>{mode}</code>
                </Col>
                <Col span={18}>
                  <Select
                    showSearch
                    allowClear
                    placeholder="选择协议画像 profile_id"
                    style={{ width: '100%' }}
                    value={b.mode_profiles?.[mode]}
                    onChange={(val) => updateModeProfile(idx, mode, val || '')}
                    options={profilesForMode(mode)}
                    optionFilterProp="label"
                  />
                </Col>
              </Row>
            ))}
          </div>
        </Card>
      ))}
    </div>
  )
}
