import { useState, useEffect } from 'react'
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
} from '@ant-design/icons'
import {
  listTasksAdmin,
  getTaskStatsAdmin,
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
}

export default function TaskAdmin() {
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<TaskItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [filterCategory, setFilterCategory] = useState<string | undefined>()
  const [filterStatus, setFilterStatus] = useState<string | undefined>()
  const [viewItem, setViewItem] = useState<TaskItem | null>(null)
  const [stats, setStats] = useState<TaskStats | null>(null)

  const fetchData = async () => {
    setLoading(true)
    try {
      const res = await listTasksAdmin({
        page,
        page_size: pageSize,
        category: filterCategory,
        status: filterStatus,
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

  useEffect(() => {
    fetchData()
    fetchStats()
  }, [page, pageSize, filterCategory, filterStatus])

  const columns: ColumnsType<TaskItem> = [
    {
      title: '任务ID',
      dataIndex: 'id',
      key: 'id',
      width: 180,
      render: (v) => <code style={{ fontSize: 11 }}>{String(v).slice(0, 18)}...</code>,
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
      width: 80,
      fixed: 'right',
      render: (_, r) => (
        <Button size="small" icon={<EyeOutlined />} onClick={() => setViewItem(r)}>
          详情
        </Button>
      ),
    },
  ]

  const successRate = stats && stats.total > 0 ? Math.round((stats.success / stats.total) * 100) : 0
  const avgDurationSec = stats ? (stats.avg_duration_ms / 1000).toFixed(2) : '0'

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card>
            <Statistic title="总任务数" value={stats?.total || 0} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="成功任务"
              value={stats?.success || 0}
              valueStyle={{ color: '#3f8600' }}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="失败任务"
              value={stats?.failed || 0}
              valueStyle={{ color: '#cf1322' }}
              prefix={<CloseCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="处理中"
              value={stats?.processing || 0}
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
        width={760}
      >
        {viewItem && (
          <div>
            <Descriptions column={2} bordered size="small" style={{ marginBottom: 16 }}>
              <Descriptions.Item label="任务ID">{String(viewItem.id)}</Descriptions.Item>
              <Descriptions.Item label="模型">
                <Tag color="blue">{viewItem.model_code}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="分类">
                <Tag color={categoryMap[viewItem.category]?.color}>{categoryMap[viewItem.category]?.label}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={statusMap[viewItem.status]?.color}>{statusMap[viewItem.status]?.label}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="耗时">
                {viewItem.duration_ms ? `${(viewItem.duration_ms / 1000).toFixed(2)}s` : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="创建时间">
                {viewItem.created_at?.replace('T', ' ').slice(0, 19)}
              </Descriptions.Item>
            </Descriptions>

            <Divider style={{ margin: '12px 0' }}>请求参数</Divider>
            <Alert
              message={viewItem.params_summary || '-'}
              type="info"
              showIcon
              style={{ marginBottom: 12 }}
            />
            <div style={{ background: '#fafafa', padding: 12, borderRadius: 6, marginBottom: 12, maxHeight: 200, overflowY: 'auto' }}>
              <pre style={{ margin: 0, fontSize: 12 }}>{JSON.stringify(viewItem.params, null, 2)}</pre>
            </div>

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
