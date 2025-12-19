'use client'

import { useEffect, useMemo, useState } from 'react'
import clsx from 'clsx'
import { RunPayload, LlmProvider } from '../lib/types'
import { isPositiveInt, isValidHttpUrl, tryParseJson } from '../lib/validators'

const providerOptions: { value: LlmProvider; label: string }[] = [
  { value: 'ollama', label: 'Ollama (local/self-hosted)' },
  { value: 'openai_compatible', label: 'OpenAI Compatible API' },
  { value: 'other', label: 'Other (manual)' },
]

type Props = {
  onSubmit: (payload: RunPayload) => Promise<void> | void
  isSubmitting: boolean
}

export function RunForm({ onSubmit, isSubmitting }: Props) {
  const [endpointUrl, setEndpointUrl] = useState('')
  const [llmProvider, setLlmProvider] = useState<LlmProvider>('ollama')
  const [model, setModel] = useState('llama3')
  const [apiKey, setApiKey] = useState('')
  const [graphqlHeadersJson, setGraphqlHeadersJson] = useState('')
  const [rounds, setRounds] = useState(2)
  const [requestsPerNode, setRequestsPerNode] = useState(2)
  const [notes, setNotes] = useState('')
  const [errors, setErrors] = useState<string[]>([])

  useEffect(() => {
    if (llmProvider === 'ollama' && model.trim() === '') {
      setModel('llama3')
    }
  }, [llmProvider, model])

  const requiresApiKey = llmProvider === 'openai_compatible' || llmProvider === 'other'

  const isValid = useMemo(() => {
    const nextErrors: string[] = []
    if (!isValidHttpUrl(endpointUrl)) nextErrors.push('Endpoint URL must start with http or https.')
    if (!model.trim()) nextErrors.push('Model is required.')
    if (!isPositiveInt(rounds, 10)) nextErrors.push('Rounds must be a positive integer (<=10).')
    if (!isPositiveInt(requestsPerNode, 20)) nextErrors.push('Requests per node must be a positive integer (<=20).')
    if (requiresApiKey && !apiKey.trim()) nextErrors.push('API key required for this provider.')
    if (graphqlHeadersJson.trim()) {
      try {
        tryParseJson(graphqlHeadersJson)
      } catch (err) {
        nextErrors.push('Headers JSON is invalid.')
      }
    }
    setErrors(nextErrors)
    return nextErrors.length === 0
  }, [endpointUrl, model, rounds, requestsPerNode, requiresApiKey, apiKey, graphqlHeadersJson])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!isValid) return
    const payload: RunPayload = {
      endpointUrl,
      llmProvider,
      model,
      apiKey: requiresApiKey ? apiKey : undefined,
      graphqlHeadersJson: graphqlHeadersJson || undefined,
      rounds,
      requestsPerNode,
      notes: notes || undefined,
    }
    onSubmit(payload)
  }

  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-6 shadow-xl">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-sm uppercase tracking-[0.2em] text-slate-400">Configuration</p>
          <h2 className="text-xl font-semibold text-white">Run parameters</h2>
        </div>
        <span className="rounded-full bg-white/10 px-3 py-1 text-xs font-semibold text-slate-200">Mock API mode</span>
      </div>

      <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
        <label className="block space-y-2">
          <span className="text-sm text-slate-200">GraphQL endpoint URL</span>
          <input
            className="w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm"
            placeholder="https://api.myapp.com/graphql"
            value={endpointUrl}
            onChange={(e) => setEndpointUrl(e.target.value)}
            required
          />
        </label>

        <div className="grid gap-4 md:grid-cols-2">
          <label className="block space-y-2">
            <span className="text-sm text-slate-200">Provider</span>
            <select
              className="w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm"
              value={llmProvider}
              onChange={(e) => setLlmProvider(e.target.value as LlmProvider)}
            >
              {providerOptions.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </label>

          <label className="block space-y-2">
            <span className="text-sm text-slate-200">Model</span>
            <input
              className="w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm"
              placeholder={llmProvider === 'ollama' ? 'llama3' : 'gpt-4o-mini'}
              value={model}
              onChange={(e) => setModel(e.target.value)}
            />
          </label>
        </div>

        {requiresApiKey && (
          <label className="block space-y-2">
            <span className="text-sm text-slate-200">API Key</span>
            <input
              type="password"
              className="w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm"
              placeholder="sk-..."
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
            />
          </label>
        )}

        <label className="block space-y-2">
          <span className="text-sm text-slate-200">GraphQL headers (JSON)</span>
          <textarea
            className="w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm"
            rows={3}
            placeholder='{"Authorization": "Bearer ..."}'
            value={graphqlHeadersJson}
            onChange={(e) => setGraphqlHeadersJson(e.target.value)}
          />
        </label>

        <div className="grid gap-4 md:grid-cols-2">
          <label className="block space-y-2">
            <span className="text-sm text-slate-200">Rounds</span>
            <input
              type="number"
              min={1}
              max={10}
              className="w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm"
              value={rounds}
              onChange={(e) => setRounds(Number(e.target.value))}
            />
          </label>
          <label className="block space-y-2">
            <span className="text-sm text-slate-200">Requests per node</span>
            <input
              type="number"
              min={1}
              max={20}
              className="w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm"
              value={requestsPerNode}
              onChange={(e) => setRequestsPerNode(Number(e.target.value))}
            />
          </label>
        </div>

        <label className="block space-y-2">
          <span className="text-sm text-slate-200">Notes (optional)</span>
          <textarea
            className="w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm"
            rows={2}
            placeholder="Describe the goal of this scan"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
        </label>

        {errors.length > 0 && (
          <ul className="list-disc space-y-1 rounded-xl border border-red-400/40 bg-red-500/10 p-3 text-sm text-red-100">
            {errors.map((err) => (
              <li key={err}>{err}</li>
            ))}
          </ul>
        )}

        <button
          type="submit"
          disabled={!isValid || isSubmitting}
          className={clsx(
            'btn-primary inline-flex items-center justify-center rounded-xl px-4 py-2 text-sm',
            (!isValid || isSubmitting) && 'opacity-60'
          )}
        >
          {isSubmitting ? 'Launching…' : 'Start run'}
        </button>
      </form>
    </div>
  )
}
