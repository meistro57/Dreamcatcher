# Dreamcatcher Source of Truth (Code-Verified)

Last verified: 2026-03-02

This document summarizes what the app *actually does today* based on code under `backend/`, `frontend/`, and startup/deploy scripts.

## Runtime Stack

- Backend: FastAPI app in `backend/main.py` with API routers mounted at `/api`.
- Database: SQLAlchemy models in `backend/database/models.py`.
- Realtime: WebSocket endpoint at `/api/ws`.
- Frontend: React + TypeScript + Vite (`frontend/src/*`).
- Dev orchestration: Docker Compose local stack (`docker-compose.local.yml`).

## Entrypoints and Startup Paths

- Backend app entrypoint: `backend/main.py` (`app = FastAPI(...)`, `uvicorn.run("main:app", ...)`).
- Docker local startup script: `start-local.sh`.
- Native startup script: `start-native.sh`.
- Local compose file used by scripts: `docker-compose.local.yml`.
- Production compose file: `docker/docker-compose.prod.yml`.

## API Composition

- Main routers mounted in `backend/main.py`:
  - `app.include_router(router, prefix="/api")` from `backend/api/__init__.py`
  - `app.include_router(auth_router, prefix="/api")` from `backend/api/auth_routes.py`
- Base API router is defined in `backend/api/routes.py`.
- Optional routers are included by `backend/api/__init__.py`:
  - `/evolution/*` (`backend/api/evolution.py`)
  - `/scheduler/*` (`backend/api/scheduler.py`)

## Authentication and Access Control

- Auth endpoints live under `/api/auth/*` in `backend/api/auth_routes.py`.
- JWT auth is implemented by `AuthService` in `backend/services/auth_service.py`.
- Protected endpoints in `routes.py` are those using `current_user: User = Depends(get_current_user)`.
- Admin/permission checks are implemented with:
  - `require_permission(...)`
  - `require_role(...)`

## Implemented Core API Endpoints

From `backend/api/routes.py`:

- Health and system:
  - `GET /api/health`
  - `GET /api/system/actions`
  - `GET /api/system/actions/history`
  - `POST /api/system/actions/{action}`
  - `GET /api/settings/api-keys/status`
  - `GET /api/settings/ai-models`
  - `POST /api/settings/ai-model`
  - `POST /api/settings/api-keys`
- Capture:
  - `POST /api/capture/voice`
  - `POST /api/capture/text`
  - `POST /api/capture/dream`
- Ideas:
  - `POST /api/ideas`
  - `GET /api/ideas`
  - `GET /api/ideas/{idea_id}`
  - `PUT /api/ideas/{idea_id}`
  - `DELETE /api/ideas/{idea_id}`
  - `POST /api/ideas/{idea_id}/archive`
  - `POST /api/ideas/{idea_id}/expand`
  - `GET /api/ideas/{idea_id}/visuals`
  - `GET /api/ideas/{idea_id}/expansions`
  - `GET /api/ideas/{idea_id}/related`
  - `POST /api/ideas/{idea_id}/generate_embedding`
- Semantic search and embeddings:
  - `GET /api/search/semantic`
  - `POST /api/embeddings/batch_update`
  - `GET /api/embeddings/stats`
  - `GET /api/logs/search/semantic`
  - `POST /api/logs/embeddings/batch_update`
  - `GET /api/logs/embeddings/stats`
- Proposals:
  - `GET /api/proposals`
  - `POST /api/proposals/{proposal_id}/approve`
- Agents and observability:
  - `GET /api/agents/status`
  - `POST /api/agents/{agent_id}/message`
  - `GET /api/agents/{agent_id}/logs`
  - `GET /api/logs`
  - `GET /api/metrics`
  - `GET /api/errors`
  - `GET /api/stats`
- Realtime:
  - `WS /api/ws`

