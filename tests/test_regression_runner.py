import json
from pathlib import Path

import pytest

from project_dream.regression_runner import run_regression_batch


def _write_seed(path: Path, seed_id: str, board_id: str, zone_id: str) -> None:
    payload = {
        "seed_id": seed_id,
        "title": f"{seed_id} title",
        "summary": f"{seed_id} summary",
        "board_id": board_id,
        "zone_id": zone_id,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def test_run_regression_batch_produces_summary_and_passes(tmp_path: Path):
    seeds_dir = tmp_path / "seeds"
    seeds_dir.mkdir(parents=True, exist_ok=True)
    _write_seed(seeds_dir / "seed_001.json", "SEED-R-001", "B01", "A")
    _write_seed(seeds_dir / "seed_002.json", "SEED-R-002", "B07", "D")

    runs_dir = tmp_path / "runs"
    summary = run_regression_batch(
        seeds_dir=seeds_dir,
        packs_dir=Path("packs"),
        output_dir=runs_dir,
        rounds=4,
        max_seeds=2,
        metric_set="v1",
        min_community_coverage=2,
        min_conflict_frame_runs=2,
        min_moderation_hook_runs=1,
        min_validation_warning_runs=1,
    )

    assert summary["schema_version"] == "regression.v1"
    assert summary["metric_set"] == "v1"
    assert summary["totals"]["seed_runs"] == 2
    assert summary["pass_fail"] is True
    assert "format_missing_zero" in summary["gates"]
    summary_path = Path(summary["summary_path"])
    assert summary_path.exists()


def test_run_regression_batch_raises_when_no_seed_files(tmp_path: Path):
    seeds_dir = tmp_path / "empty-seeds"
    seeds_dir.mkdir(parents=True, exist_ok=True)

    with pytest.raises(FileNotFoundError):
        run_regression_batch(
            seeds_dir=seeds_dir,
            packs_dir=Path("packs"),
            output_dir=tmp_path / "runs",
            rounds=4,
        )


def test_regression_seed_fixture_count():
    seeds = sorted(Path("examples/seeds/regression").glob("seed_*.json"))
    assert len(seeds) == 10
