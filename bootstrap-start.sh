#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="${ROOT_DIR}/docker-compose.local.yml"
ENV_FILE="${ROOT_DIR}/.env"

cd "${ROOT_DIR}"

echo "[1/7] Syncing repository..."
if [ -n "$(git status --porcelain)" ]; then
  echo "Working tree has local changes. Skipping git pull to avoid conflicts."
  echo "Commit/stash changes, then run: git pull --ff-only"
else
  git pull --ff-only
fi

echo "[2/7] Preparing environment file..."
if [ ! -f "${ENV_FILE}" ]; then
  if [ -f "${ROOT_DIR}/.env.local" ]; then
    cp "${ROOT_DIR}/.env.local" "${ENV_FILE}"
  elif [ -f "${ROOT_DIR}/.env.example" ]; then
    cp "${ROOT_DIR}/.env.example" "${ENV_FILE}"
  else
    touch "${ENV_FILE}"
  fi
fi

append_if_missing() {
  local key="$1"
  local value="$2"
  if ! grep -q "^${key}=" "${ENV_FILE}"; then
    printf "%s=%s\n" "${key}" "${value}" >> "${ENV_FILE}"
  fi
}

if ! grep -q '^SECRET_KEY=' "${ENV_FILE}"; then
  if command -v openssl >/dev/null 2>&1; then
    SECRET_KEY_VALUE="$(openssl rand -base64 32 | tr -d '\n')"
  else
    SECRET_KEY_VALUE="$(date +%s)-dreamcatcher-dev-secret"
  fi
  printf "SECRET_KEY=%s\n" "${SECRET_KEY_VALUE}" >> "${ENV_FILE}"
fi

append_if_missing "CORS_ORIGINS" "[\"http://localhost:3000\",\"http://localhost:5173\"]"
append_if_missing "DATABASE_URL" "postgresql://dreamcatcher:dreamcatcher_password@postgres:5432/dreamcatcher"
append_if_missing "REDIS_URL" "redis://redis:6379"
append_if_missing "ENVIRONMENT" "development"
append_if_missing "DEBUG" "true"

if grep -q '^ANTHROPIC_API_KEY=your_' "${ENV_FILE}" || grep -q '^OPENAI_API_KEY=your_' "${ENV_FILE}"; then
  echo "Warning: API keys are placeholders in .env; AI features will fail until you set real keys."
fi

echo "[3/7] Checking required tools..."
docker --version >/dev/null
docker compose version >/dev/null

echo "[4/7] Pulling base images..."
docker compose -f "${COMPOSE_FILE}" pull postgres redis

echo "[5/7] Building application images (installs backend/frontend deps)..."
docker compose -f "${COMPOSE_FILE}" build backend frontend

echo "[6/7] Starting services in background..."
docker compose -f "${COMPOSE_FILE}" up -d postgres redis backend frontend

echo "[7/7] Waiting for services..."
sleep 8
docker compose -f "${COMPOSE_FILE}" ps

echo
echo "Dreamcatcher is running:"
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo
echo "Logs:  docker compose -f docker-compose.local.yml logs -f"
echo "Stop:  docker compose -f docker-compose.local.yml down"
