import { useEffect, useMemo, useState } from 'react'
import {
  CheckOutlined,
  CloseOutlined,
  DownOutlined,
  LoadingOutlined,
  MinusOutlined,
} from '@ant-design/icons'
import type { DramaAgentProcessStep } from '@/types/dramaAgent'

const KIND_LABELS: Record<string, string> = {
  context: '上下文',
  knowledge: '知识',
  skill: 'Skill',
  style: '风格',
  model: '模型',
  thinking: '推理',
}

interface DramaAgentProcessTraceProps {
  steps?: DramaAgentProcessStep[]
  defaultOpen?: boolean
  /** 流式生成中：显示脉动态 */
  live?: boolean
}

function StepStatusIcon({ status, live }: { status: string; live?: boolean }) {
  if (live && status === 'ok') {
    return <LoadingOutlined spin className="drama-agent-trace__status-icon drama-agent-trace__status-icon--live" />
  }
  if (status === 'error') {
    return <CloseOutlined className="drama-agent-trace__status-icon drama-agent-trace__status-icon--error" />
  }
  if (status === 'skip' || status === 'empty') {
    return <MinusOutlined className="drama-agent-trace__status-icon drama-agent-trace__status-icon--muted" />
  }
  return <CheckOutlined className="drama-agent-trace__status-icon drama-agent-trace__status-icon--ok" />
}

export default function DramaAgentProcessTrace({
  steps,
  defaultOpen,
  live,
}: DramaAgentProcessTraceProps) {
  const [open, setOpen] = useState(Boolean(defaultOpen))
  const stepCount = steps?.length ?? 0

  useEffect(() => {
    if (defaultOpen) setOpen(true)
  }, [defaultOpen])

  const okCount = useMemo(
    () => steps?.filter((s) => s.status === 'ok').length ?? 0,
    [steps],
  )

  if (!steps?.length) return null

  return (
    <div className={`drama-agent-trace${live ? ' drama-agent-trace--live' : ''}`}>
      <button
        type="button"
        className="drama-agent-trace__toggle"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
      >
        {live ? (
          <LoadingOutlined spin className="drama-agent-trace__toggle-icon" />
        ) : (
          <span className="drama-agent-trace__toggle-dot" aria-hidden />
        )}
        <span className="drama-agent-trace__toggle-text">
          {live ? '正在执行' : '执行过程'}
          <span className="drama-agent-trace__toggle-meta">
            · {stepCount} 步{okCount > 0 && !live ? ` · ${okCount} 完成` : ''}
          </span>
        </span>
        <DownOutlined
          className={`drama-agent-trace__chevron${open ? ' drama-agent-trace__chevron--open' : ''}`}
        />
      </button>

      {open && (
        <ol className="drama-agent-trace__rail" aria-label="执行过程">
          {steps.map((step, index) => {
            const isLast = index === steps.length - 1
            const kindLabel = KIND_LABELS[step.kind] || step.kind
            return (
              <li
                key={step.step_id}
                className={`drama-agent-trace__step drama-agent-trace__step--${step.status}`}
                data-last={isLast || undefined}
              >
                <span className="drama-agent-trace__node" aria-hidden>
                  <StepStatusIcon status={step.status} live={live && isLast && step.status === 'ok'} />
                </span>
                <div className="drama-agent-trace__body">
                  <div className="drama-agent-trace__line">
                    <span className="drama-agent-trace__title">{step.title}</span>
                    <span className="drama-agent-trace__kind">{kindLabel}</span>
                  </div>
                  {step.summary && (
                    <p className="drama-agent-trace__summary">{step.summary}</p>
                  )}
                  {step.items && step.items.length > 0 && (
                    <ul className="drama-agent-trace__items">
                      {step.items.map((item, idx) => (
                        <li key={`${step.step_id}-${idx}`}>{item.title || item.id}</li>
                      ))}
                    </ul>
                  )}
                  {step.detail && (
                    <div className="drama-agent-trace__detail">{step.detail}</div>
                  )}
                </div>
              </li>
            )
          })}
        </ol>
      )}
    </div>
  )
}
