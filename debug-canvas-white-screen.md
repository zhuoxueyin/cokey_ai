# debug-canvas-white-screen

Status: [OPEN]

## Symptom
CanvasEditor renders white screen after the recent selection interaction changes.

## Hypotheses
1. The CanvasEditor render tree now throws at runtime because a referenced state or variable is missing or moved during the last edits.
2. The selection state effect is causing an infinite re-render loop that blanks the page before paint.
3. The ReactFlow prop combination for selection/pan is invalid for the installed @xyflow/react version and crashes during mount.
4. The new keyboard/blur handlers are interacting with the canvas portal or ReactFlow provider in a way that throws only in the browser runtime.
5. The white screen is unrelated to CanvasEditor and is caused by a different frontend runtime error that happens on the same route.

## Reproduction
- Open canvas page and refresh after the latest edits.
- Observe white screen.

## Next evidence to collect
- Browser console/runtime stack from the first error.
- Whether the blank screen happens before or after ReactFlow mounts.
- Whether removing only the latest selection-state changes restores rendering.
