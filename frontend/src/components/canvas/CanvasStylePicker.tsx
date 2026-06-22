import { useEffect, useState } from 'react'
import { Tooltip } from 'antd'
import { BgColorsOutlined, DownOutlined } from '@ant-design/icons'
import { listDramaStylesUser } from '@/api/drama'
import StylePickerGrid from '@/components/drama/StylePickerGrid'
import type { DramaStylePreset } from '@/types/drama'

interface CanvasStylePickerProps {
  stylePresetId?: string
  stylePresetName?: string
  onChange: (styleId?: string, styleName?: string) => void
}

export default function CanvasStylePicker({
  stylePresetId,
  stylePresetName,
  onChange,
}: CanvasStylePickerProps) {
  const [open, setOpen] = useState(false)
  const [styles, setStyles] = useState<DramaStylePreset[]>([])

  useEffect(() => {
    listDramaStylesUser({ page: 1, page_size: 200 }).then((res) => {
      setStyles((res.data as DramaStylePreset[]) || [])
    })
  }, [])

  const selected =
    styles.find((s) => s.style_id === stylePresetId) ||
    (stylePresetId && stylePresetName
      ? ({ style_id: stylePresetId, name: stylePresetName } as DramaStylePreset)
      : undefined)

  const label = selected?.name || '风格'

  return (
    <>
      <Tooltip title={selected ? `参考风格：${selected.name}` : '选择风格作为生图/生视频参考提示词'}>
        <button
          type="button"
          className={`canvas-text-composer__pill canvas-text-composer__pill--ghost${
            stylePresetId ? ' canvas-text-composer__pill--active' : ''
          }`}
          onClick={() => setOpen(true)}
        >
          <BgColorsOutlined />
          <span className="canvas-style-picker__label">{label}</span>
          <DownOutlined />
        </button>
      </Tooltip>
      <StylePickerGrid
        open={open}
        onClose={() => setOpen(false)}
        styles={styles}
        value={stylePresetId}
        title="选择参考风格"
        onChange={(id) => {
          const style = styles.find((s) => s.style_id === id)
          onChange(id, style?.name)
        }}
      />
    </>
  )
}
