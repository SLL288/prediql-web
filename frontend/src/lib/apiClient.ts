import { ApiClient } from './types'
import { mockApiClient } from './mockApi'

const mode = process.env.NEXT_PUBLIC_API_MODE || 'mock'

function createRestClient(): ApiClient {
  const baseUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

  return {
    async createRun(payload) {
      const res = await fetch(`${baseUrl}/api/runs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!res.ok) throw new Error('Failed to start run')
      const data = await res.json()
      return { runId: data.runId }
    },
    async getRun(runId) {
      const res = await fetch(`${baseUrl}/api/runs/${runId}`)
      if (!res.ok) throw new Error('Run not found')
      return res.json()
    },
    async getLogs(runId, cursor = 0) {
      const res = await fetch(`${baseUrl}/api/runs/${runId}/logs?cursor=${cursor}`)
      if (!res.ok) throw new Error('Run not found')
      const data = await res.json()
      return { lines: data.lines, nextCursor: data.nextCursor ?? data.next_cursor ?? cursor }
    },
    async getResults(runId) {
      const res = await fetch(`${baseUrl}/api/runs/${runId}/results`)
      if (!res.ok) throw new Error('Results not ready')
      return res.json()
    },
    async cancelRun(runId) {
      await fetch(`${baseUrl}/api/runs/${runId}/cancel`, { method: 'POST' })
    },
  }
}

export const apiClient: ApiClient = mode === 'mock' ? mockApiClient : createRestClient()
export const apiMode = mode
