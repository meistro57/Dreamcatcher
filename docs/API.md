# Dreamcatcher API Reference (Code-Verified)

Last verified: 2026-03-02

Canonical implementation map: `docs/SOURCE_OF_TRUTH.md`

## Base URL

- Local backend: `http://localhost:8000`
- API prefix: `/api`
- OpenAPI docs: `/docs`

## Auth Model

- Bearer JWT via `Authorization: Bearer <token>`.
- Public endpoints:
  - `GET /`
  - `GET /api/status`
  - `GET /api/health`
  - `GET /api/auth/health`
  - `POST /api/auth/register`
  - `POST /api/auth/login`
  - `POST /api/auth/refresh`
- Most remaining endpoints require auth.

## Endpoint Matrix

### Core

- `GET /api/health` (public)
- `GET /api/status` (public)
- `WS /api/ws` (public websocket endpoint)

### Authentication

- `POST /api/auth/register` (public)
- `POST /api/auth/login` (public)
- `POST /api/auth/refresh` (public)
- `POST /api/auth/logout` (auth)
- `POST /api/auth/logout-all` (auth)
- `GET /api/auth/me` (auth)
- `POST /api/auth/change-password` (auth)
- `POST /api/auth/verify-email/{token}` (public)
- `GET /api/auth/users` (auth + permission `user.read`)
- `GET /api/auth/users/search` (auth + permission `user.read`)
- `POST /api/auth/users/{user_id}/deactivate` (auth + permission `user.update`)
- `POST /api/auth/users/{user_id}/activate` (auth + permission `user.update`)
- `POST /api/auth/users/{user_id}/unlock` (auth + permission `user.update`)
- `POST /api/auth/users/{user_id}/reset-password` (auth + permission `user.update`)
- `POST /api/auth/cleanup-sessions` (auth + role `admin`)
- `GET /api/auth/health` (public)

### Capture

- `POST /api/capture/voice` (auth, multipart)
- `POST /api/capture/text` (auth, JSON)
- `POST /api/capture/dream` (auth, form)

### Ideas

- `GET /api/ideas` (public in current implementation)
- `GET /api/ideas/{idea_id}` (public in current implementation)
- `PUT /api/ideas/{idea_id}` (public in current implementation)
- `DELETE /api/ideas/{idea_id}` (public in current implementation)
- `POST /api/ideas/{idea_id}/archive` (public in current implementation)
- `POST /api/ideas/{idea_id}/expand` (public in current implementation)
- `GET /api/ideas/{idea_id}/visuals` (public in current implementation)
- `GET /api/ideas/{idea_id}/expansions` (public in current implementation)
- `GET /api/ideas/{idea_id}/related` (auth)
- `POST /api/ideas/{idea_id}/generate_embedding` (auth)

### Search and Embeddings

- `GET /api/search/semantic` (auth)
- `POST /api/embeddings/batch_update` (auth)
- `GET /api/embeddings/stats` (auth)
- `GET /api/logs/search/semantic` (auth)
- `POST /api/logs/embeddings/batch_update` (auth)
- `GET /api/logs/embeddings/stats` (auth)

### Proposals

- `GET /api/proposals` (public in current implementation)
- `POST /api/proposals/{proposal_id}/approve` (public in current implementation)

### Agents and Observability

- `GET /api/agents/status` (public in current implementation)
- `POST /api/agents/{agent_id}/message` (public in current implementation)
- `GET /api/agents/{agent_id}/logs` (public in current implementation)
- `GET /api/logs` (auth)
- `GET /api/metrics` (public in current implementation)
- `GET /api/errors` (public in current implementation)
- `GET /api/stats` (public in current implementation)

### Settings and System Actions

- `GET /api/settings/api-keys/status` (auth)
- `POST /api/settings/api-keys` (auth)
- `GET /api/settings/ai-models` (auth)
- `POST /api/settings/ai-model` (auth)
- `GET /api/system/actions` (auth)
- `GET /api/system/actions/history` (auth + system-action permission)
- `POST /api/system/actions/{action}` (auth + system-action permission)

### Evolution

- `GET /api/evolution/status`
- `POST /api/evolution/cycle`
- `POST /api/evolution/force`
- `POST /api/evolution/schedule`
- `GET /api/evolution/history`
- `POST /api/evolution/rollback`
- `POST /api/evolution/config`
- `GET /api/evolution/trends`
- `POST /api/evolution/emergency-stop`
- `GET /api/evolution/health`
- `POST /api/evolution/analyze`
- `GET /api/evolution/agents/performance`
- `GET /api/evolution/opportunities`
- `POST /api/evolution/opportunities/{opportunity_id}/apply`
- `GET /api/evolution/backups`
- `POST /api/evolution/test-improvement`

### Scheduler

- `GET /api/scheduler/status`
- `POST /api/scheduler/start`
- `POST /api/scheduler/stop`
- `POST /api/scheduler/config`
- `POST /api/scheduler/force-evolution`
- `GET /api/scheduler/trends`
- `GET /api/scheduler/health`
- `GET /api/scheduler/stats`
- `POST /api/scheduler/reset-stats`
- `POST /api/scheduler/emergency-stop`
- `GET /api/scheduler/next-evolution`
- `POST /api/scheduler/test-health-check`
- `GET /api/scheduler/logs`

## Frontend Contract Note

Current frontend client still defines `POST /ideas`, but backend currently has no `POST /api/ideas` route.

## Security Note

Some non-auth routes above are currently public by implementation. Keep this doc aligned with code until route protection is tightened.
