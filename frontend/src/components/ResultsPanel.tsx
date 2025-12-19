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
    const summary = results.summary || {}
    const counts = summary.counts || {}
    return [
      { label: 'Types', value: counts.types ?? 'n/a' },
      { label: 'Queries', value: counts.queries ?? 'n/a' },
      { label: 'Mutations', value: counts.mutations ?? 'n/a' },
      { label: 'Candidates', value: summary.candidates ?? 'n/a' },
      { label: 'Executions', value: summary.executions ?? 'n/a' },
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
            onClick={() => download('summary.json', results.summary)}
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

      <p className="mt-3 text-slate-200 leading-relaxed">
        Endpoint: {results.summary?.endpoint || 'n/a'} • Candidates: {results.summary?.candidates ?? 'n/a'} • Executions:{' '}
        {results.summary?.executions ?? 'n/a'}
      </p>

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
