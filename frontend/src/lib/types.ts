export type LlmProvider = 'ollama' | 'openai_compatible' | 'other'

export type RunPayload = {
  endpointUrl: string
  llmProvider: LlmProvider
  model: string
  apiKey?: string
  graphqlHeadersJson?: string
  rounds: number
  requestsPerNode: number
  notes?: string
}

export type RunState = {
  runId: string
  status: 'queued' | 'running' | 'done' | 'failed' | 'cancelled'
  progress: number
  startedAt?: string
  finishedAt?: string
  error?: string
}

export type LogsResponse = {
  lines: string[]
  nextCursor: number
}

export type ResultArtifact = { name: string; url: string }

export type ResultsResponse = {
  summary: string
  artifacts: ResultArtifact[]
  rawJson: Record<string, any>
}

export type ApiClient = {
  createRun: (payload: RunPayload) => Promise<{ runId: string }>
  getRun: (runId: string) => Promise<RunState>
  getLogs: (runId: string, cursor?: number) => Promise<LogsResponse>
  getResults: (runId: string) => Promise<ResultsResponse>
  cancelRun?: (runId: string) => Promise<void>
}
