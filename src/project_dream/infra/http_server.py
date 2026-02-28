import json
import time
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from project_dream.infra.web_api import ProjectDreamAPI


def _json_bytes(payload: dict) -> bytes:
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


def create_server(
    api: ProjectDreamAPI,
    host: str = "127.0.0.1",
    port: int = 8000,
    api_token: str = "",
    request_logger: Callable[[dict], None] | None = None,
) -> ThreadingHTTPServer:
    if not api_token:
        raise ValueError("api_token must be non-empty")

    class RequestHandler(BaseHTTPRequestHandler):
        def _send(self, status: int, payload: dict) -> None:
            self._response_status = status
            body = _json_bytes(payload)
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _emit_request_log(self, method: str, path: str, auth_ok: bool, started_at: float) -> None:
            if request_logger is None:
                return

            status = self._response_status if self._response_status is not None else 500
            event = "http_auth_failure" if status == 401 and not auth_ok else "http_request"
            entry = {
                "event": event,
                "method": method,
                "path": path,
                "status": status,
                "latency_ms": int((time.perf_counter() - started_at) * 1000),
                "auth_ok": bool(auth_ok),
            }
            try:
                request_logger(entry)
            except Exception:  # pragma: no cover - logging must not break request flow
                pass

        def _is_authorized(self, path: str) -> bool:
            if path == "/health":
                return True
            auth_header = self.headers.get("Authorization", "")
            bearer_prefix = "Bearer "
            if not auth_header.startswith(bearer_prefix):
                return False
            return auth_header[len(bearer_prefix) :].strip() == api_token

        def _read_json(self) -> dict:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length) if length > 0 else b"{}"
            return json.loads(raw.decode("utf-8"))

        def do_GET(self) -> None:  # noqa: N802
            started_at = time.perf_counter()
            self._response_status = None
            parsed = urlparse(self.path)
            path = parsed.path
            auth_ok = False
            try:
                query = parse_qs(parsed.query)

                auth_ok = self._is_authorized(path)
                if not auth_ok:
                    self._send(401, {"error": "unauthorized"})
                    return

                if path == "/health":
                    self._send(200, api.health())
                    return

                if path == "/runs/latest":
                    self._send(200, api.latest_run())
                    return

                if path == "/runs":
                    limit_raw = query.get("limit", [None])[0]
                    offset_raw = query.get("offset", [None])[0]
                    limit = 20 if limit_raw in (None, "") else int(limit_raw)
                    offset = 0 if offset_raw in (None, "") else int(offset_raw)
                    seed_id = query.get("seed_id", [None])[0] or None
                    board_id = query.get("board_id", [None])[0] or None
                    status_filter = query.get("status", [None])[0] or None
                    self._send(
                        200,
                        api.list_runs(
                            limit=limit,
                            offset=offset,
                            seed_id=seed_id,
                            board_id=board_id,
                            status=status_filter,
                        ),
                    )
                    return

                if path == "/regressions":
                    limit_raw = query.get("limit", [None])[0]
                    offset_raw = query.get("offset", [None])[0]
                    metric_set = query.get("metric_set", [None])[0] or None
                    pass_fail_raw = query.get("pass_fail", [None])[0]
                    limit = None if limit_raw in (None, "") else int(limit_raw)
                    offset = 0 if offset_raw in (None, "") else int(offset_raw)
                    pass_fail: bool | None = None
                    if pass_fail_raw not in (None, ""):
                        normalized = str(pass_fail_raw).strip().lower()
                        if normalized in {"1", "true", "yes"}:
                            pass_fail = True
                        elif normalized in {"0", "false", "no"}:
                            pass_fail = False
                        else:
                            raise ValueError(f"Invalid pass_fail: {pass_fail_raw}")
                    self._send(
                        200,
                        api.list_regression_summaries(
                            limit=limit,
                            offset=offset,
                            metric_set=metric_set,
                            pass_fail=pass_fail,
                        ),
                    )
                    return

                if path == "/regressions/latest":
                    self._send(200, api.latest_regression_summary())
                    return

                parts = [p for p in path.split("/") if p]
                if len(parts) == 3 and parts[0] == "packs":
                    self._send(200, api.get_pack_item(parts[1], parts[2]))
                    return

                if len(parts) == 2 and parts[0] == "regressions":
                    self._send(200, api.get_regression_summary(parts[1]))
                    return

                if len(parts) == 3 and parts[0] == "runs" and parts[2] in {"report", "eval", "runlog"}:
                    run_id = parts[1]
                    if parts[2] == "report":
                        self._send(200, api.get_report(run_id))
                        return
                    if parts[2] == "eval":
                        self._send(200, api.get_eval(run_id))
                        return
                    self._send(200, api.get_runlog(run_id))
                    return

                self._send(404, {"error": "not_found"})
            except FileNotFoundError as exc:
                self._send(404, {"error": "not_found", "message": str(exc)})
            except ValueError as exc:
                self._send(400, {"error": "bad_request", "message": str(exc)})
            except Exception as exc:  # pragma: no cover - defensive
                self._send(500, {"error": "internal_error", "message": str(exc)})
            finally:
                self._emit_request_log("GET", path, auth_ok, started_at)

        def do_POST(self) -> None:  # noqa: N802
            started_at = time.perf_counter()
            self._response_status = None
            parsed = urlparse(self.path)
            path = parsed.path
            auth_ok = self._is_authorized(path)
            if not auth_ok:
                self._send(401, {"error": "unauthorized"})
                self._emit_request_log("POST", path, auth_ok, started_at)
                return

            try:
                body = self._read_json()
            except json.JSONDecodeError:
                self._send(400, {"error": "invalid_json"})
                self._emit_request_log("POST", path, auth_ok, started_at)
                return

            try:
                if path == "/simulate":
                    seed_payload = body.get("seed", {})
                    rounds = int(body.get("rounds", 3))
                    payload = api.simulate(
                        seed_payload=seed_payload,
                        rounds=rounds,
                        orchestrator_backend=body.get("orchestrator_backend", "manual"),
                    )
                    self._send(200, payload)
                    return

                if path == "/evaluate":
                    payload = api.evaluate(
                        run_id=body.get("run_id"),
                        metric_set=body.get("metric_set", "v1"),
                    )
                    self._send(200, payload)
                    return

                if path == "/regress":
                    payload = api.regress(
                        seeds_dir=Path(body.get("seeds_dir", "examples/seeds/regression")),
                        rounds=int(body.get("rounds", 4)),
                        max_seeds=int(body.get("max_seeds", 10)),
                        metric_set=body.get("metric_set", "v1"),
                        min_community_coverage=int(body.get("min_community_coverage", 2)),
                        min_conflict_frame_runs=int(body.get("min_conflict_frame_runs", 2)),
                        min_moderation_hook_runs=int(body.get("min_moderation_hook_runs", 1)),
                        min_validation_warning_runs=int(body.get("min_validation_warning_runs", 1)),
                        orchestrator_backend=body.get("orchestrator_backend", "manual"),
                    )
                    self._send(200, payload)
                    return

                if path == "/kb/search":
                    payload = api.search_knowledge(
                        query=body.get("query", ""),
                        filters=body.get("filters", {}),
                        top_k=int(body.get("top_k", 5)),
                    )
                    self._send(200, payload)
                    return

                if path == "/kb/context":
                    required = ["task", "seed", "board_id", "zone_id"]
                    missing = [key for key in required if not body.get(key)]
                    if missing:
                        raise ValueError(f"Missing required fields: {', '.join(missing)}")

                    payload = api.retrieve_context_bundle(
                        task=body["task"],
                        seed=body["seed"],
                        board_id=body["board_id"],
                        zone_id=body["zone_id"],
                        persona_ids=body.get("persona_ids", []),
                        top_k=int(body.get("top_k", 3)),
                    )
                    self._send(200, payload)
                    return

                self._send(404, {"error": "not_found"})
            except ValueError as exc:
                self._send(400, {"error": "bad_request", "message": str(exc)})
            except FileNotFoundError as exc:
                self._send(404, {"error": "not_found", "message": str(exc)})
            except Exception as exc:  # pragma: no cover - defensive
                self._send(500, {"error": "internal_error", "message": str(exc)})
            finally:
                self._emit_request_log("POST", path, auth_ok, started_at)

        def log_message(self, format: str, *args) -> None:  # noqa: A003
            # Keep test output and CLI clean.
            return

    return ThreadingHTTPServer((host, port), RequestHandler)


def serve(
    api: ProjectDreamAPI,
    host: str = "127.0.0.1",
    port: int = 8000,
    api_token: str = "",
    request_logger: Callable[[dict], None] | None = None,
) -> None:
    server = create_server(
        api=api,
        host=host,
        port=port,
        api_token=api_token,
        request_logger=request_logger,
    )
    try:
        server.serve_forever()
    finally:
        server.server_close()
