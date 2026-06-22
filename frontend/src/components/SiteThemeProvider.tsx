import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { ConfigProvider, theme as antdTheme } from 'antd'
import zhCN from 'antd/locale/zh_CN'

export type SiteThemeMode = 'light' | 'dark' | 'system'

const STORAGE_KEY = 'site_theme_mode'

function getSystemDark(): boolean {
  return window.matchMedia('(prefers-color-scheme: dark)').matches
}

export function resolveEffectiveTheme(mode: SiteThemeMode): 'light' | 'dark' {
  if (mode === 'system') return getSystemDark() ? 'dark' : 'light'
  return mode
}

type ThemeContextValue = {
  mode: SiteThemeMode
  setMode: (mode: SiteThemeMode) => void
  effective: 'light' | 'dark'
  antdAlgorithm: typeof antdTheme.defaultAlgorithm
}

const ThemeContext = createContext<ThemeContextValue | null>(null)

export function SiteThemeProvider({ children }: { children: ReactNode }) {
  const [mode, setModeState] = useState<SiteThemeMode>(() => {
    const saved = localStorage.getItem(STORAGE_KEY) as SiteThemeMode | null
    return saved === 'light' || saved === 'dark' || saved === 'system' ? saved : 'light'
  })
  const [effective, setEffective] = useState<'light' | 'dark'>(() => resolveEffectiveTheme(mode))

  const apply = useCallback((nextMode: SiteThemeMode) => {
    const eff = resolveEffectiveTheme(nextMode)
    setEffective(eff)
    document.documentElement.dataset.theme = eff
    document.documentElement.style.colorScheme = eff
  }, [])

  useEffect(() => {
    apply(mode)
  }, [mode, apply])

  useEffect(() => {
    if (mode !== 'system') return
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    const onChange = () => apply('system')
    mq.addEventListener('change', onChange)
    return () => mq.removeEventListener('change', onChange)
  }, [mode, apply])

  const setMode = useCallback((next: SiteThemeMode) => {
    localStorage.setItem(STORAGE_KEY, next)
    setModeState(next)
  }, [])

  const antdAlgorithm = useMemo(
    () => (effective === 'dark' ? antdTheme.darkAlgorithm : antdTheme.defaultAlgorithm),
    [effective],
  )

  const value = useMemo(
    () => ({ mode, setMode, effective, antdAlgorithm }),
    [mode, setMode, effective, antdAlgorithm],
  )

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

export function useSiteTheme() {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useSiteTheme must be used within SiteThemeProvider')
  return ctx
}

function AntdThemeBridge({ children }: { children: ReactNode }) {
  const { antdAlgorithm, effective } = useSiteTheme()
  const darkTokens =
    effective === 'dark'
      ? {
          colorBgContainer: '#1e1e24',
          colorBgElevated: '#22222a',
          colorBgLayout: '#141418',
          colorBorder: '#2e2e36',
          colorText: '#e8e8ec',
          colorTextSecondary: '#a8a8b0',
        }
      : {}
  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        algorithm: antdAlgorithm,
        token: {
          colorPrimary: '#7c5cfc',
          borderRadius: 8,
          fontFamily:
            "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif",
          ...darkTokens,
        },
      }}
    >
      {children}
    </ConfigProvider>
  )
}

export function AppThemeRoot({ children }: { children: ReactNode }) {
  return (
    <SiteThemeProvider>
      <AntdThemeBridge>{children}</AntdThemeBridge>
    </SiteThemeProvider>
  )
}
