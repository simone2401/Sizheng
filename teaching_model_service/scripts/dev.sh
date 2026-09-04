#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

resource_pid=""
model_pid=""
cleanup() {
  [[ -z "$resource_pid" ]] || kill "$resource_pid" 2>/dev/null || true
  [[ -z "$model_pid" ]] || kill "$model_pid" 2>/dev/null || true
  wait "$resource_pid" "$model_pid" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

uvicorn app.resource_api.main:app \
  --host "${RESOURCE_API_HOST:-127.0.0.1}" \
  --port "${RESOURCE_API_PORT:-8001}" &
resource_pid=$!

uvicorn app.model_api.main:app \
  --host "${MODEL_API_HOST:-127.0.0.1}" \
  --port "${MODEL_API_PORT:-8000}" &
model_pid=$!

printf 'Resource API: http://%s:%s\n' "${RESOURCE_API_HOST:-127.0.0.1}" "${RESOURCE_API_PORT:-8001}"
printf 'Model API:    http://%s:%s\n' "${MODEL_API_HOST:-127.0.0.1}" "${MODEL_API_PORT:-8000}"
printf 'Press Ctrl+C to stop both services.\n'
wait -n "$resource_pid" "$model_pid"
