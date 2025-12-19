# PrediQL Web (UI Prototype)

Frontend-only prototype for orchestrating PrediQL runs. Uses Next.js (App Router) + Tailwind and ships with a mock API so the UI is demo-able without any backend.

## Quick start

```bash
cd frontend
npm install
npm run dev
```

The app defaults to `NEXT_PUBLIC_API_MODE=mock`, which simulates run creation, status, live logs, and results.

## Mock API behavior
- States: queued → running → done over ~20–40s
- Logs emit every 0.5–1.5s
- Generates a fake results JSON (validQueriesFound, mutationsTried, potentialIssues)
- Cancel button marks a run as failed/cancelled (mock-only)

## Switching to a real backend (future)
Set env vars before `npm run dev` or `npm run build`:

```bash
export NEXT_PUBLIC_API_MODE=rest
export NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

Expected REST endpoints (not implemented in this prototype):
- `POST /api/runs` → `{ runId }`
- `GET /api/runs/:id` → `{ status, progress, startedAt, finishedAt, error? }`
- `GET /api/runs/:id/logs?cursor=n` → `{ lines, nextCursor }`
- `GET /api/runs/:id/results` → `{ summary, artifacts: [{name, url}], rawJson }`
- Optional future: `POST /api/runs/:id/cancel`

## Project structure
```
prediql-web/
  frontend/
    package.json
    next.config.js
    tailwind.config.ts
    src/
      app/
        page.tsx
        layout.tsx
        globals.css
      components/
        RunForm.tsx
        RunStatus.tsx
        LogViewer.tsx
        ResultsPanel.tsx
        HeaderBar.tsx
      lib/
        apiClient.ts
        mockApi.ts
        types.ts
        validators.ts
```

## Notes
- Tailwind is configured for the App Router under `src/`.
- All backend calls are funneled through `src/lib/apiClient.ts` for easy swapping of implementations.
- The UI includes validation for endpoint URL, headers JSON, and numeric params; Start Run is disabled until valid.
- Warning banner reminds users to only test endpoints they own or have permission to test.
