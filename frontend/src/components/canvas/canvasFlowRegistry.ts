import CanvasBezierEdge from './CanvasBezierEdge'
import ResourceNode from './nodes/ResourceNode'
import TextNode from './nodes/TextNode'
import ImageNode from './nodes/ImageNode'
import VideoNode from './nodes/VideoNode'
import GroupNode from './nodes/GroupNode'
import TitleNode from './nodes/TitleNode'

export const canvasEdgeTypes = {
  canvas: CanvasBezierEdge,
}

export const canvasNodeTypes = {
  resource: ResourceNode,
  text: TextNode,
  image: ImageNode,
  video: VideoNode,
  group: GroupNode,
  title: TitleNode,
}
