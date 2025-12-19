import { ApiClient, LogsResponse, ResultsResponse, RunPayload, RunState } from './types'

const simulations = new Map<string, Simulation>()

const randomBetween = (min: number, max: number) => Math.random() * (max - min) + min

function genId() {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    // @ts-ignore
    return crypto.randomUUID()
  }
  return Math.random().toString(36).slice(2)
}

type Simulation = {
  runId: string
  payload: RunPayload
  status: RunState['status']
  progress: number
  startedAt?: string
  finishedAt?: string
  error?: string
  logs: string[]
  results?: ResultsResponse
  logTimer?: ReturnType<typeof setInterval>
  progressTimer?: ReturnType<typeof setInterval>
  completionTimer?: ReturnType<typeof setTimeout>
}

function scheduleSimulation(sim: Simulation) {
  sim.startedAt = new Date().toISOString()
  sim.status = 'running'
  sim.logs.push('Run started: warming up LLM and probing schema...')

  const durationMs = randomBetween(20000, 40000)
  const started = Date.now()

  sim.progressTimer = setInterval(() => {
    const elapsed = Date.now() - started
    const pct = Math.min(0.96, elapsed / durationMs)
    sim.progress = pct
  }, 1000)

  sim.logTimer = setInterval(() => {
    const messages = [
      'Analyzing schema nodes...',
      'Generating exploratory query...',
      'Attempting mutation fuzzing...',
      'Synthesizing auth bypass patterns...',
      'Scoring potential issue severity...',
      'LLM thinking about next path...',
      'Batching follow-up requests...',
    ]
    const msg = messages[Math.floor(Math.random() * messages.length)]
    sim.logs.push(`${new Date().toLocaleTimeString()} | ${msg}`)
  }, randomBetween(500, 1500))

  sim.completionTimer = setTimeout(() => {
    sim.status = 'done'
    sim.progress = 1
    sim.finishedAt = new Date().toISOString()
    sim.logs.push('Run finished: summarizing findings...')
    const rawJson = {
      endpoint: sim.payload.endpointUrl,
      model: sim.payload.model,
      rounds: sim.payload.rounds,
      requestsPerNode: sim.payload.requestsPerNode,
      validQueriesFound: Math.floor(randomBetween(3, 12)),
      mutationsTried: Math.floor(randomBetween(1, 6)),
      potentialIssues: [
        'Exposed introspection enabled',
        'Potential IDOR vector on user node',
      ],
    }
    sim.results = {
      summary: {
        endpoint: sim.payload.endpointUrl,
        candidates: rawJson.validQueriesFound,
        executions: rawJson.mutationsTried,
        counts: {
          types: 0,
          queries: 0,
          mutations: rawJson.mutationsTried,
        },
        text: `Scanned ${sim.payload.endpointUrl}. Found ${rawJson.validQueriesFound} plausible queries and ${rawJson.potentialIssues.length} potential issues.`,
      },
      artifacts: [
        { name: 'summary.json', url: '#' },
        { name: 'raw_results.json', url: '#' },
      ],
      rawJson,
    }
    clearInterval(sim.logTimer)
    clearInterval(sim.progressTimer)
  }, durationMs)
}

function ensureSimulation(runId: string): Simulation {
  const sim = simulations.get(runId)
  if (!sim) {
    throw new Error('Run not found')
  }
  return sim
}

export const mockApiClient: ApiClient = {
  async createRun(payload) {
    const runId = genId()
    const sim: Simulation = {
      runId,
      payload,
      status: 'queued',
      progress: 0,
      logs: [`Queued run for ${payload.endpointUrl}`],
    }
    simulations.set(runId, sim)
    // Slight delay before starting
    setTimeout(() => scheduleSimulation(sim), 800)
    return { runId }
  },

  async getRun(runId) {
    const sim = ensureSimulation(runId)
    return {
      runId: sim.runId,
      status: sim.status,
      progress: { pct: sim.progress, stage: sim.status },
      startedAt: sim.startedAt,
      finishedAt: sim.finishedAt,
      error: sim.error,
    }
  },

  async getLogs(runId, cursor = 0): Promise<LogsResponse> {
    const sim = ensureSimulation(runId)
    const lines = sim.logs.slice(cursor)
    const nextCursor = cursor + lines.length
    return { lines, nextCursor }
  },

  async getResults(runId): Promise<ResultsResponse> {
    const sim = ensureSimulation(runId)
    if (sim.status !== 'done' || !sim.results) {
      throw new Error('Results not ready yet')
    }
    return sim.results
  },

  async cancelRun(runId) {
    const sim = ensureSimulation(runId)
    sim.status = 'failed'
    sim.error = 'Cancelled by user'
    sim.progress = 0
    sim.finishedAt = new Date().toISOString()
    sim.logs.push('Run cancelled by user.')
    clearInterval(sim.logTimer)
    clearInterval(sim.progressTimer)
    clearTimeout(sim.completionTimer)
  },
}
