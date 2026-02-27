import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from project_dream.infra.web_api import ProjectDreamAPI


def _json_bytes(payload: dict) -> bytes:
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


def create_server(api: ProjectDreamAPI, host: str = "127.0.0.1", port: int = 8000) -> ThreadingHTTPServer:
    class RequestHandler(BaseHTTPRequestHandler):
        def _send(self, status: int, payload: dict) -> None:
            body = _json_bytes(payload)
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _read_json(self) -> dict:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length) if length > 0 else b"{}"
            return json.loads(raw.decode("utf-8"))

        def do_GET(self) -> None:  # noqa: N802
            try:
                if self.path == "/health":
                    self._send(200, api.health())
                    return

                if self.path == "/runs/latest":
                    self._send(200, api.latest_run())
                    return

                parts = [p for p in self.path.split("/") if p]
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
            except Exception as exc:  # pragma: no cover - defensive
                self._send(500, {"error": "internal_error", "message": str(exc)})

        def do_POST(self) -> None:  # noqa: N802
            try:
                body = self._read_json()
            except json.JSONDecodeError:
                self._send(400, {"error": "invalid_json"})
                return

            try:
                if self.path == "/simulate":
                    seed_payload = body.get("seed", {})
                    rounds = int(body.get("rounds", 3))
                    payload = api.simulate(seed_payload=seed_payload, rounds=rounds)
                    self._send(200, payload)
                    return

                if self.path == "/evaluate":
                    payload = api.evaluate(
                        run_id=body.get("run_id"),
                        metric_set=body.get("metric_set", "v1"),
                    )
                    self._send(200, payload)
                    return

                if self.path == "/regress":
                    payload = api.regress(
                        seeds_dir=Path(body.get("seeds_dir", "examples/seeds/regression")),
                        rounds=int(body.get("rounds", 4)),
                        max_seeds=int(body.get("max_seeds", 10)),
                        metric_set=body.get("metric_set", "v1"),
                        min_community_coverage=int(body.get("min_community_coverage", 2)),
                        min_conflict_frame_runs=int(body.get("min_conflict_frame_runs", 2)),
                        min_moderation_hook_runs=int(body.get("min_moderation_hook_runs", 1)),
                        min_validation_warning_runs=int(body.get("min_validation_warning_runs", 1)),
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

        def log_message(self, format: str, *args) -> None:  # noqa: A003
            # Keep test output and CLI clean.
            return

    return ThreadingHTTPServer((host, port), RequestHandler)


def serve(api: ProjectDreamAPI, host: str = "127.0.0.1", port: int = 8000) -> None:
    server = create_server(api=api, host=host, port=port)
    try:
        server.serve_forever()
    finally:
        server.server_close()
