import { useState, useEffect, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  Table,
  Button,
  Space,
  Tag,
  Select,
  message,
  Card,
  Timeline,
  Input,
  Descriptions,
  Empty,
  Typography,
  Collapse,
  Tooltip,
  Spin,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  ReloadOutlined,
  EyeOutlined,
  SearchOutlined,
  CloseOutlined,
} from '@ant-design/icons'
import { listTraceLogsAdmin, getTraceLogAdmin } from '@/api'
import type { TraceLogItem, TraceLogChannelAttempt } from '@/types'
import { formatServerDateTime } from '@/utils/formatDateTime'

const { Option } = Select
const { Text, Paragraph } = Typography

const stepLabelMap: Record<string, string> = {
  frontend_request: '前端入参',
  param_normalize: '参数规范化',
  channel_bindings: '渠道绑定列表',
  channel_select: '选中渠道',
  channel_fallback: '备用渠道',
  channel_invoke_prepare: '渠道调用准备',
  channel_http_request: '渠道 HTTP 请求',
  channel_http_response: '渠道 HTTP 响应',
  parse_result: '解析结果',
  task_failed: '任务失败',
  channel_fallback_error: '备用渠道异常',
  channel_fallback_skipped: '跳过渠道降级',
  channel_debug_request: '渠道调试入参',
  channel_debug_response: '渠道调试响应',
}

const statusColor: Record<string, string> = {
  success: 'green',
  failed: 'red',
  processing: 'blue',
}

function JsonBlock({ data, maxHeight = 240 }: { data: unknown; maxHeight?: number }) {
  return (
    <pre
      style={{
        margin: 0,
        fontSize: 11,
        lineHeight: 1.5,
        background: '#fafafa',
        padding: 10,
        borderRadius: 6,
        maxHeight,
        overflow: 'auto',
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-all',
      }}
    >
      {JSON.stringify(data, null, 2)}
    </pre>
  )
}

