import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { useParams } from 'react-router-dom'
import { canvasAgentBridge } from '@/utils/canvasAgentBridge'
import DramaAgentPanel from './DramaAgentPanel'

/** 挂载在 CanvasEditorInner 之外，画布 setNodes 不会触发本组件重渲染 */
export default function CanvasAgentPanelPortal() {
  const { projectId } = useParams<{ projectId: string }>()
  const panelCanvasId = projectId || 'new'
  const bindableCanvasProjectId = projectId && projectId !== 'new' ? projectId : undefined
  const [workspaceEl, setWorkspaceEl] = useState(() => canvasAgentBridge.workspaceEl)

  useEffect(() => {
    setWorkspaceEl(canvasAgentBridge.workspaceEl)
    return canvasAgentBridge.subscribeWorkspace(() => {
      setWorkspaceEl(canvasAgentBridge.workspaceEl)
    })
  }, [])

  if (!workspaceEl) return null

  return createPortal(
    <DramaAgentPanel
      canvasProjectId={panelCanvasId}
      bindableCanvasProjectId={bindableCanvasProjectId}
      spawnTextNodeRef={canvasAgentBridge.spawnTextNodeRef}
      spawnImageTaskRef={canvasAgentBridge.spawnImageTaskRef}
    />,
    workspaceEl,
  )
}
