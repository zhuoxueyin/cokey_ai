import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

/** 菜单「无限画布」入口：进入空白画布，首次编辑后再保存项目 */
export default function CanvasEntryPage() {
  const navigate = useNavigate()

  useEffect(() => {
    navigate('/canvas/new', { replace: true })
  }, [navigate])

  return null
}
