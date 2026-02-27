import json
import threading
import urllib.request
from pathlib import Path

from project_dream.infra.http_server import create_server
from project_dream.infra.store import FileRunRepository
from project_dream.infra.web_api import ProjectDreamAPI


def _request_json(method: str, url: str, payload: dict | None = None) -> tuple[int, dict]:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=5) as resp:
        body = resp.read().decode("utf-8")
        return resp.status, json.loads(body)


def test_http_server_health_simulate_evaluate(tmp_path: Path):
    api = ProjectDreamAPI(
        repository=FileRunRepository(tmp_path / "runs"),
        packs_dir=Path("packs"),
    )
    server = create_server(api=api, host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        host, port = server.server_address
        base = f"http://{host}:{port}"

        status, health = _request_json("GET", f"{base}/health")
        assert status == 200
        assert health["status"] == "ok"

        status, sim = _request_json(
            "POST",
            f"{base}/simulate",
            {
                "seed": {
                    "seed_id": "SEED-HTTP-001",
                    "title": "HTTP 시뮬",
                    "summary": "HTTP 요약",
                    "board_id": "B07",
                    "zone_id": "D",
                },
                "rounds": 3,
            },
        )
        assert status == 200
        assert sim["run_id"].startswith("run-")

        status, eva = _request_json(
            "POST",
            f"{base}/evaluate",
            {
                "run_id": sim["run_id"],
                "metric_set": "v2",
            },
        )
        assert status == 200
        assert eva["schema_version"] == "eval.v1"
        assert eva["metric_set"] == "v2"

        status, reg = _request_json(
            "POST",
            f"{base}/regress",
            {
                "seeds_dir": "examples/seeds/regression",
                "rounds": 3,
                "max_seeds": 3,
                "metric_set": "v2",
            },
        )
        assert status == 200
        assert reg["schema_version"] == "regression.v1"
        assert reg["totals"]["seed_runs"] == 3

        status, latest = _request_json("GET", f"{base}/runs/latest")
        assert status == 200
        known_run_ids = {sim["run_id"], *[row["run_id"] for row in reg["runs"]]}
        assert latest["run_id"] in known_run_ids

        status, report = _request_json("GET", f"{base}/runs/{sim['run_id']}/report")
        assert status == 200
        assert report["schema_version"] == "report.v1"

        status, eval_payload = _request_json("GET", f"{base}/runs/{sim['run_id']}/eval")
        assert status == 200
        assert eval_payload["schema_version"] == "eval.v1"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
