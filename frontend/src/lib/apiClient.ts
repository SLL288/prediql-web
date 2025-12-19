import { ApiClient } from './types'
import { mockApiClient } from './mockApi'

const mode = process.env.NEXT_PUBLIC_API_MODE || 'mock'

function createRestClient(): ApiClient {
  const baseUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

  return {
    async createRun(payload) {
      // POST /api/runs { endpointUrl, llmProvider, model, apiKey?, requestsPerNode, rounds, headers? }
      const res = await fetch(`${baseUrl}/api/runs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!res.ok) throw new Error('Failed to start run')
      return res.json()
    },
    async getRun(runId) {
      // GET /api/runs/{runId}
      const res = await fetch(`${baseUrl}/api/runs/${runId}`)
      if (!res.ok) throw new Error('Run not found')
      return res.json()
    },
    async getLogs(runId, cursor = 0) {
      // GET /api/runs/{runId}/logs?cursor=n
      const res = await fetch(`${baseUrl}/api/runs/${runId}/logs?cursor=${cursor}`)
      if (!res.ok) throw new Error('Run not found')
      return res.json()
    },
    async getResults(runId) {
      // GET /api/runs/{runId}/results
      const res = await fetch(`${baseUrl}/api/runs/${runId}/results`)
      if (!res.ok) throw new Error('Results not ready')
      return res.json()
    },
    async cancelRun(runId) {
      // Optional future endpoint: POST /api/runs/{runId}/cancel
      console.warn('cancelRun REST stub invoked; no-op until backend implements cancel endpoint')
      return Promise.resolve()
    },
  }
}

export const apiClient: ApiClient = mode === 'mock' ? mockApiClient : createRestClient()
export const apiMode = mode
