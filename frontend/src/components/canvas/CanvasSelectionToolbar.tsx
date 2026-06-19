import { Button, Space } from 'antd'
import { GroupOutlined, UngroupOutlined } from '@ant-design/icons'

interface CanvasSelectionToolbarProps {
  selectedCount: number
  canGroup: boolean
  canUngroup: boolean
  onGroup: () => void
  onUngroup: () => void
}

export default function CanvasSelectionToolbar({
  selectedCount,
  canGroup,
  canUngroup,
  onGroup,
  onUngroup,
}: CanvasSelectionToolbarProps) {
  if (selectedCount === 0) return null
  if (!canGroup && !canUngroup) return null

  return (
    <div className="canvas-selection-toolbar">
      <Space size={8}>
        <span className="canvas-selection-toolbar__hint">已选 {selectedCount} 项</span>
        {canGroup ? (
          <Button type="primary" size="small" icon={<GroupOutlined />} onClick={onGroup}>
            分组
          </Button>
        ) : null}
        {canUngroup ? (
          <Button size="small" icon={<UngroupOutlined />} onClick={onUngroup}>
            解组
          </Button>
        ) : null}
      </Space>
    </div>
  )
}
