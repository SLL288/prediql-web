"use client"

import { useEffect, useRef, useState } from 'react'
import { HeaderBar } from '../components/HeaderBar'
import { RunForm } from '../components/RunForm'
import { RunStatus } from '../components/RunStatus'
import { LogViewer } from '../components/LogViewer'
import { ResultsPanel } from '../components/ResultsPanel'
import { apiClient, apiMode } from '../lib/apiClient'
import { ResultsResponse, RunPayload, RunState } from '../lib/types'

const tabs = ['status', 'logs', 'results'] as const

export default function Page() {
  const [runId, setRunId] = useState<string | null>(null)
  const [runState, setRunState] = useState<RunState | null>(null)
  const [logs, setLogs] = useState<string[]>([])
  const [logCursor, setLogCursor] = useState(0)
  const logCursorRef = useRef(0)
  const [results, setResults] = useState<ResultsResponse | null>(null)
  const [activeTab, setActiveTab] = useState<(typeof tabs)[number]>('status')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!runId) return

    let cancelled = false

    async function pollStatus() {
      try {
        const status = await apiClient.getRun(runId)
        if (cancelled) return
        setRunState(status)
        if (status.status === 'done') {
          fetchResults(runId)
        }
      } catch (err) {
        console.error(err)
      }
    }

    async function pollLogs() {
      try {
        const res = await apiClient.getLogs(runId, logCursorRef.current)
        if (cancelled) return
        if (res.lines.length) {
          setLogs((prev) => [...prev, ...res.lines])
          setLogCursor(res.nextCursor)
          logCursorRef.current = res.nextCursor
        }
      } catch (err) {
        console.error(err)
      }
    }

    const statusInterval = setInterval(pollStatus, 1200)
    const logsInterval = setInterval(pollLogs, 1000)

    pollStatus()
    pollLogs()

    return () => {
      cancelled = true
      clearInterval(statusInterval)
      clearInterval(logsInterval)
    }
  }, [runId])

  const startRun = async (payload: RunPayload) => {
    setIsSubmitting(true)
    setError(null)
    setLogs([])
    setLogCursor(0)
    logCursorRef.current = 0
    setResults(null)
    setRunState(null)
    setActiveTab('status')
    try {
      const { runId: newRunId } = await apiClient.createRun(payload)
      setRunId(newRunId)
      setRunState({ runId: newRunId, status: 'queued', progress: 0 })
    } catch (err: any) {
      setError(err?.message || 'Failed to start run')
    } finally {
      setIsSubmitting(false)
    }
  }

  const fetchResults = async (id: string) => {
    try {
      const res = await apiClient.getResults(id)
      setResults(res)
    } catch (err) {
      console.error(err)
    }
  }

  const cancelRun = async () => {
    if (!runId || !apiClient.cancelRun) return
    await apiClient.cancelRun(runId)
    const status = await apiClient.getRun(runId)
    setRunState(status)
  }

  return (
    <main className="container-outer mx-auto px-4 py-8">
      <HeaderBar />

      {error && <div className="mb-4 rounded-xl border border-red-400/40 bg-red-500/10 px-3 py-2 text-sm text-red-100">{error}</div>}

      <div className="grid gap-6 lg:grid-cols-[1.1fr_1fr]">
        <div>
          <RunForm onSubmit={startRun} isSubmitting={isSubmitting} />
        </div>

        <div className="space-y-4">
          <div className="flex gap-2">
            {tabs.map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`rounded-full px-4 py-2 text-xs font-semibold capitalize ${
                  activeTab === tab ? 'bg-white/20 text-white' : 'bg-white/5 text-slate-300'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          {activeTab === 'status' && <RunStatus run={runState} onCancel={cancelRun} />}
          {activeTab === 'logs' && <LogViewer logs={logs} />}
          {activeTab === 'results' && <ResultsPanel results={results} />}
        </div>
      </div>
    </main>
  )
}
