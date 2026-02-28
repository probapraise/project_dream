import json
from pathlib import Path

from project_dream.cli import main


def test_cli_simulate_writes_run_outputs(tmp_path: Path):
    seed_file = tmp_path / "seed.json"
    seed_file.write_text(
        json.dumps(
            {
                "seed_id": "SEED-001",
                "title": "먹통 사건",
                "summary": "장터기둥 장애",
                "board_id": "B07",
                "zone_id": "D",
            }
        ),
        encoding="utf-8",
    )

    rc = main(
        [
            "simulate",
            "--seed",
            str(seed_file),
            "--output-dir",
            str(tmp_path / "runs"),
            "--rounds",
            "3",
        ]
    )
    assert rc == 0
    runlogs = list((tmp_path / "runs").glob("*/runlog.jsonl"))
    assert runlogs
    report_md_files = list((tmp_path / "runs").glob("*/report.md"))
    report_json_files = list((tmp_path / "runs").glob("*/report.json"))
    assert report_md_files
    assert report_json_files

    runlog_path = runlogs[0]
    rows = [json.loads(line) for line in runlog_path.read_text(encoding="utf-8").splitlines()]
    assert any(row.get("type") == "round" and "community_id" in row for row in rows)
    assert any(row.get("type") == "action" for row in rows)

    report_json = json.loads(report_json_files[0].read_text(encoding="utf-8"))
    assert report_json["schema_version"] == "report.v1"
    assert len(report_json["lens_summaries"]) == 4
    assert "conflict_map" in report_json
    assert 3 <= len(report_json["dialogue_candidates"]) <= 5

    report_md = report_md_files[0].read_text(encoding="utf-8")
    assert "## Conflict Map" in report_md
    assert "## Risk Checks" in report_md


def test_cli_simulate_uses_vector_backend_env_defaults(tmp_path: Path, monkeypatch):
    seed_file = tmp_path / "seed.json"
    seed_file.write_text(
        json.dumps(
            {
                "seed_id": "SEED-ENV-001",
                "title": "환경 기본값 테스트",
                "summary": "벡터 백엔드 env 기본값 테스트",
                "board_id": "B07",
                "zone_id": "D",
            }
        ),
        encoding="utf-8",
    )
    vector_db_path = tmp_path / "env-vectors.sqlite3"

    monkeypatch.setenv("PROJECT_DREAM_VECTOR_BACKEND", "sqlite")
    monkeypatch.setenv("PROJECT_DREAM_VECTOR_DB_PATH", str(vector_db_path))

    rc = main(
        [
            "simulate",
            "--seed",
            str(seed_file),
            "--output-dir",
            str(tmp_path / "runs"),
            "--rounds",
            "3",
        ]
    )
    assert rc == 0
    assert vector_db_path.exists()
