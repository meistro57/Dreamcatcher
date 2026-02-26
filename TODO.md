# TODO

## P0 - Fix before/with next deploy

- [ ] Fix frontend API and WebSocket base URLs in Docker Compose files.
  - [ ] `docker-compose.local.yml`: set `VITE_API_URL` to `http://localhost:8000/api` and `VITE_WS_URL` to `ws://localhost:8000/api/ws`.
  - [ ] `docker/docker-compose.yml`: set `VITE_API_URL` to `http://localhost:8000/api` and `VITE_WS_URL` to `ws://localhost:8000/api/ws`.
- [ ] Remove insecure auth defaults.
  - [ ] Require `SECRET_KEY` in runtime config; fail fast if missing.
  - [ ] Do not auto-create admin with default password.
  - [ ] Gate test-user seeding behind explicit development flag.
- [ ] Lock down CORS for credentialed requests.
  - [ ] Replace wildcard `allow_origins=["*"]` with explicit origin list from env.

## P1 - Reliability fixes

- [ ] Standardize health endpoint usage to `/api/health` across scripts and compose files.
- [ ] Update SQLAlchemy health probe to use `text("SELECT 1")`.
- [ ] Finish migration from `docker-compose` to `docker compose` in all scripts/docs.

## P2 - Follow-up

- [ ] Run full backend test suite in an environment with dependencies installed.
- [ ] Add CI checks for script linting and endpoint/path consistency.
