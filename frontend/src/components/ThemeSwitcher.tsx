import { Dropdown } from 'antd'
import type { MenuProps } from 'antd'
import { BulbOutlined, CheckOutlined } from '@ant-design/icons'
import type { SiteThemeMode } from '@/hooks/useSiteTheme'

const LABELS: Record<SiteThemeMode, string> = {
  light: '浅色',
  dark: '深色',
  system: '随系统',
}

interface ThemeSwitcherProps {
  mode: SiteThemeMode
  onChange: (mode: SiteThemeMode) => void
}

export default function ThemeSwitcher({ mode, onChange }: ThemeSwitcherProps) {
  const items: MenuProps['items'] = (['light', 'dark', 'system'] as SiteThemeMode[]).map((m) => ({
    key: m,
    label: (
      <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        {mode === m ? <CheckOutlined /> : <span style={{ width: 14 }} />}
        {LABELS[m]}
      </span>
    ),
    onClick: () => onChange(m),
  }))

  return (
    <Dropdown menu={{ items }} trigger={['click']}>
      <button type="button" className="app-header-theme-btn" title="主题">
        <BulbOutlined />
      </button>
    </Dropdown>
  )
}