function TraceLogDetail({
  item,
  loading,
  onClose,
}: {
  item: TraceLogItem | null
  loading: boolean
  onClose: () => void
}) {
  if (!item && !loading) {
    return (
      <div
        style={{
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#999',
          padding: 24,
        }}
      >
        <Empty description="点击左侧列表行查看链路详情" />
      </div>
    )
  }

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div
        style={{
          padding: '12px 16px',
          borderBottom: '1px solid #f0f0f0',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexShrink: 0,
          background: '#fff',
        }}
      >
        <Text strong>链路详情</Text>
        <Button type="text" size="small" icon={<CloseOutlined />} onClick={onClose} />
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: 16, background: '#fafafa' }}>
        <Spin spinning={loading}>
          {item && (
            <>
              <Card size="small" style={{ marginBottom: 12 }}>
                <Descriptions size="small" column={1} bordered>
                  <Descriptions.Item label="Log ID">
                    <Text copyable={{ text: item.trace_id }} style={{ fontSize: 11 }}>
                      {item.trace_id}
                    </Text>
                  </Descriptions.Item>
                  <Descriptions.Item label="任务 ID">
                    {item.task_id ? (
                      <a href={`/admin/tasks?task_id=${encodeURIComponent(item.task_id)}`} target="_blank" rel="noreferrer">
                        <Text copyable={{ text: item.task_id }} style={{ fontSize: 11 }}>
                          {item.task_id}
                        </Text>
                      </a>
                    ) : (
                      '-'
                    )}
                  </Descriptions.Item>
                  <Descriptions.Item label="模型">{item.model_code || '-'}</Descriptions.Item>
                  <Descriptions.Item label="分类">{item.category || '-'}</Descriptions.Item>
                  <Descriptions.Item label="渠道">{item.channel_code || '-'}</Descriptions.Item>
                  <Descriptions.Item label="状态">
                    <Tag color={statusColor[item.status] || 'default'}>{item.status}</Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label="耗时">
                    {item.duration_ms != null ? `${(item.duration_ms / 1000).toFixed(2)}s` : '-'}
                  </Descriptions.Item>
                  <Descriptions.Item label="创建时间">
                    {formatServerDateTime(item.created_at)}
                  </Descriptions.Item>
                  {item.error_message && (
                    <Descriptions.Item label="错误">
                      <Text type="danger">{item.error_message}</Text>
                    </Descriptions.Item>
                  )}
                </Descriptions>
              </Card>

              {item.channel_attempts && item.channel_attempts.length > 0 && (
                <Card size="small" title="渠道调用记录" style={{ marginBottom: 12 }}>
                  <Collapse
                    size="small"
                    items={item.channel_attempts.map((att: TraceLogChannelAttempt, i: number) => ({
                      key: String(i),
                      label: (
                        <Space>
                          <Tag color={att.success ? 'green' : 'red'}>
                            {att.success ? '成功' : '失败'}
                          </Tag>
                          <Text>{att.channel_code}</Text>
                          {att.endpoint_type && (
                            <Text type="secondary" style={{ fontSize: 11 }}>
                              {att.endpoint_type}
                            </Text>
                          )}
                        </Space>
                      ),
                      children: (
                        <div>
                          {att.error_message && (
                            <Paragraph type="danger" style={{ fontSize: 12, marginBottom: 8 }}>
                              {att.error_message}
                            </Paragraph>
                          )}
                          <div style={{ fontSize: 12, color: '#666', marginBottom: 4 }}>请求</div>
                          <JsonBlock data={att.request} maxHeight={180} />
                          <div style={{ fontSize: 12, color: '#666', margin: '10px 0 4px' }}>响应</div>
                          <JsonBlock data={att.response} maxHeight={180} />
                        </div>
                      ),
                    }))}
                  />
                </Card>
              )}

              <Card size="small" title={`关键步骤 (${item.steps?.length || 0})`}>
                {item.steps && item.steps.length > 0 ? (
                  <Timeline
                    items={item.steps.map((s) => ({
                      color: s.level === 'error' ? 'red' : 'blue',
                      children: (
                        <div style={{ paddingBottom: 4 }}>
                          <div style={{ fontWeight: 500, fontSize: 13 }}>
                            {stepLabelMap[s.step] || s.step}
                            <Text type="secondary" style={{ fontSize: 11, marginLeft: 8 }}>
                              {formatServerDateTime(s.timestamp)}
                            </Text>
                          </div>
                          {s.data && Object.keys(s.data).length > 0 && (
                            <div style={{ marginTop: 6 }}>
                              <JsonBlock data={s.data} maxHeight={160} />
                            </div>
                          )}
                        </div>
                      ),
                    }))}
                  />
                ) : (
                  <Empty description="暂无步骤" image={Empty.PRESENTED_IMAGE_SIMPLE} />
                )}
              </Card>
            </>
          )}
        </Spin>
      </div>
    </div>
  )
}

