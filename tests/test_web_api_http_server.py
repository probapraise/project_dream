import json
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

from project_dream.infra.http_server import create_server
from project_dream.infra.store import FileRunRepository
from project_dream.infra.web_api import ProjectDreamAPI


def _request_json(
    method: str,
    url: str,
    payload: dict | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict]:
    data = None
    request_headers = dict(headers or {})
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request_headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=request_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        payload = json.loads(body) if body else {}
        return exc.code, payload


def test_http_server_health_simulate_evaluate(tmp_path: Path):
    api = ProjectDreamAPI(
        repository=FileRunRepository(tmp_path / "runs"),
        packs_dir=Path("packs"),
    )
    token = "test-token"
    auth = {"Authorization": f"Bearer {token}"}
    wrong_auth = {"Authorization": "Bearer wrong-token"}

    server = create_server(api=api, host="127.0.0.1", port=0, api_token=token)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        host, port = server.server_address
        base = f"http://{host}:{port}"

        status, health = _request_json("GET", f"{base}/health")
        assert status == 200
        assert health["status"] == "ok"

        status, unauthorized_latest = _request_json("GET", f"{base}/runs/latest")
        assert status == 401
        assert unauthorized_latest["error"] == "unauthorized"

        status, wrong_token_latest = _request_json("GET", f"{base}/runs/latest", headers=wrong_auth)
        assert status == 401
        assert wrong_token_latest["error"] == "unauthorized"

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
            headers=auth,
        )
        assert status == 200
        assert sim["run_id"].startswith("run-")

        status, unauthorized_sim = _request_json(
            "POST",
            f"{base}/simulate",
            {
                "seed": {
                    "seed_id": "SEED-HTTP-UNAUTH",
                    "title": "unauth",
                    "summary": "unauth",
                    "board_id": "B07",
                    "zone_id": "D",
                },
                "rounds": 3,
            },
        )
        assert status == 401
        assert unauthorized_sim["error"] == "unauthorized"

        status, eva = _request_json(
            "POST",
            f"{base}/evaluate",
            {
                "run_id": sim["run_id"],
                "metric_set": "v2",
            },
            headers=auth,
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
            headers=auth,
        )
        assert status == 200
        assert reg["schema_version"] == "regression.v1"
        assert reg["totals"]["seed_runs"] == 3

        status, reg_second = _request_json(
            "POST",
            f"{base}/regress",
            {
                "seeds_dir": "examples/seeds/regression",
                "rounds": 3,
                "max_seeds": 2,
                "metric_set": "v1",
            },
            headers=auth,
        )
        assert status == 200
        assert reg_second["schema_version"] == "regression.v1"
        assert reg_second["totals"]["seed_runs"] == 2

        status, reg_list = _request_json("GET", f"{base}/regressions", headers=auth)
        assert status == 200
        assert reg_list["count"] >= 2
        assert len(reg_list["items"]) >= 2
        assert reg_list["items"][0]["summary_id"].startswith("regression-")
        assert reg_list["items"][0]["summary_path"].endswith(".json")

        status, reg_list_limited = _request_json("GET", f"{base}/regressions?limit=1", headers=auth)
        assert status == 200
        assert reg_list_limited["count"] == 1
        assert len(reg_list_limited["items"]) == 1
        assert reg_list_limited["total"] >= 2
        assert reg_list_limited["limit"] == 1
        assert reg_list_limited["offset"] == 0

        status, reg_list_filtered = _request_json(
            "GET",
            f"{base}/regressions?metric_set=v1&pass_fail=true",
            headers=auth,
        )
        assert status == 200
        assert reg_list_filtered["count"] >= 1
        assert all(item["metric_set"] == "v1" for item in reg_list_filtered["items"])
        assert all(item["pass_fail"] is True for item in reg_list_filtered["items"])

        status, reg_list_paged = _request_json("GET", f"{base}/regressions?limit=1&offset=1", headers=auth)
        assert status == 200
        assert reg_list_paged["count"] == 1
        assert reg_list_paged["total"] >= 2
        assert reg_list_paged["limit"] == 1
        assert reg_list_paged["offset"] == 1

        status, reg_latest = _request_json("GET", f"{base}/regressions/latest", headers=auth)
        assert status == 200
        assert reg_latest["schema_version"] == "regression.v1"
        assert reg_latest["metric_set"] == "v1"
        assert reg_latest["totals"]["seed_runs"] == 2
        assert reg_latest["summary_path"].endswith(".json")
        summary_id = Path(reg_latest["summary_path"]).name
        summary_id_stem = summary_id.removesuffix(".json")

        status, reg_by_filename = _request_json("GET", f"{base}/regressions/{summary_id}", headers=auth)
        assert status == 200
        assert reg_by_filename["schema_version"] == "regression.v1"
        assert reg_by_filename["summary_path"].endswith(summary_id)

        status, reg_by_stem = _request_json("GET", f"{base}/regressions/{summary_id_stem}", headers=auth)
        assert status == 200
        assert reg_by_stem["schema_version"] == "regression.v1"
        assert reg_by_stem["summary_path"].endswith(summary_id)

        status, latest = _request_json("GET", f"{base}/runs/latest", headers=auth)
        assert status == 200
        known_run_ids = {
            sim["run_id"],
            *[row["run_id"] for row in reg["runs"]],
            *[row["run_id"] for row in reg_second["runs"]],
        }
        assert latest["run_id"] in known_run_ids

        status, runs_list = _request_json("GET", f"{base}/runs", headers=auth)
        assert status == 200
        assert runs_list["count"] >= 1
        assert runs_list["total"] >= 1
        assert any(row["run_id"] == sim["run_id"] for row in runs_list["items"])

        status, runs_filtered = _request_json("GET", f"{base}/runs?seed_id=SEED-HTTP-001", headers=auth)
        assert status == 200
        assert runs_filtered["count"] >= 1
        assert any(row["run_id"] == sim["run_id"] for row in runs_filtered["items"])

        status, runs_paged = _request_json("GET", f"{base}/runs?limit=1&offset=0", headers=auth)
        assert status == 200
        assert runs_paged["count"] == 1
        assert runs_paged["limit"] == 1
        assert runs_paged["offset"] == 0

        status, report = _request_json("GET", f"{base}/runs/{sim['run_id']}/report", headers=auth)
        assert status == 200
        assert report["schema_version"] == "report.v1"

        status, eval_payload = _request_json("GET", f"{base}/runs/{sim['run_id']}/eval", headers=auth)
        assert status == 200
        assert eval_payload["schema_version"] == "eval.v1"

        status, runlog = _request_json("GET", f"{base}/runs/{sim['run_id']}/runlog", headers=auth)
        assert status == 200
        assert runlog["run_id"] == sim["run_id"]
        assert runlog["rows"]

        status, kb_search = _request_json(
            "POST",
            f"{base}/kb/search",
            {
                "query": "illegal_trade",
                "filters": {"kind": "board", "board_id": "B07"},
                "top_k": 3,
            },
            headers=auth,
        )
        assert status == 200
        assert kb_search["count"] >= 1
        assert kb_search["items"][0]["item_id"] == "B07"

        status, kb_context = _request_json(
            "POST",
            f"{base}/kb/context",
            {
                "task": "거래 사기 의혹",
                "seed": "중계망 장애",
                "board_id": "B07",
                "zone_id": "D",
                "persona_ids": ["P07"],
                "top_k": 2,
            },
            headers=auth,
        )
        assert status == 200
        assert kb_context["bundle"]["board_id"] == "B07"
        assert kb_context["corpus"]

        status, pack_item = _request_json("GET", f"{base}/packs/board/B07", headers=auth)
        assert status == 200
        assert pack_item["id"] == "B07"
        assert pack_item["name"] == "장터기둥"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_http_server_emits_structured_access_logs(tmp_path: Path):
    api = ProjectDreamAPI(
        repository=FileRunRepository(tmp_path / "runs"),
        packs_dir=Path("packs"),
    )
    token = "log-token"
    auth = {"Authorization": f"Bearer {token}"}
    access_logs: list[dict] = []

    server = create_server(
        api=api,
        host="127.0.0.1",
        port=0,
        api_token=token,
        request_logger=access_logs.append,
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        host, port = server.server_address
        base = f"http://{host}:{port}"

        _request_json("GET", f"{base}/health")
        _request_json("GET", f"{base}/runs/latest")
        _request_json("GET", f"{base}/runs/latest", headers=auth)

        deadline = time.time() + 0.5
        while len(access_logs) < 3 and time.time() < deadline:
            time.sleep(0.01)

        assert len(access_logs) >= 3
        for entry in access_logs:
            assert entry["method"] in {"GET", "POST"}
            assert entry["path"].startswith("/")
            assert isinstance(entry["status"], int)
            assert isinstance(entry["latency_ms"], int)
            assert isinstance(entry["auth_ok"], bool)
            assert entry["event"] in {"http_request", "http_auth_failure"}

        unauthorized_runs_latest = [
            entry
            for entry in access_logs
            if entry["path"] == "/runs/latest" and entry["status"] == 401
        ]
        assert unauthorized_runs_latest
        assert all(not entry["auth_ok"] for entry in unauthorized_runs_latest)
        assert all(entry["event"] == "http_auth_failure" for entry in unauthorized_runs_latest)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
