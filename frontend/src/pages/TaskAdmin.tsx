import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Select,
  message,
  Card,
  Row,
  Col,
  Empty,
  Descriptions,
  Statistic,
  Progress,
  Divider,
  Alert,
  Popconfirm,
  Input,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  ReloadOutlined,
  EyeOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  SyncOutlined,
  FileTextOutlined,
  PictureOutlined,
  VideoCameraOutlined,
  StopOutlined,
} from '@ant-design/icons'
import {
  listTasksAdmin,
  getTaskStatsAdmin,
  getTaskAdmin,
  cancelAllTasksAdmin,
  cancelTaskAdmin,
} from '@/api'
import type { TaskItem, TaskStats } from '@/types'

const { Option } = Select

const categoryMap: Record<string, { label: string; color: string; icon: React.ReactNode }> = {
  text: { label: '文本', color: 'blue', icon: <FileTextOutlined /> },
  image: { label: '图像', color: 'green', icon: <PictureOutlined /> },
  video: { label: '视频', color: 'purple', icon: <VideoCameraOutlined /> },
}

const statusMap: Record<string, { label: string; color: string; icon: React.ReactNode }> = {
  pending: { label: '等待中', color: 'default', icon: <ClockCircleOutlined /> },
  processing: { label: '处理中', color: 'blue', icon: <SyncOutlined spin /> },
  success: { label: '成功', color: 'green', icon: <CheckCircleOutlined /> },
  failed: { label: '失败', color: 'red', icon: <CloseCircleOutlined /> },
  queued: { label: '排队中', color: 'orange', icon: <ClockCircleOutlined /> },
}