export default function TraceLogAdmin() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [loading, setLoading] = useState(false)
  const [detailLoading, setDetailLoading] = useState(false)
  const [data, setData] = useState<TraceLogItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [timeRange, setTimeRange] = useState('24h')
  const [filterStatus, setFilterStatus] = useState<string | undefined>()
  const [filterCategory, setFilterCategory] = useState<string | undefined>()
  const [searchTraceId, setSearchTraceId] = useState('')
  const [searchTaskId, setSearchTaskId] = useState('')
  const [filterModelCode, setFilterModelCode] = useState('')
  const [filterChannelCode, setFilterChannelCode] = useState('')
  const [viewItem, setViewItem] = useState<TraceLogItem | null>(null)
  const [selectedTraceId, setSelectedTraceId] = useState<string | null>(null)

  const loadDetail = useCallback(async (traceId: string) => {
    setSelectedTraceId(traceId)
    setDetailLoading(true)
    try {
      const res = await getTraceLogAdmin(traceId)
      if (res.code === 'success' && res.data) {
        setViewItem(res.data)
      }
    } catch (e: any) {
      message.error(e.message || '加载详情失败')
    } finally {
      setDetailLoading(false)
    }
  }, [])

  const fetchData = async () => {
    setLoading(true)
    try {
      const res = await listTraceLogsAdmin({
        page,
        page_size: pageSize,
        time_range: timeRange,
        status: filterStatus,
        category: filterCategory,
        trace_id: searchTraceId.trim() || undefined,
        task_id: searchTaskId.trim() || undefined,
        model_code: filterModelCode.trim() || undefined,
        channel_code: filterChannelCode.trim() || undefined,
      })
      setData(res.data || [])
      setTotal(res.total || 0)
    } catch (e: any) {
      message.error(e.message || '加载失败')
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = () => {
    setPage(1)
    fetchData()
  }

  const handleView = (row: TraceLogItem) => {
    loadDetail(row.trace_id)
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev)
      next.set('trace_id', row.trace_id)
      return next
    })
  }

  const handleCloseDetail = () => {
    setViewItem(null)
    setSelectedTraceId(null)
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev)
      next.delete('trace_id')
      return next
    })
  }

  useEffect(() => {
    const qTrace = searchParams.get('trace_id')
    const qTask = searchParams.get('task_id')
    const qModel = searchParams.get('model_code')
    const qChannel = searchParams.get('channel_code')
    if (qTrace) {
      setSearchTraceId(qTrace)
      loadDetail(qTrace)
    }
    if (qTask) setSearchTaskId(qTask)
    if (qModel) setFilterModelCode(qModel)
    if (qChannel) setFilterChannelCode(qChannel)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    fetchData()
  }, [page, pageSize, timeRange, filterStatus, filterCategory, filterModelCode, filterChannelCode, searchTraceId, searchTaskId])

  const columns: ColumnsType<TraceLogItem> = [
    {
      title: 'Log ID',
      dataIndex: 'trace_id',
      key: 'trace_id',
      width: 160,
      ellipsis: true,
      render: (v) => (
        <Tooltip title={v}>
          <code style={{ fontSize: 11 }}>{v}</code>
        </Tooltip>
      ),
    },
    {
      title: '任务 ID',
      dataIndex: 'task_id',
      key: 'task_id',
      width: 140,
      ellipsis: true,
      render: (v) =>
        v ? (
          <Tooltip title={v}>
            <a href={`/admin/tasks?task_id=${encodeURIComponent(v)}`} target="_blank" rel="noreferrer">
              <code style={{ fontSize: 11 }}>{v}</code>
            </a>
          </Tooltip>
        ) : (
          '-'
        ),
    },
    {
      title: '模型',
      dataIndex: 'model_code',
      key: 'model_code',
      width: 110,
      ellipsis: true,
      render: (v) => (v ? <Tag style={{ margin: 0 }}>{v}</Tag> : '-'),
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      width: 72,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 88,
      render: (v) => <Tag color={statusColor[v] || 'default'}>{v}</Tag>,
    },
    {
      title: '渠道',
      dataIndex: 'channel_code',
      key: 'channel_code',
      width: 120,
      ellipsis: true,
      render: (v) => v || '-',
    },
    {
      title: '步骤',
      dataIndex: 'step_count',
      key: 'step_count',
      width: 64,
      align: 'center',
    },
    {
      title: '耗时',
      dataIndex: 'duration_ms',
      key: 'duration_ms',
      width: 72,
      render: (v) => (v != null ? `${(v / 1000).toFixed(1)}s` : '-'),
    },
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (v) => formatServerDateTime(v),
    },
    {
      title: '操作',
      key: 'action',
      width: 72,
      fixed: 'right',
      render: (_, r) => (
        <Button
          type="link"
          size="small"
          icon={<EyeOutlined />}
          onClick={(e) => {
            e.stopPropagation()
            handleView(r)
          }}
        >
          详情
        </Button>
      ),
    },
  ]

  return (
    <div
      style={{
        height: '100%',
        boxSizing: 'border-box',
        padding: 16,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      <Card
        size="small"
        style={{ marginBottom: 12, flexShrink: 0 }}
        styles={{ body: { padding: '12px 16px' } }}
      >
        <Space wrap>
          <Input
            placeholder="Log ID / trace_id"
            prefix={<SearchOutlined />}
            value={searchTraceId}
            onChange={(e) => setSearchTraceId(e.target.value)}
            onPressEnter={handleSearch}
            style={{ width: 220 }}
            allowClear
          />
          <Input
            placeholder="任务 ID"
            value={searchTaskId}
            onChange={(e) => setSearchTaskId(e.target.value)}
            onPressEnter={handleSearch}
            style={{ width: 220 }}
            allowClear
          />
          <Input
            placeholder="模型编码"
            value={filterModelCode}
            onChange={(e) => setFilterModelCode(e.target.value)}
            onPressEnter={handleSearch}
            style={{ width: 140 }}
            allowClear
          />
          <Input
            placeholder="渠道编码"
            value={filterChannelCode}
            onChange={(e) => setFilterChannelCode(e.target.value)}
            onPressEnter={handleSearch}
            style={{ width: 140 }}
            allowClear
          />
          <Button type="primary" onClick={handleSearch}>
            查询
          </Button>
          <Select value={timeRange} onChange={setTimeRange} style={{ width: 110 }}>
            <Option value="1h">1小时</Option>
            <Option value="6h">6小时</Option>
            <Option value="24h">24小时</Option>
            <Option value="7d">7天</Option>
            <Option value="30d">30天</Option>
            <Option value="all">全部</Option>
          </Select>
          <Select
            placeholder="状态"
            allowClear
            value={filterStatus}
            onChange={setFilterStatus}
            style={{ width: 100 }}
          >
            <Option value="success">success</Option>
            <Option value="failed">failed</Option>
            <Option value="processing">processing</Option>
          </Select>
          <Select
            placeholder="分类"
            allowClear
            value={filterCategory}
            onChange={setFilterCategory}
            style={{ width: 90 }}
          >
            <Option value="image">image</Option>
            <Option value="video">video</Option>
            <Option value="text">text</Option>
          </Select>
          <Button icon={<ReloadOutlined />} onClick={fetchData}>
            刷新
          </Button>
        </Space>
      </Card>

      <div
        style={{
          flex: 1,
          minHeight: 0,
          display: 'flex',
          gap: 12,
          overflow: 'hidden',
        }}
      >
        <Card
          title="链路日志列表"
          size="small"
          style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column' }}
          styles={{ body: { flex: 1, minHeight: 0, padding: 0, overflow: 'hidden' } }}
        >
          <Table
            rowKey="trace_id"
            loading={loading}
            columns={columns}
            dataSource={data}
            size="small"
            scroll={{ x: 1100, y: 'calc(100vh - 280px)' }}
            pagination={{
              current: page,
              pageSize,
              total,
              showSizeChanger: true,
              showTotal: (t) => `共 ${t} 条`,
              size: 'small',
              onChange: (p, ps) => {
                setPage(p)
                setPageSize(ps)
              },
            }}
            onRow={(record) => ({
              onClick: () => handleView(record),
              style: {
                cursor: 'pointer',
                background: selectedTraceId === record.trace_id ? '#e6f4ff' : undefined,
              },
            })}
          />
        </Card>

        <Card
          size="small"
          style={{
            width: 440,
            flexShrink: 0,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
          }}
          styles={{ body: { flex: 1, minHeight: 0, padding: 0, overflow: 'hidden' } }}
        >
          <TraceLogDetail item={viewItem} loading={detailLoading} onClose={handleCloseDetail} />
        </Card>
      </div>
    </div>
  )
}
