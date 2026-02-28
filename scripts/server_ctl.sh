#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${PROJECT_DREAM_ENV_FILE:-$ROOT_DIR/.env}"
RUNTIME_DIR="${PROJECT_DREAM_RUNTIME_DIR:-$ROOT_DIR/.runtime}"
PID_FILE="${PROJECT_DREAM_SERVER_PID_FILE:-$RUNTIME_DIR/project_dream_server.pid}"
LOG_FILE="${PROJECT_DREAM_SERVER_LOG_FILE:-$RUNTIME_DIR/project_dream_server.log}"
STARTUP_WAIT_SEC="${PROJECT_DREAM_SERVER_STARTUP_WAIT_SEC:-1}"
TAIL_LINES="${PROJECT_DREAM_LOG_TAIL_LINES:-120}"

mkdir -p "$RUNTIME_DIR"

usage() {
  cat <<'EOF'
Usage: scripts/server_ctl.sh <command>

Commands:
  start      Start server in background
  stop       Stop server
  status     Show running status
  restart    Restart server
  logs       Show recent logs
  logs -f    Follow logs
  check      Run smoke checks (starts server if not running)
EOF
}

read_pid() {
  if [[ -f "$PID_FILE" ]]; then
    cat "$PID_FILE"
  fi
}

is_running() {
  local pid
  pid="$(read_pid || true)"
  if [[ -z "$pid" ]]; then
    return 1
  fi
  kill -0 "$pid" 2>/dev/null
}

cleanup_stale_pid() {
  if [[ -f "$PID_FILE" ]] && ! is_running; then
    rm -f "$PID_FILE"
  fi
}

start_server() {
  cleanup_stale_pid
  if is_running; then
    echo "[INFO] server already running (pid=$(read_pid))"
    return 0
  fi

  echo "[INFO] starting server..."
  PROJECT_DREAM_ENV_FILE="$ENV_FILE" "$ROOT_DIR/scripts/dev_serve.sh" >>"$LOG_FILE" 2>&1 &
  local pid=$!
  echo "$pid" > "$PID_FILE"

  sleep "$STARTUP_WAIT_SEC"
  if ! kill -0 "$pid" 2>/dev/null; then
    echo "[FAIL] server exited during startup. Recent logs:"
    tail -n 40 "$LOG_FILE" || true
    rm -f "$PID_FILE"
    return 1
  fi

  echo "[OK] server started (pid=$pid)"
  echo "[INFO] log file: $LOG_FILE"
}

stop_server() {
  cleanup_stale_pid
  if ! is_running; then
    echo "[INFO] server is not running"
    return 0
  fi

  local pid
  pid="$(read_pid)"
  echo "[INFO] stopping server (pid=$pid)..."
  kill "$pid" 2>/dev/null || true

  local i
  for i in {1..20}; do
    if ! kill -0 "$pid" 2>/dev/null; then
      break
    fi
    sleep 0.25
  done

  if kill -0 "$pid" 2>/dev/null; then
    echo "[WARN] graceful stop timeout, forcing kill"
    kill -9 "$pid" 2>/dev/null || true
  fi

  rm -f "$PID_FILE"
  echo "[OK] server stopped"
}

status_server() {
  cleanup_stale_pid
  if is_running; then
    echo "[OK] running (pid=$(read_pid))"
    echo "[INFO] log file: $LOG_FILE"
    return 0
  fi
  echo "[INFO] stopped"
  return 1
}

show_logs() {
  local mode="${1:-}"
  if [[ ! -f "$LOG_FILE" ]]; then
    echo "[INFO] no log file found: $LOG_FILE"
    return 1
  fi

  if [[ "$mode" == "-f" || "$mode" == "--follow" ]]; then
    tail -n "$TAIL_LINES" -f "$LOG_FILE"
    return 0
  fi
  tail -n "$TAIL_LINES" "$LOG_FILE"
}

check_server() {
  cleanup_stale_pid
  if ! is_running; then
    echo "[INFO] server not running, starting first..."
    start_server
  fi
  PROJECT_DREAM_ENV_FILE="$ENV_FILE" "$ROOT_DIR/scripts/smoke_api.sh"
}

cmd="${1:-}"
case "$cmd" in
  start)
    start_server
    ;;
  stop)
    stop_server
    ;;
  status)
    status_server
    ;;
  restart)
    stop_server
    start_server
    ;;
  logs)
    show_logs "${2:-}"
    ;;
  check)
    check_server
    ;;
  ""|-h|--help|help)
    usage
    ;;
  *)
    echo "[FAIL] unknown command: $cmd"
    usage
    exit 2
    ;;
esac
