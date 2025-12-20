# PrediQL Web

Next.js + FastAPI + Ollama stack for running PrediQL-style GraphQL scans. The frontend stays static (Cloudflare Pages), while the backend + Ollama run via Docker Compose on a VPS.

Research paper (for reference): https://arxiv.org/pdf/2510.10407

## Frontend (static)
- Location: `frontend/`
- Default mode: `NEXT_PUBLIC_API_MODE=mock` (no backend needed)
- REST mode: set `NEXT_PUBLIC_API_MODE=rest` and `NEXT_PUBLIC_BACKEND_URL=https://your-backend.example.com`
- Local dev:
  ```bash
  cd frontend
  npm install
  npm run dev
  ```
- Static build (Cloudflare Pages): `npm run build` (exports to `frontend/out`)

## Backend (FastAPI + Ollama / API LLMs)
- Location: `backend/app`
- Endpoints:
  - `POST /api/runs` → create run, returns `{ runId, status }`
  - `GET /api/runs/{runId}` → status `{ runId, status, progress{pct,stage,detail}, startedAt, finishedAt, error }`
  - `GET /api/runs/{runId}/logs?cursor=n` → `{ lines, nextCursor }`
  - `GET /api/runs/{runId}/results` → `{ summary, artifacts[{name,url}], rawJson }`
  - `GET /api/runs/{runId}/artifacts/{filename}` → serve run artifacts
  - `POST /api/runs/{runId}/cancel` → request cancellation
- Runner behavior (MVP): introspects the GraphQL endpoint, summarizes schema counts, asks the configured LLM for candidate queries, optionally executes them, saves `raw_results.json`, `summary.json`, and `logs.txt` under `backend/runs/{runId}/`.
- LLM providers: `ollama` (default, local), `openai_compatible` (requires user API key), `gemini` (requires user API key).

## Docker Compose (backend + Ollama)
- File: `docker-compose.yml`
- Services:
  - `backend` (FastAPI)
  - `ollama` (llama3 model)
- Volumes: `backend_runs` for artifacts, `ollama` for model cache.
- One-time model pull: `docker compose exec ollama ollama pull llama3`
- Local dev start:
  ```bash
  docker compose up --build
  # backend on http://localhost:8000, ollama on 11434 (keep private in prod)
  ```
- If you only use API providers (OpenAI-compatible or Gemini), you can run just the backend service without the Ollama container; ensure users provide `apiKey` in the UI.

### Backend env vars
- `OLLAMA_BASE_URL` (default `http://ollama:11434`)
- `OPENAI_BASE_URL` (default `https://api.openai.com/v1`)
- `GEMINI_BASE_URL` (default `https://generativelanguage.googleapis.com`)
- `RUNS_DIR` (default `/app/runs`)
- `CORS_ORIGINS` (comma-separated, default `http://localhost:3000`)
- `MAX_ROUNDS` (default 5)
- `MAX_REQUESTS_PER_NODE` (default 5)

## Deploying
- Frontend (Cloudflare Pages):
  - Build command: `npm ci && npm run build`
  - Output directory: `frontend/out` (project root `frontend`)
  - Env: `NEXT_PUBLIC_API_MODE=rest`, `NEXT_PUBLIC_BACKEND_URL=https://your-backend-domain`
- Backend (VPS with Docker Compose):
  - Copy repo, set envs, run `docker compose up -d --build`
  - Keep Ollama port firewalled; only expose backend 8000

## Security notes
- Validate URLs (http/https only) and header JSON; limits for rounds/requests enforced by envs.
- API keys are never persisted to disk.
- Keep Ollama service behind a firewall or localhost-only.

## Project structure
```
backend/
  app/
    main.py
    api/runs.py
    core/{runner.py,ollama_client.py,graphql_client.py,storage.py,models.py,utils.py}
  Dockerfile
  requirements.txt
frontend/
  package.json
  next.config.js
  tailwind.config.ts
  src/app/{page.tsx,layout.tsx,globals.css}
  src/components/{RunForm,RunStatus,LogViewer,ResultsPanel,HeaderBar}.tsx
  src/lib/{apiClient,mockApi,types,validators}.ts
```
