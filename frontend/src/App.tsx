import { useEffect } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Workspace from './pages/Workspace'
import { useGenerationStore } from './store/generation'
import { getDefaultModel } from './api'

function App() {
  const { activeCategory, setModel } = useGenerationStore()

  useEffect(() => {
    const loadDefault = async () => {
      try {
        const res = await getDefaultModel(activeCategory)
        if (res.code === 'success' && res.data) {
          setModel(res.data)
        }
      } catch (e) {
        console.error('加载默认模型失败', e)
      }
    }
    loadDefault()
  }, [activeCategory])

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Workspace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
