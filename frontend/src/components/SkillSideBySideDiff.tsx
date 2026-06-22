import { useMemo } from 'react'
import { buildSideBySideDiff, countSideDiffChanges } from '@/utils/skillTextDiff'

export interface SkillSideBySideDiffProps {
  oldText: string
  newText: string
  oldLabel?: string
  newLabel?: string
  className?: string
}

function cellClass(kind: string): string {
  if (kind === 'delete') return 'skill-side-diff__cell--delete'
  if (kind === 'insert') return 'skill-side-diff__cell--insert'
  if (kind === 'empty') return 'skill-side-diff__cell--empty'
  return 'skill-side-diff__cell--equal'
}

export default function SkillSideBySideDiff({
  oldText,
  newText,
  oldLabel = '线上已发布',
  newLabel = '待发布草稿',
  className,
}: SkillSideBySideDiffProps) {
  const rows = useMemo(() => buildSideBySideDiff(oldText, newText), [oldText, newText])
  const stats = useMemo(() => countSideDiffChanges(rows), [rows])

  return (
    <div className={['skill-side-diff', className].filter(Boolean).join(' ')}>
      <div className="skill-side-diff__meta">
        <span>
          删除 <strong>{stats.deleted}</strong> 行
        </span>
        <span>
          新增 <strong>{stats.inserted}</strong> 行
        </span>
        <span>
          共 <strong>{rows.length}</strong> 行
        </span>
      </div>
      <div className="skill-side-diff__columns">
        <div className="skill-side-diff__col-head">{oldLabel}</div>
        <div className="skill-side-diff__col-head">{newLabel}</div>
      </div>
      <div className="skill-side-diff__scroll">
        {rows.length === 0 ? (
          <div className="skill-side-diff__empty">（两侧均为空）</div>
        ) : (
          rows.map((row, index) => (
            <div key={index} className="skill-side-diff__row">
              <div className={`skill-side-diff__cell skill-side-diff__cell--left ${cellClass(row.left.kind)}`}>
                <span className="skill-side-diff__gutter">{row.left.num ?? ''}</span>
                <code className="skill-side-diff__text">{row.left.text || ' '}</code>
              </div>
              <div className={`skill-side-diff__cell skill-side-diff__cell--right ${cellClass(row.right.kind)}`}>
                <span className="skill-side-diff__gutter">{row.right.num ?? ''}</span>
                <code className="skill-side-diff__text">{row.right.text || ' '}</code>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
