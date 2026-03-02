#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="${ROOT_DIR}/docker-compose.local.yml"
ENV_FILE="${ROOT_DIR}/.env"

log() {
  printf "[start.sh] %s\n" "$1"
}

fail() {
  printf "[start.sh] ERROR: %s\n" "$1" >&2
  exit 1
}

append_if_missing() {
  local key="$1"
  local value="$2"
  if ! grep -q "^${key}=" "${ENV_FILE}"; then
    printf "%s=%s\n" "${key}" "${value}" >> "${ENV_FILE}"
  fi
}

ensure_env_file() {
  if [ -f "${ENV_FILE}" ]; then
    return
  fi

  if [ -f "${ROOT_DIR}/.env.local" ]; then
    cp "${ROOT_DIR}/.env.local" "${ENV_FILE}"
  elif [ -f "${ROOT_DIR}/.env.example" ]; then
    cp "${ROOT_DIR}/.env.example" "${ENV_FILE}"
  else
    touch "${ENV_FILE}"
  fi
}

ensure_env_defaults() {
  if ! grep -q '^SECRET_KEY=' "${ENV_FILE}"; then
    if command -v openssl >/dev/null 2>&1; then
      printf "SECRET_KEY=%s\n" "$(openssl rand -base64 32 | tr -d '\n')" >> "${ENV_FILE}"
    else
      printf "SECRET_KEY=%s\n" "$(date +%s)-dreamcatcher-dev-secret" >> "${ENV_FILE}"
    fi
  fi

  append_if_missing "CORS_ORIGINS" "[\"http://localhost:3000\",\"http://localhost:5173\"]"
  append_if_missing "DATABASE_URL" "postgresql://dreamcatcher:dreamcatcher_password@postgres:5432/dreamcatcher"
  append_if_missing "REDIS_URL" "redis://redis:6379"
  append_if_missing "ENVIRONMENT" "development"
  append_if_missing "DEBUG" "true"
  append_if_missing "DEFAULT_DEV_USER_EMAIL" "user@dreamcatcher.local"
  append_if_missing "DEFAULT_DEV_USER_USERNAME" "user"
  append_if_missing "DEFAULT_DEV_USER_PASSWORD" "password"
  append_if_missing "DEFAULT_DEV_USER_FULL_NAME" "Default User"
  append_if_missing "ENFORCE_DEFAULT_DEV_CREDENTIALS" "true"
  append_if_missing "ENABLE_SYSTEM_ACTIONS" "true"
  append_if_missing "SYSTEM_ACTION_USERS" "user,admin"
}

wait_for_http() {
  local url="$1"
  local attempts="${2:-40}"
  local sleep_s="${3:-3}"
  local i=1
  while [ "${i}" -le "${attempts}" ]; do
    if curl -fsS "${url}" >/dev/null 2>&1; then
      return 0
    fi
    sleep "${sleep_s}"
    i=$((i + 1))
  done
  return 1
}

main() {
  cd "${ROOT_DIR}"

  command -v docker >/dev/null 2>&1 || fail "docker command not found"
  docker compose version >/dev/null 2>&1 || fail "docker compose (v2 plugin) not available"
  docker info >/dev/null 2>&1 || fail "Docker daemon is not running"
  [ -f "${COMPOSE_FILE}" ] || fail "Missing ${COMPOSE_FILE}"

  log "Preparing environment"
  ensure_env_file
  ensure_env_defaults
  mkdir -p "${ROOT_DIR}/logs"

  log "Starting core services"
  docker compose -f "${COMPOSE_FILE}" up -d postgres redis

  log "Starting app services (build + up)"
  docker compose -f "${COMPOSE_FILE}" up -d --build backend frontend

  log "Bootstrapping database schema and auth seed"
  docker compose -f "${COMPOSE_FILE}" exec -T backend python -c \
    "from database.database import create_tables; from database.init_auth import init_auth_system; create_tables(); init_auth_system(); print('bootstrap complete')"

  log "Waiting for backend health endpoint"
  wait_for_http "http://localhost:8000/api/health" || fail "Backend health check timed out"

  log "Verifying auth schema and seeded login"
  docker compose -f "${COMPOSE_FILE}" exec -T backend python - <<'PY'
from database.database import get_db
from database.models import User
from services.auth_service import AuthService
import os

with get_db() as db:
    username = os.getenv("DEFAULT_DEV_USER_USERNAME", "user").lower()
    password = os.getenv("DEFAULT_DEV_USER_PASSWORD", "password")
    user = db.query(User).filter(User.username == username).first()
    assert user is not None, "Default dev user missing after bootstrap"
    auth = AuthService(os.getenv("SECRET_KEY"), db)
    assert auth.pwd_context.verify(password, user.password_hash), "Default dev password not synchronized"
    print("auth seed verified")
PY

  log "Waiting for frontend"
  wait_for_http "http://localhost:3000" 20 2 || fail "Frontend health check timed out"

  log "Running backend tests"
  docker compose -f "${COMPOSE_FILE}" exec -T backend pytest -q tests

  log "Running frontend tests"
  docker compose -f "${COMPOSE_FILE}" exec -T frontend npm test -- --run

  log "Done"
  log "Frontend: http://localhost:3000"
  log "Backend:  http://localhost:8000"
  log "API docs: http://localhost:8000/docs"
  log "Local login (dev seed):"
  log "  username: $(grep '^DEFAULT_DEV_USER_USERNAME=' "${ENV_FILE}" | tail -n1 | cut -d= -f2-)"
  log "  password: $(grep '^DEFAULT_DEV_USER_PASSWORD=' "${ENV_FILE}" | tail -n1 | cut -d= -f2-)"
  log "  email:    $(grep '^DEFAULT_DEV_USER_EMAIL=' "${ENV_FILE}" | tail -n1 | cut -d= -f2-)"
}

main "$@"
