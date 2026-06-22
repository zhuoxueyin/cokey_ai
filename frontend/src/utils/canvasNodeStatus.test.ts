import { describe, expect, it } from 'vitest'
import { resolveNodeDisplayStatus, shouldSyncCanvasNodeFromServer } from './canvasNodeStatus'
import type { CanvasNode } from '@/types/canvas'

function baseNode(overrides: Partial<CanvasNode> = {}): CanvasNode {
  return {
    id: '1',
    node_id: 'n1',
    project_id: 'p1',
    node_type: 'image',
    title: 'test',
    position: { x: 0, y: 0 },
    config: {},
    result_version: 0,
    status: 'idle',
    input_stale: false,
    upstream_snapshot: {},
    created_at: '',
    updated_at: '',
    ...overrides,
  }
}

describe('shouldSyncCanvasNodeFromServer', () => {
  it('syncs when server finished running', () => {
    const local = baseNode({ status: 'running', result_version: 1 })
    const server = baseNode({
      status: 'success',
      result_version: 2,
      result: { images: ['https://example.com/a.png'] },
    })
    expect(shouldSyncCanvasNodeFromServer(local, server)).toBe(true)
  })

  it('ignores unchanged idle nodes', () => {
    const local = baseNode({ status: 'idle', result_version: 1 })
    const server = baseNode({ status: 'idle', result_version: 1 })
    expect(shouldSyncCanvasNodeFromServer(local, server)).toBe(false)
  })
})

describe('resolveNodeDisplayStatus', () => {
  it('shows success when result exists even if status is running', () => {
    const node = baseNode({
      status: 'running',
      result: { images: ['https://example.com/a.png'] },
    })
    expect(resolveNodeDisplayStatus(node, 'n1')).toBe('success')
  })

  it('shows running when activeRunNodeId matches without result', () => {
    const node = baseNode({ status: 'idle' })
    expect(resolveNodeDisplayStatus(node, 'n1')).toBe('running')
  })

  it('shows running when success but result not synced yet', () => {
    const node = baseNode({ status: 'success', task_id: 'task_1' })
    expect(resolveNodeDisplayStatus(node, null)).toBe('running')
  })
})
