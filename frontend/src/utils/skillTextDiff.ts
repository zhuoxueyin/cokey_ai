export type SideDiffCellKind = 'equal' | 'delete' | 'insert' | 'empty'

export interface SideDiffCell {
  num?: number
  text: string
  kind: SideDiffCellKind
}

export interface SideDiffRow {
  left: SideDiffCell
  right: SideDiffCell
}

interface DiffOpcode {
  tag: 'equal' | 'insert' | 'delete'
  i1: number
  i2: number
  j1: number
  j2: number
}

function normalizeLines(text: string): string[] {
  if (!text) return []
  return text.replace(/\r\n/g, '\n').split('\n')
}

/** LCS 行级 opcodes，语义对齐 Python difflib.SequenceMatcher.get_opcodes */
function getLineOpcodes(oldLines: string[], newLines: string[]): DiffOpcode[] {
  const n = oldLines.length
  const m = newLines.length
  const dp: number[][] = Array.from({ length: n + 1 }, () => Array(m + 1).fill(0))

  for (let i = n - 1; i >= 0; i -= 1) {
    for (let j = m - 1; j >= 0; j -= 1) {
      dp[i][j] =
        oldLines[i] === newLines[j]
          ? dp[i + 1][j + 1] + 1
          : Math.max(dp[i + 1][j], dp[i][j + 1])
    }
  }

  const ops: DiffOpcode[] = []
  let i = 0
  let j = 0

  while (i < n || j < m) {
    if (i < n && j < m && oldLines[i] === newLines[j]) {
      const startI = i
      const startJ = j
      while (i < n && j < m && oldLines[i] === newLines[j]) {
        i += 1
        j += 1
      }
      ops.push({ tag: 'equal', i1: startI, i2: i, j1: startJ, j2: j })
    } else if (j < m && (i >= n || dp[i][j + 1] >= dp[i + 1][j])) {
      const startJ = j
      while (j < m && (i >= n || dp[i][j + 1] >= dp[i + 1][j])) {
        j += 1
      }
      ops.push({ tag: 'insert', i1: i, i2: i, j1: startJ, j2: j })
    } else {
      const startI = i
      while (i < n && (j >= m || dp[i + 1][j] >= dp[i][j + 1])) {
        i += 1
      }
      ops.push({ tag: 'delete', i1: startI, i2: i, j1: j, j2: j })
    }
  }

  return ops
}

const EMPTY_CELL = (kind: SideDiffCellKind): SideDiffCell => ({ text: '', kind })

export function buildSideBySideDiff(oldText: string, newText: string): SideDiffRow[] {
  const oldLines = normalizeLines(oldText)
  const newLines = normalizeLines(newText)
  const rows: SideDiffRow[] = []

  for (const op of getLineOpcodes(oldLines, newLines)) {
    if (op.tag === 'equal') {
      for (let k = op.i1; k < op.i2; k += 1) {
        const j = op.j1 + (k - op.i1)
        rows.push({
          left: { num: k + 1, text: oldLines[k], kind: 'equal' },
          right: { num: j + 1, text: newLines[j], kind: 'equal' },
        })
      }
      continue
    }

    if (op.tag === 'delete') {
      for (let k = op.i1; k < op.i2; k += 1) {
        rows.push({
          left: { num: k + 1, text: oldLines[k], kind: 'delete' },
          right: EMPTY_CELL('empty'),
        })
      }
      continue
    }

    for (let k = op.j1; k < op.j2; k += 1) {
      rows.push({
        left: EMPTY_CELL('empty'),
        right: { num: k + 1, text: newLines[k], kind: 'insert' },
      })
    }
  }

  return rows
}

export function countSideDiffChanges(rows: SideDiffRow[]): { deleted: number; inserted: number } {
  let deleted = 0
  let inserted = 0
  for (const row of rows) {
    if (row.left.kind === 'delete') deleted += 1
    if (row.right.kind === 'insert') inserted += 1
  }
  return { deleted, inserted }
}
