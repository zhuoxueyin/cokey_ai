import React from 'react'
import ReactDOM from 'react-dom/client'
import { AppThemeRoot } from './components/SiteThemeProvider'
import App from './App'
import './index.css'

const saved = localStorage.getItem('site_theme_mode')
const mode = saved === 'dark' || saved === 'system' ? saved : 'light'
const effective =
  mode === 'system'
    ? window.matchMedia('(prefers-color-scheme: dark)').matches
      ? 'dark'
      : 'light'
    : mode
document.documentElement.dataset.theme = effective
document.documentElement.style.colorScheme = effective

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AppThemeRoot>
      <App />
    </AppThemeRoot>
  </React.StrictMode>,
)
