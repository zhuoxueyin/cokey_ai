import type { CanvasUpstreamPreview } from '@/utils/canvasUpstream'
import NodeReferenceStrip from './NodeReferenceStrip'

interface UpstreamInputChipsProps {
  upstream: CanvasUpstreamPreview
}

export default function UpstreamInputChips({ upstream }: UpstreamInputChipsProps) {
  return <NodeReferenceStrip upstream={upstream} variant="panel" />
}
