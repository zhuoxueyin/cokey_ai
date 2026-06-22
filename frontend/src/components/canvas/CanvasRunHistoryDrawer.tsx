import { useCallback, useEffect, useState, type ReactNode } from 'react'
import { Button, Drawer, Empty, List, Modal, Space, Spin, Tag, Typography, message } from 'antd'
import {
  FileTextOutlined,
  PictureOutlined,
  VideoCameraOutlined,
  AimOutlined,
  LinkOutlined,
  CopyOutlined,
  RobotOutlined,
} from '@ant-design/icons'
import { getCanvasRunDetail, listCanvasRuns } from '@/api/canvas'
import type { CanvasRunDetail, CanvasRunRecord } from '@/types/canvas'
import NodeResultView from './NodeResultView'
import { formatServerDateTime } from '@/utils/formatDateTime'

const { Text, Paragraph, Link } = Typography

async function copyToClipboard(text: string) {
  try {
    await navigator.clipboard.writeText(text)
    message.success('已复制')
  } catch {
    message.error('复制失败')
  }
}

const STATUS_MAP: Record<string, { color: string; label: string }> = {
  success: { color: 'success', label: '成功' },
  failed: { color: 'error', label: '失败' },
  processing: { color: 'processing', label: '进行中' },
  pending: { color: 'default', label: '等待' },
}

const NODE_TYPE_ICON: Record<string, ReactNode> = {
  text: <FileTextOutlined />,
  image: <PictureOutlined />,
  video: <VideoCameraOutlined />,
  agent_chat: <RobotOutlined />,
}

const CATEGORY_LABEL: Record<string, string> = {
  text: '文本',
  image: '图片',
  video: '视频',
  agent_chat: '创作助手',
}

interface IdField {
  label: string
  value?: string
  href?: string
}

function RunIdLine({ label, value, href, compact }: IdField & { compact?: boolean }) {
  if (!value) return null
  return (
    <div className={`canvas-run-id-line${compact ? ' canvas-run-id-line--compact' : ''}`}>
      <span className="canvas-run-id-line__label">{label}</span>
      <code className="canvas-run-id-line__value" title={value}>
        {value}
      </code>
      <Button
        type="text"
        size="small"
        className="canvas-run-id-line__copy"
        icon={<CopyOutlined />}
        aria-label={`复制${label}`}
        onClick={(e) => {
          e.stopPropagation()
          void copyToClipboard(value)
        }}
      />
      {href ? (
        <Link href={href} target="_blank" rel="noopener noreferrer" className="canvas-run-id-line__link">
          <LinkOutlined />
        </Link>
      ) : null}
    </div>
  )
}

function RunIdsBlock({ fields, compact }: { fields: IdField[]; compact?: boolean }) {
  const visible = fields.filter((f) => f.value)
  if (visible.length === 0) return null
  return (
    <div className={`canvas-run-ids${compact ? ' canvas-run-ids--compact' : ''}`}>
      {visible.map((f) => (
        <RunIdLine key={f.label} {...f} compact={compact} />
      ))}
    </div>
  )
}

function buildRunIdFields(
  record: Pick<
    CanvasRunRecord,
    | 'node_id'
    | 'task_id'
    | 'trace_id'
    | 'project_id'
    | 'canvas_project_id'
    | 'channel_code'
    | 'external_task_id'
  >,
  withLinks = false,
): IdField[] {
  return [
    { label: '节点 ID', value: record.node_id },
    { label: '任务 ID', value: record.task_id, href: withLinks ? `/admin/tasks?task_id=${record.task_id}` : undefined },
    { label: '日志 ID', value: record.trace_id, href: withLinks && record.trace_id ? `/admin/trace-logs?trace_id=${record.trace_id}` : undefined },
    { label: '项目 ID', value: record.canvas_project_id || record.project_id },
    { label: '渠道', value: record.channel_code },
    { label: '外部任务', value: record.external_task_id },
  ]
}

interface CanvasRunHistoryDrawerProps {
  open: boolean
  onClose: () => void
  projectId: string
  refreshKey?: number
  onFocusNode?: (nodeId: string) => void
}

