import json
from pathlib import Path

import pytest

from project_dream.regression_runner import run_regression_batch
import project_dream.regression_runner as regression_runner
from project_dream.sim_orchestrator import run_simulation as base_run_simulation


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
    assert summary["totals"]["context_trace_runs"] == 2
    assert summary["totals"]["stage_trace_runs"] == 2
    assert summary["totals"]["stage_trace_consistent_runs"] == 2
    assert summary["totals"]["stage_trace_ordered_runs"] == 2
    assert summary["totals"]["avg_stage_trace_coverage_rate"] == pytest.approx(1.0)
    assert summary["totals"]["report_gate_pass_runs"] == 2
    assert summary["pass_fail"] is True
    assert "format_missing_zero" in summary["gates"]
    assert summary["gates"]["context_trace_runs"] is True
    assert summary["gates"]["stage_trace_runs"] is True
    assert summary["gates"]["stage_trace_consistent_runs"] is True
    assert summary["gates"]["stage_trace_ordered_runs"] is True
    assert summary["gates"]["stage_trace_coverage_rate"] is True
    assert summary["gates"]["report_gate_pass_runs"] is True
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


def test_run_regression_batch_uses_retrieved_context_corpus(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    seeds_dir = tmp_path / "seeds"
    seeds_dir.mkdir(parents=True, exist_ok=True)
    _write_seed(seeds_dir / "seed_001.json", "SEED-R-CONTEXT-001", "B07", "D")

    captured_corpora: list[list[str]] = []
    def spy_run_simulation_with_backend(
        *,
        seed,
        rounds,
        corpus,
        max_retries=2,
        packs=None,
        backend="manual",
    ):
        captured_corpora.append(list(corpus))
        return base_run_simulation(
            seed=seed,
            rounds=rounds,
            corpus=corpus,
            max_retries=max_retries,
            packs=packs,
        )

    monkeypatch.setattr(
        regression_runner,
        "run_simulation_with_backend",
        spy_run_simulation_with_backend,
    )
    monkeypatch.setattr(
        regression_runner,
        "build_index",
        lambda packs, **kwargs: {"fake": "index"},
        raising=False,
    )
    monkeypatch.setattr(
        regression_runner,
        "retrieve_context",
        lambda index, **kwargs: {"bundle": {}, "corpus": [f"ctx-{kwargs['board_id']}-{kwargs['zone_id']}"]},
        raising=False,
    )

    run_regression_batch(
        seeds_dir=seeds_dir,
        packs_dir=Path("packs"),
        output_dir=tmp_path / "runs",
        corpus_dir=tmp_path / "missing-corpus",
        rounds=3,
        max_seeds=1,
        metric_set="v1",
        min_community_coverage=1,
        min_conflict_frame_runs=0,
        min_moderation_hook_runs=0,
        min_validation_warning_runs=0,
    )

    assert captured_corpora
    assert captured_corpora[0] == ["ctx-B07-D"]


def test_run_regression_batch_merges_ingested_corpus(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    seeds_dir = tmp_path / "seeds"
    seeds_dir.mkdir(parents=True, exist_ok=True)
    _write_seed(seeds_dir / "seed_001.json", "SEED-R-CONTEXT-002", "B07", "D")

    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir(parents=True, exist_ok=True)
    (corpus_dir / "reference.jsonl").write_text(
        '{"text":"ctx-reference"}\n{"text":"ctx-B07-D"}\n',
        encoding="utf-8",
    )
    (corpus_dir / "refined.jsonl").write_text('{"text":"ctx-refined"}\n', encoding="utf-8")
    (corpus_dir / "generated.jsonl").write_text("", encoding="utf-8")

    captured_corpora: list[list[str]] = []
    def spy_run_simulation_with_backend(
        *,
        seed,
        rounds,
        corpus,
        max_retries=2,
        packs=None,
        backend="manual",
    ):
        captured_corpora.append(list(corpus))
        return base_run_simulation(
            seed=seed,
            rounds=rounds,
            corpus=corpus,
            max_retries=max_retries,
            packs=packs,
        )

    monkeypatch.setattr(
        regression_runner,
        "run_simulation_with_backend",
        spy_run_simulation_with_backend,
    )
    monkeypatch.setattr(
        regression_runner,
        "build_index",
        lambda packs, **kwargs: {"fake": "index"},
        raising=False,
    )
    monkeypatch.setattr(
        regression_runner,
        "retrieve_context",
        lambda index, **kwargs: {"bundle": {}, "corpus": [f"ctx-{kwargs['board_id']}-{kwargs['zone_id']}"]},
        raising=False,
    )

    run_regression_batch(
        seeds_dir=seeds_dir,
        packs_dir=Path("packs"),
        output_dir=tmp_path / "runs",
        rounds=3,
        max_seeds=1,
        metric_set="v1",
        min_community_coverage=1,
        min_conflict_frame_runs=0,
        min_moderation_hook_runs=0,
        min_validation_warning_runs=0,
        corpus_dir=corpus_dir,
    )

    assert captured_corpora
    assert captured_corpora[0] == ["ctx-B07-D", "ctx-reference", "ctx-refined"]


def test_run_regression_batch_forwards_orchestrator_backend(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    seeds_dir = tmp_path / "seeds"
    seeds_dir.mkdir(parents=True, exist_ok=True)
    _write_seed(seeds_dir / "seed_001.json", "SEED-R-CONTEXT-003", "B07", "D")

    captured: dict = {}
    def fake_run_simulation_with_backend(
        *,
        seed,
        rounds,
        corpus,
        max_retries=2,
        packs=None,
        backend="manual",
    ):
        captured["backend"] = backend
        return base_run_simulation(
            seed=seed,
            rounds=rounds,
            corpus=corpus,
            max_retries=max_retries,
            packs=packs,
        )

    monkeypatch.setattr(
        regression_runner,
        "run_simulation_with_backend",
        fake_run_simulation_with_backend,
        raising=False,
    )

    run_regression_batch(
        seeds_dir=seeds_dir,
        packs_dir=Path("packs"),
        output_dir=tmp_path / "runs",
        rounds=3,
        max_seeds=1,
        metric_set="v1",
        min_community_coverage=1,
        min_conflict_frame_runs=0,
        min_moderation_hook_runs=0,
        min_validation_warning_runs=0,
        orchestrator_backend="langgraph",
    )

    assert captured["backend"] == "langgraph"


def test_run_regression_batch_forwards_vector_backend_to_build_index(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    seeds_dir = tmp_path / "seeds"
    seeds_dir.mkdir(parents=True, exist_ok=True)
    _write_seed(seeds_dir / "seed_001.json", "SEED-R-VECTOR-001", "B07", "D")

    captured: dict = {}

    def fake_build_index(packs, corpus_dir=None, *, vector_backend="memory", vector_db_path=None):
        captured["vector_backend"] = vector_backend
        captured["vector_db_path"] = vector_db_path
        return {"fake": "index"}

    monkeypatch.setattr(regression_runner, "build_index", fake_build_index, raising=False)
    monkeypatch.setattr(
        regression_runner,
        "retrieve_context",
        lambda index, **kwargs: {"bundle": {}, "corpus": ["ctx-B07-D"]},
        raising=False,
    )

    vector_db_path = tmp_path / "vectors.sqlite3"
    run_regression_batch(
        seeds_dir=seeds_dir,
        packs_dir=Path("packs"),
        output_dir=tmp_path / "runs",
        rounds=3,
        max_seeds=1,
        metric_set="v1",
        min_community_coverage=1,
        min_conflict_frame_runs=0,
        min_moderation_hook_runs=0,
        min_validation_warning_runs=0,
        vector_backend="sqlite",
        vector_db_path=vector_db_path,
    )

    assert captured["vector_backend"] == "sqlite"
    assert captured["vector_db_path"] == vector_db_path
