import { BaseEdge, EdgeLabelRenderer, getBezierPath, type EdgeProps } from '@xyflow/react'

/** 画布连线：选中态加粗发光 + 中心提示标签 */
export default function CanvasBezierEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  selected,
}: EdgeProps) {
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  })

  return (
    <>
      {selected ? (
        <BaseEdge
          id={`${id}-halo`}
          path={edgePath}
          className="canvas-edge__halo"
          interactionWidth={0}
        />
      ) : null}
      <BaseEdge
        id={id}
        path={edgePath}
        className={selected ? 'canvas-edge__path canvas-edge__path--selected' : 'canvas-edge__path'}
      />
      {selected ? (
        <EdgeLabelRenderer>
          <div
            className="canvas-edge-selection-tag nodrag nopan"
            style={{
              transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
            }}
          >
            连线已选中 · Delete 删除
          </div>
        </EdgeLabelRenderer>
      ) : null}
    </>
  )
}
