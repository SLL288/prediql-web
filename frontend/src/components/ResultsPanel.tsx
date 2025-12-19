'use client'

import { useMemo, useState } from 'react'
import { ResultsResponse } from '../lib/types'

type Props = {
  results: ResultsResponse | null
}

export function ResultsPanel({ results }: Props) {
  const [expanded, setExpanded] = useState(false)

  const cards = useMemo(() => {
    if (!results) return []
    const raw = results.rawJson || {}
    return [
      { label: 'Valid queries', value: raw.validQueriesFound ?? 'n/a' },
      { label: 'Mutations tried', value: raw.mutationsTried ?? 'n/a' },
      { label: 'Potential issues', value: raw.potentialIssues?.length ?? 'n/a' },
    ]
  }, [results])

  if (!results) {
    return (
      <div className="rounded-2xl border border-white/10 bg-white/5 p-6 text-sm text-slate-300">
        Results will appear when the run completes.
      </div>
    )
  }

  const download = (filename: string, payload: Record<string, any>) => {
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-6 shadow-lg">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Results</p>
          <h3 className="text-lg font-semibold text-white">Summary</h3>
        </div>
        <div className="flex gap-2 text-xs">
          <button
            className="rounded-lg border border-white/20 px-3 py-1 text-slate-100 hover:border-white/50"
            onClick={() => download('summary.json', { summary: results.summary })}
          >
            Download summary.json
          </button>
          <button
            className="rounded-lg border border-white/20 px-3 py-1 text-slate-100 hover:border-white/50"
            onClick={() => download('raw_results.json', results.rawJson)}
          >
            Download raw_results.json
          </button>
        </div>
      </div>

      <p className="mt-3 text-slate-200 leading-relaxed">{results.summary}</p>

      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        {cards.map((card) => (
          <div key={card.label} className="rounded-xl border border-white/10 bg-black/30 p-3">
            <p className="text-xs uppercase tracking-[0.15em] text-slate-400">{card.label}</p>
            <p className="text-2xl font-semibold text-white">{card.value}</p>
          </div>
        ))}
      </div>

      <div className="mt-4">
        <button
          onClick={() => setExpanded((x) => !x)}
          className="text-sm text-cyan-200 hover:text-white"
        >
          {expanded ? 'Hide raw JSON' : 'Show raw JSON'}
        </button>
        {expanded && (
          <pre className="mt-2 max-h-80 overflow-auto rounded-xl border border-white/10 bg-black/30 p-3 text-sm text-slate-100">
            {JSON.stringify(results.rawJson, null, 2)}
          </pre>
        )}
      </div>
    </div>
  )
}
