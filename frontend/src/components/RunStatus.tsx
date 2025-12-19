'use client'

import clsx from 'clsx'
import { RunState } from '../lib/types'

type Props = {
  run: RunState | null
  onCancel?: () => void
}

const statusColor: Record<RunState['status'], string> = {
  queued: 'bg-amber-500/20 text-amber-100 border-amber-500/40',
  running: 'bg-blue-500/20 text-blue-100 border-blue-500/40',
  done: 'bg-emerald-500/20 text-emerald-100 border-emerald-500/40',
  failed: 'bg-red-500/20 text-red-100 border-red-500/40',
  cancelled: 'bg-slate-500/20 text-slate-100 border-slate-500/40',
}

export function RunStatus({ run, onCancel }: Props) {
  if (!run) {
    return (
      <div className="rounded-2xl border border-white/10 bg-white/5 p-6 text-sm text-slate-300">
        No active run yet. Launch one to see status.
      </div>
    )
  }

  const progressPct = Math.round((run.progress?.pct || 0) * 100)

  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-6 shadow-lg">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Run status</p>
          <h3 className="text-lg font-semibold text-white">{run.runId}</h3>
          <p className="text-xs text-slate-400">Started: {run.startedAt || 'pending'} | Finished: {run.finishedAt || '–'}</p>
        </div>
        <span className={clsx('rounded-full border px-3 py-1 text-xs font-semibold capitalize', statusColor[run.status])}>
          {run.status}
        </span>
      </div>

      <div className="mt-4">
        <div className="flex items-center justify-between text-xs text-slate-300">
          <span>Progress</span>
          <span className="font-mono">{progressPct}%</span>
        </div>
        <div className="mt-2 h-3 w-full overflow-hidden rounded-full bg-white/10">
          <div className="h-full rounded-full bg-gradient-to-r from-sky-400 to-cyan-300" style={{ width: `${progressPct}%` }} />
        </div>
        <p className="mt-1 text-xs text-slate-400">
          Stage: {run.progress?.stage || 'n/a'} {run.progress?.detail ? `— ${run.progress.detail}` : ''}
        </p>
        {run.error && <p className="mt-2 text-sm text-red-200">{run.error}</p>}
      </div>

      {run.status === 'running' && onCancel && (
        <button
          onClick={onCancel}
          className="mt-4 rounded-lg border border-red-400/50 px-3 py-2 text-xs font-semibold text-red-100 hover:border-red-200"
        >
          Cancel run
        </button>
      )}
    </div>
  )
}
