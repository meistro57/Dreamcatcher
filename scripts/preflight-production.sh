#!/usr/bin/env bash

set -euo pipefail

ENV_FILE="${1:-.env}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "[preflight] Missing env file: $ENV_FILE" >&2
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "[preflight] docker is required" >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "[preflight] docker compose plugin is required" >&2
  exit 1
fi

set -a
# shellcheck source=/dev/null
source "$ENV_FILE"
set +a

is_placeholder() {
  local value="${1:-}"
  local normalized
  normalized="$(echo "$value" | tr '[:upper:]' '[:lower:]' | xargs)"

  [[ -z "$normalized" ]] && return 0
  [[ "$normalized" == "changeme" ]] && return 0
  [[ "$normalized" == *"your_"* ]] && return 0
  [[ "$normalized" == *"_here"* ]] && return 0
  [[ "$normalized" == *"replace_with"* ]] && return 0
  return 1
}

require_value() {
  local key="$1"
  local value="${!key:-}"
  if is_placeholder "$value"; then
    echo "[preflight] $key is missing or placeholder in $ENV_FILE" >&2
    exit 1
  fi
}

require_value "ENVIRONMENT"
if [[ "${ENVIRONMENT}" != "production" ]]; then
  echo "[preflight] ENVIRONMENT must be 'production' (got '${ENVIRONMENT}')" >&2
  exit 1
fi

require_value "FORCE_HTTPS"
if [[ "${FORCE_HTTPS}" != "true" ]]; then
  echo "[preflight] FORCE_HTTPS must be true in production" >&2
  exit 1
fi

require_value "SECRET_KEY"
if [[ "${#SECRET_KEY}" -lt 32 ]]; then
  echo "[preflight] SECRET_KEY must be at least 32 characters" >&2
  exit 1
fi

require_value "DB_PASSWORD"
require_value "DOMAIN"
require_value "SUBDOMAIN"
require_value "FULL_DOMAIN"
require_value "CORS_ORIGINS"

if [[ "${CORS_ORIGINS}" != *"https://"* ]]; then
  echo "[preflight] CORS_ORIGINS must include https origins in production" >&2
  exit 1
fi

if is_placeholder "${ANTHROPIC_API_KEY:-}" \
  && is_placeholder "${OPENAI_API_KEY:-}" \
  && is_placeholder "${OPENROUTER_API_KEY:-}"; then
  echo "[preflight] Set at least one AI key: ANTHROPIC_API_KEY, OPENAI_API_KEY, or OPENROUTER_API_KEY" >&2
  exit 1
fi

echo "[preflight] Production checks passed for $ENV_FILE"
