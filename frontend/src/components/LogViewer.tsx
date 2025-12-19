'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import clsx from 'clsx'

type Props = {
  logs: string[]
  title?: string
}

export function LogViewer({ logs, title = 'Logs' }: Props) {
  const [autoScroll, setAutoScroll] = useState(true)
  const [filter, setFilter] = useState('')
  const logRef = useRef<HTMLDivElement | null>(null)

  const filtered = useMemo(() => {
    if (!filter.trim()) return logs
    const lower = filter.toLowerCase()
    return logs.filter((l) => l.toLowerCase().includes(lower))
  }, [filter, logs])

  useEffect(() => {
    if (!autoScroll) return
    const el = logRef.current
    if (el) {
      el.scrollTop = el.scrollHeight
    }
  }, [filtered, autoScroll])

  async function copyLogs() {
    try {
      await navigator.clipboard.writeText(filtered.join('\n'))
    } catch (err) {
      console.error('Copy failed', err)
    }
  }

  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-4 shadow-lg">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-slate-400">{title}</p>
          <h3 className="text-lg font-semibold text-white">Live stream</h3>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-200">
          <label className="flex items-center gap-1">
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={(e) => setAutoScroll(e.target.checked)}
              className="h-3 w-3 rounded border-white/30 bg-black/30"
            />
            Auto-scroll
          </label>
          <button
            onClick={copyLogs}
            className="rounded-lg border border-white/30 px-2 py-1 text-xs hover:border-white/60"
          >
            Copy
          </button>
        </div>
      </div>

      <div className="mt-3 flex items-center gap-2">
        <input
          className="w-full rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-xs"
          placeholder="Filter logs"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        />
        <span className="text-[11px] text-slate-400">{filtered.length} lines</span>
      </div>

      <div
        ref={logRef}
        className={clsx(
          'mt-3 h-64 overflow-y-auto rounded-xl border border-white/10 bg-black/40 p-3 font-mono text-[12px] leading-5 text-slate-100',
          'shadow-inner'
        )}
      >
        {filtered.length === 0 ? (
          <p className="text-slate-500">No logs yet.</p>
        ) : (
          filtered.map((line, idx) => <div key={`${line}-${idx}`}>{line}</div>)
        )}
      </div>
    </div>
  )
}
