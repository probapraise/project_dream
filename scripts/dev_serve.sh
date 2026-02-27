#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GIT_COMMON_DIR="$(git -C "$ROOT_DIR" rev-parse --git-common-dir 2>/dev/null || true)"
ENV_FILE="${PROJECT_DREAM_ENV_FILE:-$ROOT_DIR/.env}"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

: "${PROJECT_DREAM_API_TOKEN:?PROJECT_DREAM_API_TOKEN is required (set it in .env or env)}"

HOST="${PROJECT_DREAM_HOST:-127.0.0.1}"
PORT="${PROJECT_DREAM_PORT:-8000}"
RUNS_DIR="${PROJECT_DREAM_RUNS_DIR:-runs}"
PACKS_DIR="${PROJECT_DREAM_PACKS_DIR:-packs}"

if [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
  PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
elif [[ -n "$GIT_COMMON_DIR" && -x "$GIT_COMMON_DIR/../.venv/bin/python" ]]; then
  PYTHON_BIN="$GIT_COMMON_DIR/../.venv/bin/python"
else
  PYTHON_BIN="python3"
fi

cd "$ROOT_DIR"
export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"
exec "$PYTHON_BIN" -m project_dream.cli serve \
  --host "$HOST" \
  --port "$PORT" \
  --runs-dir "$RUNS_DIR" \
  --packs-dir "$PACKS_DIR" \
  --api-token "$PROJECT_DREAM_API_TOKEN"
