import json
from pathlib import Path

from project_dream.cli import main


def _write_seed(path: Path, seed_id: str, board_id: str, zone_id: str) -> None:
    payload = {
        "seed_id": seed_id,
        "title": f"{seed_id} title",
        "summary": f"{seed_id} summary",
        "board_id": board_id,
        "zone_id": zone_id,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def test_cli_regress_writes_summary_and_returns_zero(tmp_path: Path):
    seeds_dir = tmp_path / "seeds"
    seeds_dir.mkdir(parents=True, exist_ok=True)
    _write_seed(seeds_dir / "seed_001.json", "SEED-C-001", "B01", "A")
    _write_seed(seeds_dir / "seed_002.json", "SEED-C-002", "B07", "D")

    runs_dir = tmp_path / "runs"
    rc = main(
        [
            "regress",
            "--seeds-dir",
            str(seeds_dir),
            "--output-dir",
            str(runs_dir),
            "--max-seeds",
            "2",
            "--rounds",
            "4",
            "--min-community-coverage",
            "2",
            "--min-conflict-frame-runs",
            "2",
            "--min-moderation-hook-runs",
            "1",
            "--min-validation-warning-runs",
            "1",
        ]
    )
    assert rc == 0

    summary_files = list((runs_dir / "regressions").glob("regression-*.json"))
    assert len(summary_files) == 1
    payload = json.loads(summary_files[0].read_text(encoding="utf-8"))
    assert payload["schema_version"] == "regression.v1"
    assert payload["pass_fail"] is True


def test_cli_regress_returns_nonzero_when_gate_fails(tmp_path: Path):
    seeds_dir = tmp_path / "seeds-fail"
    seeds_dir.mkdir(parents=True, exist_ok=True)
    _write_seed(seeds_dir / "seed_001.json", "SEED-C-101", "B01", "A")
    _write_seed(seeds_dir / "seed_002.json", "SEED-C-102", "B01", "A")

    rc = main(
        [
            "regress",
            "--seeds-dir",
            str(seeds_dir),
            "--output-dir",
            str(tmp_path / "runs-fail"),
            "--max-seeds",
            "2",
            "--rounds",
            "4",
            "--min-community-coverage",
            "3",
        ]
    )
    assert rc != 0


def test_cli_regress_uses_vector_backend_env_defaults(tmp_path: Path, monkeypatch):
    seeds_dir = tmp_path / "seeds-env"
    seeds_dir.mkdir(parents=True, exist_ok=True)
    _write_seed(seeds_dir / "seed_001.json", "SEED-C-ENV-001", "B01", "A")

    vector_db_path = tmp_path / "regress-env-vectors.sqlite3"
    monkeypatch.setenv("PROJECT_DREAM_VECTOR_BACKEND", "sqlite")
    monkeypatch.setenv("PROJECT_DREAM_VECTOR_DB_PATH", str(vector_db_path))

    runs_dir = tmp_path / "runs-env"
    rc = main(
        [
            "regress",
            "--seeds-dir",
            str(seeds_dir),
            "--output-dir",
            str(runs_dir),
            "--max-seeds",
            "1",
            "--rounds",
            "3",
            "--min-community-coverage",
            "1",
            "--min-conflict-frame-runs",
            "0",
            "--min-moderation-hook-runs",
            "0",
            "--min-validation-warning-runs",
            "0",
        ]
    )
    assert rc == 0
    assert vector_db_path.exists()

    summary_files = list((runs_dir / "regressions").glob("regression-*.json"))
    assert len(summary_files) == 1
    payload = json.loads(summary_files[0].read_text(encoding="utf-8"))
    assert payload["config"]["vector_backend"] == "sqlite"
    assert payload["config"]["vector_db_path"] == str(vector_db_path)
