#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
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
BASE_URL="${PROJECT_DREAM_BASE_URL:-http://$HOST:$PORT}"
AUTH_HEADER="Authorization: Bearer $PROJECT_DREAM_API_TOKEN"

TMP_BODY="$(mktemp)"
trap 'rm -f "$TMP_BODY"' EXIT

request() {
  local method="$1"
  local url="$2"
  local data="${3:-}"
  local use_auth="${4:-0}"
  local -a curl_args

  curl_args=(--silent --show-error --output "$TMP_BODY" --write-out "%{http_code}" -X "$method")
  if [[ "$use_auth" == "1" ]]; then
    curl_args+=(-H "$AUTH_HEADER")
  fi
  if [[ -n "$data" ]]; then
    curl_args+=(-H "Content-Type: application/json" --data "$data")
  fi
  curl_args+=("$url")

  STATUS_CODE="$(curl "${curl_args[@]}")"
  BODY="$(cat "$TMP_BODY")"
}

assert_status() {
  local expected="$1"
  local label="$2"
  if [[ "$STATUS_CODE" != "$expected" ]]; then
    echo "[FAIL] $label expected=$expected actual=$STATUS_CODE body=$BODY"
    exit 1
  fi
  echo "[PASS] $label ($STATUS_CODE)"
}

request GET "$BASE_URL/health"
assert_status "200" "health check"

request GET "$BASE_URL/runs/latest"
assert_status "401" "unauthorized read endpoint"

SIM_PAYLOAD='{"seed":{"seed_id":"SEED-SMOKE-001","title":"smoke","summary":"smoke run","board_id":"B07","zone_id":"D"},"rounds":3}'
request POST "$BASE_URL/simulate" "$SIM_PAYLOAD" 1
assert_status "200" "authorized simulate"

if [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
  PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
else
  PYTHON_BIN="python3"
fi

RUN_ID="$("$PYTHON_BIN" -c 'import json,sys; print(json.loads(sys.argv[1])["run_id"])' "$BODY")"
if [[ -z "$RUN_ID" ]]; then
  echo "[FAIL] simulate response missing run_id: $BODY"
  exit 1
fi
echo "[PASS] simulate produced run_id=$RUN_ID"

request GET "$BASE_URL/runs/latest" "" 1
assert_status "200" "authorized read endpoint"