export default function CanvasRunHistoryDrawer({
  open,
  onClose,
  projectId,
  refreshKey = 0,
  onFocusNode,
}: CanvasRunHistoryDrawerProps) {
  const [loading, setLoading] = useState(false)
  const [runs, setRuns] = useState<CanvasRunRecord[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [detailOpen, setDetailOpen] = useState(false)
  const [detailLoading, setDetailLoading] = useState(false)
  const [detail, setDetail] = useState<CanvasRunDetail | null>(null)

  const loadRuns = useCallback(
    async (p = 1) => {
      setLoading(true)
      try {
        const res = await listCanvasRuns(projectId, { page: p, page_size: 30 })
        if (res.code === 'success') {
          setRuns(Array.isArray(res.data) ? res.data : [])
          setTotal(res.total ?? 0)
          setPage(p)
        }
      } catch {
        message.error('加载运行记录失败')
      } finally {
        setLoading(false)
      }
    },
    [projectId],
  )

  useEffect(() => {
    if (open) loadRuns(1)
  }, [open, refreshKey, loadRuns])

  const openDetail = async (record: CanvasRunRecord) => {
    setDetailOpen(true)
    setDetailLoading(true)
    setDetail(null)
    try {
      const res = await getCanvasRunDetail(projectId, record.task_id)
      if (res.code === 'success' && res.data) {
        setDetail(res.data)
      } else {
        message.error(res.message || '加载详情失败')
        setDetailOpen(false)
      }
    } catch {
      message.error('加载详情失败')
      setDetailOpen(false)
    } finally {
      setDetailLoading(false)
    }
  }

  const formatDuration = (ms?: number) => {
    if (!ms || ms <= 0) return '—'
    if (ms < 1000) return `${ms}ms`
    return `${(ms / 1000).toFixed(1)}s`
  }

  return (
    <>
      <Drawer
        title="运行记录"
        placement="right"
        width={440}
        zIndex={1400}
        open={open}
        onClose={onClose}
        className="canvas-run-history-drawer"
        styles={{
          body: { padding: '12px 16px', overflow: 'auto' },
          header: { flexShrink: 0 },
        }}
        extra={<Text type="secondary">共 {total} 条</Text>}
      >
        {loading && runs.length === 0 ? (
          <div className="canvas-run-history-drawer__loading">
            <Spin />
          </div>
        ) : runs.length === 0 ? (
          <Empty description="暂无运行记录" />
        ) : (
          <List
            className="canvas-run-history-list"
            dataSource={runs}
            pagination={
              total > 30
                ? {
                    current: page,
                    total,
                    pageSize: 30,
                    size: 'small',
                    onChange: (p) => loadRuns(p),
                  }
                : false
            }
            renderItem={(item) => {
              const st = STATUS_MAP[item.status] || { color: 'default', label: item.status }
              return (
                <List.Item
                  className="canvas-run-history-list__item"
                  onClick={() => {
                    if (window.getSelection()?.toString()) return
                    openDetail(item)
                  }}
                >
                  <div className="canvas-run-history-list__main">
                    <div className="canvas-run-history-list__title">
                      {NODE_TYPE_ICON[item.node_type || item.canvas_node_type || item.category || ''] || <PictureOutlined />}
                      <span>{item.node_title || '未命名节点'}</span>
                      <Tag color={st.color} style={{ marginLeft: 'auto' }}>
                        {st.label}
                      </Tag>
                    </div>
                    <div className="canvas-run-history-list__meta">
                      <span>{CATEGORY_LABEL[item.node_type || item.canvas_node_type || item.category || ''] || item.category}</span>
                      <span>{item.model_code}</span>
                      <span>{formatDuration(item.duration_ms)}</span>
                    </div>
                    <RunIdsBlock
                      compact
                      fields={buildRunIdFields(item).filter((f) =>
                        ['节点 ID', '任务 ID', '日志 ID'].includes(f.label),
                      )}
                    />
                    {item.params_summary && (
                      <Paragraph className="canvas-run-history-list__prompt canvas-run-selectable">
                        {item.params_summary}
                      </Paragraph>
                    )}
                    <Text type="secondary" className="canvas-run-history-list__time">
                      {formatServerDateTime(item.created_at)}
                    </Text>
                  </div>
                </List.Item>
              )
            }}
          />
        )}
      </Drawer>

      <Modal
        title={detail ? `运行结果 · ${detail.node_title}` : '运行结果'}
        open={detailOpen}
        onCancel={() => setDetailOpen(false)}
        footer={
          detail?.node_id && onFocusNode
            ? [
                <Button key="close" onClick={() => setDetailOpen(false)}>
                  关闭
                </Button>,
                <Button
                  key="focus"
                  type="primary"
                  icon={<AimOutlined />}
                  onClick={() => {
                    if (detail?.node_id) {
                      onFocusNode(detail.node_id)
                      setDetailOpen(false)
                      onClose()
                    }
                  }}
                >
                  定位节点
                </Button>,
              ]
            : [
                <Button key="close" type="primary" onClick={() => setDetailOpen(false)}>
                  关闭
                </Button>,
              ]
        }
        width={720}
        zIndex={1450}
        destroyOnClose
        className="canvas-run-detail-modal"
      >
        {detailLoading ? (
          <div className="canvas-run-history-drawer__loading">
            <Spin tip="加载中…" />
          </div>
        ) : detail ? (
          <div className="canvas-run-detail">
            <div className="canvas-run-detail__meta">
              <Tag color={(STATUS_MAP[detail.status] || STATUS_MAP.failed).color}>
                {(STATUS_MAP[detail.status] || STATUS_MAP.failed).label}
              </Tag>
              <Text type="secondary">{detail.model_code}</Text>
              <Text type="secondary">{formatServerDateTime(detail.created_at)}</Text>
              {detail.duration_ms ? (
                <Text type="secondary">耗时 {formatDuration(detail.duration_ms)}</Text>
              ) : null}
            </div>
            <div className="canvas-run-detail__ids-panel">
              <Text type="secondary" className="canvas-run-detail__ids-title">
                定位信息
              </Text>
              <RunIdsBlock fields={buildRunIdFields(detail, true)} />
              {(detail.trace_id || detail.task_id) && (
                <Space size="small" wrap className="canvas-run-detail__ids-actions">
                  {detail.trace_id ? (
                    <Link href={`/admin/trace-logs?trace_id=${detail.trace_id}`} target="_blank">
                      查看链路日志
                    </Link>
                  ) : null}
                  {detail.task_id ? (
                    <Link href={`/admin/tasks?task_id=${detail.task_id}`} target="_blank">
                      查看任务详情
                    </Link>
                  ) : null}
                </Space>
              )}
            </div>
            {detail.params?.prompt && (
              <div className="canvas-run-detail__prompt">
                <Text type="secondary">提示词</Text>
                <Paragraph
                  className="canvas-run-selectable"
                  style={{ marginBottom: 0, whiteSpace: 'pre-wrap' }}
                >
                  {String(detail.params.prompt)}
                </Paragraph>
              </div>
            )}
            <div className="canvas-run-detail__result">
              <NodeResultView
                result={detail.result}
                status={detail.status === 'success' ? 'success' : detail.status === 'failed' ? 'failed' : detail.status}
                errorMessage={detail.error_message}
                fitContain
              />
            </div>
          </div>
        ) : null}
      </Modal>
    </>
  )
}