From `backend/api/auth_routes.py`:

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `POST /api/auth/logout`
- `POST /api/auth/logout-all`
- `GET /api/auth/me`
- `POST /api/auth/change-password`
- `POST /api/auth/verify-email/{token}`
- `GET /api/auth/users`
- `GET /api/auth/users/search`
- `POST /api/auth/users/{user_id}/deactivate`
- `POST /api/auth/users/{user_id}/activate`
- `POST /api/auth/users/{user_id}/unlock`
- `POST /api/auth/users/{user_id}/reset-password`
- `POST /api/auth/cleanup-sessions`
- `GET /api/auth/health`

## Agent System Actually Wired

Always registered in `backend/api/routes.py`:

- `listener` (`AgentListener`)
- `classifier` (`AgentClassifier`)
- `semantic` (`SemanticAgent`)

Attempted optional registration (warning on failure):

- `expander`, `proposer`, `reviewer`, `visualizer`, `meta`

Pipeline behavior in code:

- Capture endpoints call `listener_agent.handle_message(...)`.
- Listener stores idea and triggers classifier via agent messaging.
- Classifier may trigger expander if score thresholds are met.
- Expander may trigger visualizer.
- Visualizer may trigger proposer.

## Database Model Surface

Primary entities in `backend/database/models.py`:

- Auth/user: `User`, `Role`, `UserSession`, `user_roles`
- Ideas: `Idea`, `Tag`, `idea_tags`, `idea_relationships`
- Processing outputs: `IdeaExpansion`, `IdeaVisual`, `Proposal`, `ProposalTask`
- Agent/runtime telemetry: `Agent`, `AgentLog`, `SystemMetrics`, `ScheduledTask`

## Environment Variables Used in Code

Observed via `os.getenv(...)` across Python code:

- Core runtime/security:
  - `SECRET_KEY`, `CORS_ORIGINS`, `ENVIRONMENT`, `FORCE_HTTPS`, `DEBUG`
- Data services:
  - `DATABASE_URL`, `REDIS_URL`
- AI providers:
  - `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `OPENROUTER_API_KEY`, `DEFAULT_AI_MODEL`
- ComfyUI:
  - `COMFYUI_URL`, `COMFYUI_ENABLED`, `COMFYUI_TIMEOUT`, `COMFYUI_STORAGE_PATH`, `COMFYUI_OUTPUT_DIR`
- Dev/admin/system actions:
  - `ENABLE_SYSTEM_ACTIONS`, `SYSTEM_ACTION_USERS`, `SYSTEM_ACTION_AUDIT_FILE`
  - `DEFAULT_DEV_USER_EMAIL`, `DEFAULT_DEV_USER_USERNAME`, `DEFAULT_DEV_USER_PASSWORD`, `DEFAULT_DEV_USER_FULL_NAME`
  - `DISABLE_DEFAULT_DEV_USER`
  - `IDEA_PROCESSING_TIMEOUT_MINUTES`
- Testing:
  - `TEST_DATABASE_URL`

Frontend env vars in use:

- `VITE_API_URL`
- `VITE_WS_URL`

## Frontend Integration Reality

- API base URL resolution: `frontend/src/utils/api.ts`
  - Uses `VITE_API_URL`, else `${window.location.origin}/api`, else `http://localhost:8000/api`.
- WebSocket URL resolution: `frontend/src/stores/webSocketStore.ts`
  - Uses `VITE_WS_URL`, else protocol-relative `/api/ws`, else `ws://localhost:8000/api/ws`.
- App routes are defined in `frontend/src/App.tsx`.

## Notable Code/Contract Mismatches To Track

- No high-priority contract drifts from the last reconciliation pass (2026-03-02).
- Continue monitoring optional/legacy code paths in agent and scheduler modules for older field/signature assumptions.

## Recommended Baseline for Ongoing Work

When docs conflict, trust these files first:

1. `backend/main.py`
2. `backend/api/routes.py` + `backend/api/auth_routes.py`
3. `backend/database/models.py` + `backend/database/crud.py`
4. `docker-compose.local.yml` + startup scripts
5. `frontend/src/utils/api.ts` + `frontend/src/stores/webSocketStore.ts`