export default function TaskAdmin() {
  const [searchParams] = useSearchParams()
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<TaskItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [filterCategory, setFilterCategory] = useState<string | undefined>()
  const [filterStatus, setFilterStatus] = useState<string | undefined>()
  const [filterModelCode, setFilterModelCode] = useState('')
  const [filterChannelCode, setFilterChannelCode] = useState('')
  const [searchTaskId, setSearchTaskId] = useState('')
  const [searchTraceId, setSearchTraceId] = useState('')
  const [timeRange, setTimeRange] = useState<string>('24h')
  const [viewItem, setViewItem] = useState<TaskItem | null>(null)
  const [stats, setStats] = useState<TaskStats | null>(null)
  const [sortBy, setSortBy] = useState('created_at')
  const [sortOrder, setSortOrder] = useState(-1)

  const fetchData = async () => {
    setLoading(true)
    try {
      const res = await listTasksAdmin({
        page,
        page_size: pageSize,
        category: filterCategory,
        status: filterStatus,
        model_code: filterModelCode.trim() || undefined,
        channel_code: filterChannelCode.trim() || undefined,
        task_id: searchTaskId.trim() || undefined,
        trace_id: searchTraceId.trim() || undefined,
        time_range: timeRange,
        sort_by: sortBy,
        sort_order: sortOrder,
      })
      setData(res.data || [])
      setTotal(res.total || 0)
    } catch (e: any) {
      message.error(e.message || '加载失败')
    } finally {
      setLoading(false)
    }
  }

  const fetchStats = async () => {
    try {
      const res = await getTaskStatsAdmin()
      setStats(res.data || null)
    } catch (e: any) {
      console.warn('统计加载失败', e)
    }
  }

  const handleCancelAll = async () => {
    try {
      const res = await cancelAllTasksAdmin()
      if (res.code === 'success' && res.data) {
        message.success(`已停止 ${res.data.modified_count} 个进行中的任务`)
        fetchData()
        fetchStats()
      } else {
        message.error(res.message || '操作失败')
      }
    } catch (e: any) {
      message.error(e.message || '操作失败')
    }
  }

  const handleCancelTask = async (task_id: string) => {
    try {
      const res = await cancelTaskAdmin(task_id)
      if (res.code === 'success') {
        message.success('任务已停止')
        fetchData()
        fetchStats()
      } else {
        message.error(res.message || '操作失败')
      }
    } catch (e: any) {
      message.error(e.message || '操作失败')
    }
  }

  const handleViewTask = async (r: TaskItem) => {
    setViewItem(r)
    try {
      const res = await getTaskAdmin(r.task_id)
      if (res.code === 'success' && res.data) {
        setViewItem(res.data)
      }
    } catch {
      /* 使用列表数据 */
    }
  }

  useEffect(() => {
    const qModel = searchParams.get('model_code')
    const qChannel = searchParams.get('channel_code')
    const qTask = searchParams.get('task_id')
    const qTrace = searchParams.get('trace_id')
    if (qModel) setFilterModelCode(qModel)
    if (qChannel) setFilterChannelCode(qChannel)
    if (qTask) setSearchTaskId(qTask)
    if (qTrace) setSearchTraceId(qTrace)
  }, [searchParams])

  useEffect(() => {
    fetchData()
    fetchStats()
  }, [page, pageSize, filterCategory, filterStatus, filterModelCode, filterChannelCode, searchTaskId, searchTraceId, timeRange, sortBy, sortOrder])

  const columns: ColumnsType<TaskItem> = [
    {
      title: '任务 ID',
      dataIndex: 'task_id',
      key: 'task_id',
      width: 200,
      ellipsis: true,
      render: (v) => (
        <code style={{ fontSize: 11 }} title={v}>{v || '-'}</code>
      ),
    },
    {
      title: 'Trace ID',
      dataIndex: 'trace_id',
      key: 'trace_id',
      width: 180,
      ellipsis: true,
      render: (v) =>
        v ? (
          <a href={`/admin/trace-logs?trace_id=${encodeURIComponent(v)}`} target="_blank" rel="noreferrer">
            <code style={{ fontSize: 11 }} title={v}>{v}</code>
          </a>
        ) : (
          '-'
        ),
    },
    {
      title: '模型',
      dataIndex: 'model_code',
      key: 'model_code',
      width: 140,
      render: (v) => <Tag color="blue">{v}</Tag>,
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      width: 90,
      render: (v) => {
        const c = categoryMap[v] || { label: v, color: 'default', icon: null }
        return (
          <Tag color={c.color}>
            {c.icon} {c.label}
          </Tag>
        )
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 110,
      render: (v) => {
        const s = statusMap[v] || { label: v, color: 'default', icon: null }
        return (
          <Tag color={s.color}>
            {s.icon} {s.label}
          </Tag>
        )
      },
    },
    {
      title: '参数摘要',
      dataIndex: 'params_summary',
      key: 'params_summary',
      ellipsis: true,
      render: (v) => <span style={{ color: '#666' }}>{v || '-'}</span>,
    },
    {
      title: '耗时',
      dataIndex: 'duration_ms',
      key: 'duration_ms',
      width: 100,
      render: (v) => v ? `${(v / 1000).toFixed(2)}s` : '-',
      sorter: (a, b) => (a.duration_ms || 0) - (b.duration_ms || 0),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 170,
      render: (v) => v?.replace('T', ' ').slice(0, 19),
    },
    {
      title: '操作',
      key: 'actions',
      width: 150,
      fixed: 'right',
      render: (_, r) => (
        <Space>
          <Button size="small" icon={<EyeOutlined />} onClick={() => handleViewTask(r)}>
            详情
          </Button>
          {(r.status === 'processing' || r.status === 'pending') && (
            <Popconfirm
              title="确定要停止此任务吗？"
              okText="确定"
              cancelText="取消"
              onConfirm={() => handleCancelTask(r.task_id)}
            >
              <Button size="small" danger icon={<StopOutlined />}>
                停止
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ]

  const successRate = stats ? Math.round(stats.success_rate || 0) : 0
  const avgDurationSec = stats ? (stats.avg_duration_ms / 1000).toFixed(2) : '0'

  return (
    <div style={{ padding: 24, height: '100%', overflowY: 'auto', boxSizing: 'border-box' }}>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card>
            <Statistic title="总任务数" value={stats?.total_tasks || 0} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="成功任务"
              value={stats?.success_count || 0}
              valueStyle={{ color: '#3f8600' }}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="失败任务"
              value={stats?.failed_count || 0}
              valueStyle={{ color: '#cf1322' }}
              prefix={<CloseCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="处理中"
              value={(stats?.processing_count || 0) + (stats?.pending_count || 0)}
              valueStyle={{ color: '#1890ff' }}
              prefix={<SyncOutlined spin />}
            />
            <div style={{ marginTop: 8 }}>
              <Progress percent={successRate} size="small" />
              <div style={{ fontSize: 12, color: '#888' }}>
                成功率 {successRate}% · 平均 {avgDurationSec}s
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      <Card
        title="任务列表"
        extra={
          <Space>
            <Select
              placeholder="时间范围"
              style={{ width: 120 }}
              value={timeRange}
              onChange={(v) => { setTimeRange(v); setPage(1) }}
            >
              <Option value="1h">最近1小时</Option>
              <Option value="6h">最近6小时</Option>
              <Option value="24h">最近24小时</Option>
              <Option value="7d">最近7天</Option>
              <Option value="30d">最近30天</Option>
              <Option value="all">全部时间</Option>
            </Select>
            <Input
              placeholder="任务 ID"
              allowClear
              style={{ width: 200 }}
              value={searchTaskId}
              onChange={(e) => { setSearchTaskId(e.target.value); setPage(1) }}
            />
            <Input
              placeholder="Trace ID"
              allowClear
              style={{ width: 200 }}
              value={searchTraceId}
              onChange={(e) => { setSearchTraceId(e.target.value); setPage(1) }}
            />
            <Input
              placeholder="模型编码"
              allowClear
              style={{ width: 130 }}
              value={filterModelCode}
              onChange={(e) => { setFilterModelCode(e.target.value); setPage(1) }}
            />
            <Input
              placeholder="渠道编码"
              allowClear
              style={{ width: 130 }}
              value={filterChannelCode}
              onChange={(e) => { setFilterChannelCode(e.target.value); setPage(1) }}
            />
            <Select
              placeholder="分类筛选"
              allowClear
              style={{ width: 120 }}
              value={filterCategory}
              onChange={(v) => { setFilterCategory(v); setPage(1) }}
            >
              <Option value="text">文本</Option>
              <Option value="image">图像</Option>
              <Option value="video">视频</Option>
            </Select>
            <Select
              placeholder="状态筛选"
              allowClear
              style={{ width: 120 }}
              value={filterStatus}
              onChange={(v) => { setFilterStatus(v); setPage(1) }}
            >
              <Option value="pending">等待中</Option>
              <Option value="processing">处理中</Option>
              <Option value="success">成功</Option>
              <Option value="failed">失败</Option>
            </Select>
            <Select
              placeholder="排序字段"
              style={{ width: 120 }}
              value={sortBy}
              onChange={(v) => { setSortBy(v || 'created_at'); setPage(1) }}
            >
              <Option value="created_at">创建时间</Option>
              <Option value="updated_at">更新时间</Option>
              <Option value="duration_ms">耗时</Option>
            </Select>
            <Button
              type={sortOrder === -1 ? 'primary' : 'default'}
              onClick={() => { setSortOrder(sortOrder === -1 ? 1 : -1); setPage(1) }}
            >
              {sortOrder === -1 ? '最新优先' : '最早优先'}
            </Button>
            <Popconfirm
              title="确定要停止全部进行中的任务吗？"
              description="所有等待中和处理中的任务将被标记为失败"
              okText="确定"
              cancelText="取消"
              onConfirm={handleCancelAll}
            >
              <Button danger icon={<StopOutlined />}>
                停止全部进行中
              </Button>
            </Popconfirm>
            <Button icon={<ReloadOutlined />} onClick={() => { fetchData(); fetchStats() }}>
              刷新
            </Button>
          </Space>
        }
      >
        <Table
          rowKey="id"
          loading={loading}
          dataSource={data}
          columns={columns}
          pagination={{
            current: page,
            pageSize,
            total,
            onChange: (p, ps) => { setPage(p); setPageSize(ps) },
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (t) => `共 ${t} 条`,
          }}
          scroll={{ x: 1200 }}
        />
      </Card>

      <Modal
        title="任务详情"
        open={!!viewItem}
        onCancel={() => setViewItem(null)}
        footer={[<Button key="close" onClick={() => setViewItem(null)}>关闭</Button>]}
        width={900}
      >
        {viewItem && (
          <div>
            <Descriptions column={2} bordered size="small" style={{ marginBottom: 16 }}>
              <Descriptions.Item label="任务 ID" span={2}>
                <code style={{ fontSize: 11 }}>{viewItem.task_id}</code>
              </Descriptions.Item>
              <Descriptions.Item label="模型">
                <Tag color="blue">{viewItem.model_code}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="分类">
                <Tag color={categoryMap[viewItem.category]?.color}>{categoryMap[viewItem.category]?.label}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={statusMap[viewItem.status]?.color}>{statusMap[viewItem.status]?.label}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="渠道">
                {viewItem.channel_code ? <Tag color="orange">{viewItem.channel_code}</Tag> : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="Trace ID">
                {viewItem.trace_id ? (
                  <a
                    href={`/admin/trace-logs?trace_id=${viewItem.trace_id}`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    <code style={{ fontSize: 11 }}>{viewItem.trace_id}</code>
                  </a>
                ) : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="耗时">
                {viewItem.duration_ms ? `${(viewItem.duration_ms / 1000).toFixed(2)}s` : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="创建时间">
                {viewItem.created_at?.replace('T', ' ').slice(0, 19)}
              </Descriptions.Item>
              <Descriptions.Item label="更新时间">
                {viewItem.updated_at?.replace('T', ' ').slice(0, 19) || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="会话ID">
                {viewItem.session_id || '-'}
              </Descriptions.Item>
            </Descriptions>

            <Divider style={{ margin: '12px 0' }}>前端请求参数</Divider>
            <Alert
              message={viewItem.params_summary || '-'}
              type="info"
              showIcon
              style={{ marginBottom: 12 }}
            />
            <div style={{ background: '#fafafa', padding: 12, borderRadius: 6, marginBottom: 12, maxHeight: 200, overflowY: 'auto' }}>
              <pre style={{ margin: 0, fontSize: 12 }}>{JSON.stringify(viewItem.params, null, 2)}</pre>
            </div>

            {/* 渠道请求：HTTP 实际请求 + 网关上下文（不重复展示） */}
            {!viewItem.channel_request && !viewItem.channel_response && (
              <Alert
                type="warning"
                showIcon
                style={{ marginBottom: 12 }}
                message="本任务未记录渠道入参/出参（可能是备用渠道成功时的历史数据，或走了 /execute 旧路径）"
                description={viewItem.trace_id ? `可在「链路日志」中按 Trace ID 查询：${viewItem.trace_id}` : undefined}
              />
            )}

            {viewItem.channel_request && (
              <>
                <Divider style={{ margin: '12px 0' }}>渠道请求</Divider>
                {(viewItem.channel_request as any).http_request ? (
                  <div style={{ background: '#f9f0ff', padding: 12, borderRadius: 6, marginBottom: 12, maxHeight: 280, overflowY: 'auto' }}>
                    <pre style={{ margin: 0, fontSize: 12 }}>
                      {JSON.stringify((viewItem.channel_request as any).http_request, null, 2)}
                    </pre>
                  </div>
                ) : null}
                {(() => {
                  const { http_request: _hr, ...meta } = viewItem.channel_request as Record<string, unknown>
                  if (Object.keys(meta).length === 0) return null
                  return (
                    <div style={{ background: '#fff7e6', padding: 12, borderRadius: 6, marginBottom: 12, maxHeight: 160, overflowY: 'auto' }}>
                      <div style={{ fontSize: 12, color: '#8c8c8c', marginBottom: 6 }}>网关上下文</div>
                      <pre style={{ margin: 0, fontSize: 12 }}>{JSON.stringify(meta, null, 2)}</pre>
                    </div>
                  )
                })()}
              </>
            )}

            {/* 渠道响应（视频类型包含创建和查询两次响应） */}
            {viewItem.channel_response && Object.keys(viewItem.channel_response).length > 0 && (
              <>
                <Divider style={{ margin: '12px 0' }}>渠道响应</Divider>
                {(viewItem.channel_response as any).primary_failed && (
                  <div style={{ marginBottom: 12 }}>
                    <div style={{ fontSize: 13, fontWeight: 500, color: '#fa8c16', marginBottom: 8 }}>
                      主渠道失败（已切换备用）
                    </div>
                    <div style={{ background: '#fff7e6', padding: 12, borderRadius: 6, maxHeight: 180, overflowY: 'auto' }}>
                      <pre style={{ margin: 0, fontSize: 12 }}>
                        {JSON.stringify((viewItem.channel_response as any).primary_failed, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
                {(viewItem.channel_response as any).error && (
                  <div style={{ marginBottom: 12 }}>
                    <Alert
                      type="error"
                      message={(viewItem.channel_response as any).error?.error_message || '渠道返回错误'}
                      description={(viewItem.channel_response as any).error?.error_code}
                    />
                  </div>
                )}
                {(viewItem.channel_response as any).raw && (
                  <div style={{ marginBottom: 12 }}>
                    <div style={{ fontSize: 13, fontWeight: 500, color: '#722ed1', marginBottom: 8 }}>
                      渠道原始响应
                    </div>
                    <div style={{ background: '#f9f0ff', padding: 12, borderRadius: 6, maxHeight: 220, overflowY: 'auto' }}>
                      <pre style={{ margin: 0, fontSize: 12 }}>
                        {JSON.stringify((viewItem.channel_response as any).raw, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
                {viewItem.category === 'video' && viewItem.channel_response.create && (
                  <div style={{ marginBottom: 12 }}>
                    <div style={{ fontSize: 13, fontWeight: 500, color: '#1890ff', marginBottom: 8 }}>
                      ① 创建任务响应
                    </div>
                    <div style={{ background: '#e6f7ff', padding: 12, borderRadius: 6, maxHeight: 150, overflowY: 'auto' }}>
                      <pre style={{ margin: 0, fontSize: 12 }}>{JSON.stringify(viewItem.channel_response.create, null, 2)}</pre>
                    </div>
                  </div>
                )}
                {viewItem.channel_response.query && (
                  <div style={{ marginBottom: 12 }}>
                    <div style={{ fontSize: 13, fontWeight: 500, color: '#52c41a', marginBottom: 8 }}>
                      {viewItem.category === 'video' ? '② 查询任务响应' : '响应结果'}
                    </div>
                    <div style={{ background: '#f6ffed', padding: 12, borderRadius: 6, maxHeight: 200, overflowY: 'auto' }}>
                      <pre style={{ margin: 0, fontSize: 12 }}>{JSON.stringify(viewItem.channel_response.query, null, 2)}</pre>
                    </div>
                  </div>
                )}
              </>
            )}

            {viewItem.error_message && (
              <>
                <Divider style={{ margin: '12px 0' }}>错误信息</Divider>
                <Alert
                  message={viewItem.error_message}
                  type="error"
                  showIcon
                />
              </>
            )}

            {viewItem.result && (
              <>
                <Divider style={{ margin: '12px 0' }}>返回结果</Divider>
                <div style={{ background: '#f6ffed', padding: 12, borderRadius: 6, maxHeight: 300, overflowY: 'auto' }}>
                  {viewItem.result.text && (
                    <div style={{ marginBottom: 8 }}>
                      <strong>文本:</strong>
                      <div style={{ whiteSpace: 'pre-wrap', marginTop: 4 }}>{viewItem.result.text}</div>
                    </div>
                  )}
                  {viewItem.result.images && viewItem.result.images.length > 0 && (
                    <Row gutter={[8, 8]} style={{ marginTop: 8 }}>
                      {viewItem.result.images.map((img: any, i: number) => (
                        <Col key={i} span={12}>
                          {img.url?.startsWith('http') ? (
                            <img
                              src={img.url}
                              alt={`result-${i}`}
                              style={{ width: '100%', borderRadius: 4, border: '1px solid #ddd' }}
                            />
                          ) : (
                            <div style={{ background: '#f0f0f0', padding: 12, borderRadius: 4, fontSize: 12 }}>
                              {img.url || img.revised_prompt || '图像数据'}
                            </div>
                          )}
                        </Col>
                      ))}
                    </Row>
                  )}
                  {viewItem.result.videos && viewItem.result.videos.length > 0 && (
                    <Row gutter={[8, 8]} style={{ marginTop: 8 }}>
                      {viewItem.result.videos.map((vid: any, i: number) => (
                        <Col key={i} span={24}>
                          {vid.url?.startsWith('http') ? (
                            <video
                              src={vid.url}
                              controls
                              style={{ width: '100%', borderRadius: 4 }}
                            />
                          ) : (
                            <div style={{ background: '#f0f0f0', padding: 12, borderRadius: 4, fontSize: 12 }}>
                              {vid.url || vid.revised_prompt || '视频数据'}
                            </div>
                          )}
                        </Col>
                      ))}
                    </Row>
                  )}
                  {!viewItem.result.text && !viewItem.result.images && !viewItem.result.videos && (
                    <pre style={{ margin: 0, fontSize: 12 }}>{JSON.stringify(viewItem.result, null, 2)}</pre>
                  )}
                </div>
              </>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}
