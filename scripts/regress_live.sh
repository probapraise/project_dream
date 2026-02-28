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

SEEDS_DIR="${PROJECT_DREAM_LIVE_SEEDS_DIR:-examples/seeds/regression}"
PACKS_DIR="${PROJECT_DREAM_LIVE_PACKS_DIR:-packs}"
OUTPUT_DIR="${PROJECT_DREAM_LIVE_OUTPUT_DIR:-runs}"
ROUNDS="${PROJECT_DREAM_LIVE_ROUNDS:-3}"
MAX_SEEDS="${PROJECT_DREAM_LIVE_MAX_SEEDS:-2}"
METRIC_SET="${PROJECT_DREAM_LIVE_METRIC_SET:-v2}"
MIN_COMMUNITY_COVERAGE="${PROJECT_DREAM_LIVE_MIN_COMMUNITY_COVERAGE:-1}"
MIN_CONFLICT_FRAME_RUNS="${PROJECT_DREAM_LIVE_MIN_CONFLICT_FRAME_RUNS:-0}"
MIN_MODERATION_HOOK_RUNS="${PROJECT_DREAM_LIVE_MIN_MODERATION_HOOK_RUNS:-0}"
MIN_VALIDATION_WARNING_RUNS="${PROJECT_DREAM_LIVE_MIN_VALIDATION_WARNING_RUNS:-0}"
LLM_MODEL="${PROJECT_DREAM_LIVE_LLM_MODEL:-${PROJECT_DREAM_LLM_MODEL:-gemini-3.1-flash}}"
LLM_TIMEOUT_SEC="${PROJECT_DREAM_LIVE_LLM_TIMEOUT_SEC:-${PROJECT_DREAM_LLM_TIMEOUT_SEC:-60}}"
BASELINE_FILE="${PROJECT_DREAM_LIVE_BASELINE_FILE:-runs/regressions/regress-live-baseline.json}"
ALLOWED_RATE_DROP="${PROJECT_DREAM_LIVE_ALLOWED_RATE_DROP:-0.05}"
ALLOWED_COMMUNITY_DROP="${PROJECT_DREAM_LIVE_ALLOWED_COMMUNITY_DROP:-1}"
UPDATE_BASELINE="${PROJECT_DREAM_LIVE_UPDATE_BASELINE:-0}"

if [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
  PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
elif [[ -n "$GIT_COMMON_DIR" && -x "$GIT_COMMON_DIR/../.venv/bin/python" ]]; then
  PYTHON_BIN="$GIT_COMMON_DIR/../.venv/bin/python"
else
  PYTHON_BIN="python3"
fi

cd "$ROOT_DIR"
export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"
exec "$PYTHON_BIN" -m project_dream.cli regress-live \
  --seeds-dir "$SEEDS_DIR" \
  --packs-dir "$PACKS_DIR" \
  --output-dir "$OUTPUT_DIR" \
  --rounds "$ROUNDS" \
  --max-seeds "$MAX_SEEDS" \
  --metric-set "$METRIC_SET" \
  --min-community-coverage "$MIN_COMMUNITY_COVERAGE" \
  --min-conflict-frame-runs "$MIN_CONFLICT_FRAME_RUNS" \
  --min-moderation-hook-runs "$MIN_MODERATION_HOOK_RUNS" \
  --min-validation-warning-runs "$MIN_VALIDATION_WARNING_RUNS" \
  --llm-model "$LLM_MODEL" \
  --llm-timeout-sec "$LLM_TIMEOUT_SEC" \
  --baseline-file "$BASELINE_FILE" \
  --allowed-rate-drop "$ALLOWED_RATE_DROP" \
  --allowed-community-drop "$ALLOWED_COMMUNITY_DROP" \
  $([[ "$UPDATE_BASELINE" == "1" ]] && printf '%s' "--update-baseline")
