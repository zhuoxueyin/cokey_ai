import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Alert,
  Card,
  Table,
  Tag,
  Space,
  Button,
  Select,
  Modal,
  Descriptions,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { ReloadOutlined, EyeOutlined } from '@ant-design/icons'
import { listProtocolProfilesAdmin } from '@/api'
import type { ProtocolProfileItem } from '@/types'
import { INVOCATION_MODE_LABELS } from '@/constants/protocol'

export default function ProtocolProfileAdmin() {
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<ProtocolProfileItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(50)
  const [provider, setProvider] = useState<string | undefined>()
  const [mode, setMode] = useState<string | undefined>()
  const [viewItem, setViewItem] = useState<ProtocolProfileItem | null>(null)

  const fetchData = async () => {
    setLoading(true)
    try {
      const res = await listProtocolProfilesAdmin({
        page,
        page_size: pageSize,
        provider,
        invocation_mode: mode,
      })
      setData((res.data as ProtocolProfileItem[]) || [])
      setTotal(res.total || 0)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [page, pageSize, provider, mode])

  const columns: ColumnsType<ProtocolProfileItem> = [
    {
      title: 'profile_id',
      dataIndex: 'profile_id',
      key: 'profile_id',
      width: 280,
      render: (v) => <code style={{ fontSize: 11 }}>{v}</code>,
    },
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      width: 160,
      ellipsis: true,
    },
    {
      title: '任务模式',
      dataIndex: 'invocation_mode',
      key: 'invocation_mode',
      width: 120,
      render: (v) => (
        <Tag>{INVOCATION_MODE_LABELS[v] || v}</Tag>
      ),
    },
    {
      title: '协议槽位',
      dataIndex: 'protocol_slot',
      key: 'protocol_slot',
      width: 200,
      render: (v) => <code style={{ fontSize: 11 }}>{v}</code>,
    },
    {
      title: 'endpoint_type',
      dataIndex: 'endpoint_type',
      key: 'endpoint_type',
      width: 100,
    },
    {
      title: 'provider',
      dataIndex: 'provider',
      key: 'provider',
      width: 90,
      render: (v) => v || '*',
    },
    {
      title: '来源',
      key: 'source',
      width: 80,
      render: (_, r) => (
        r.is_builtin ? <Tag color="blue">内置</Tag> : <Tag>自定义</Tag>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 80,
      render: (_, r) => (
        <Button size="small" icon={<EyeOutlined />} onClick={() => setViewItem(r)} />
      ),
    },
  ]

  return (
    <div style={{ padding: 24, height: '100%', overflow: 'auto' }}>
      <Alert
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
        message="协议画像 = 路由契约层"
        description={
          <span>
            定义任务模式如何构参、解析响应（builder/parser）。模型绑定通过 <code>mode_profiles</code> 引用；
            日常查看在此页，新建复杂协议请走 <Link to="/admin/onboarding">接入工单</Link>。
          </span>
        }
      />
      <Card
        title="协议画像库"
        extra={
          <Space>
            <Select
              allowClear
              placeholder="provider"
              style={{ width: 120 }}
              value={provider}
              onChange={(v) => { setProvider(v); setPage(1) }}
              options={[
                { value: 'apiyi', label: 'apiyi' },
                { value: 'weelinking', label: 'weelinking' },
                { value: 'volcengine', label: 'volcengine' },
              ]}
            />
            <Select
              allowClear
              placeholder="任务模式"
              style={{ width: 140 }}
              value={mode}
              onChange={(v) => { setMode(v); setPage(1) }}
              options={Object.entries(INVOCATION_MODE_LABELS).map(([value, label]) => ({
                value,
                label,
              }))}
            />
            <Button icon={<ReloadOutlined />} onClick={fetchData} />
          </Space>
        }
      >
        <Table
          rowKey="profile_id"
          loading={loading}
          dataSource={data}
          columns={columns}
          size="small"
          pagination={{
            current: page,
            pageSize,
            total,
            onChange: (p, ps) => { setPage(p); setPageSize(ps) },
            showSizeChanger: true,
            showTotal: (t) => `共 ${t} 条`,
          }}
          scroll={{ x: 1100 }}
        />
      </Card>

      <Modal
        title={viewItem?.profile_id}
        open={!!viewItem}
        onCancel={() => setViewItem(null)}
        footer={null}
        width={640}
      >
        {viewItem && (
          <Descriptions column={1} size="small" bordered>
            <Descriptions.Item label="名称">{viewItem.name}</Descriptions.Item>
            <Descriptions.Item label="任务模式">{viewItem.invocation_mode}</Descriptions.Item>
            <Descriptions.Item label="协议槽位">{viewItem.protocol_slot}</Descriptions.Item>
            <Descriptions.Item label="endpoint_type">{viewItem.endpoint_type}</Descriptions.Item>
            <Descriptions.Item label="HTTP 路径">{viewItem.http?.path}</Descriptions.Item>
            <Descriptions.Item label="builder">{viewItem.request?.builder || '—'}</Descriptions.Item>
            <Descriptions.Item label="parser">{viewItem.response?.parser || '—'}</Descriptions.Item>
            <Descriptions.Item label="size_strategy">{viewItem.request?.size_strategy || '—'}</Descriptions.Item>
            <Descriptions.Item label="说明">{viewItem.description || '—'}</Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  )
}
