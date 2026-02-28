import json
from pathlib import Path

from project_dream.app_service import simulate_and_persist
from project_dream.eval_export import export_external_eval_bundle
from project_dream.infra.store import FileRunRepository
from project_dream.models import SeedInput


def _read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def test_export_external_eval_bundle_writes_promptfoo_ragas_trace_files(tmp_path: Path):
    repo = FileRunRepository(tmp_path / "runs")
    seed = SeedInput(
        seed_id="SEED-EXPORT-001",
        title="외부 평가 export",
        summary="promptfoo ragas tracing 포맷 export",
        board_id="B07",
        zone_id="D",
    )
    run_dir = simulate_and_persist(
        seed=seed,
        rounds=3,
        packs_dir=Path("packs"),
        repository=repo,
        corpus_dir=tmp_path / "missing-corpus",
    )

    manifest = export_external_eval_bundle(run_dir)

    assert manifest["schema_version"] == "external_eval_export.v1"
    assert manifest["run_id"] == run_dir.name
    assert manifest["counts"]["promptfoo_cases"] >= 3
    assert manifest["counts"]["ragas_samples"] >= 3
    assert manifest["counts"]["trace_events"] >= 1

    out = run_dir / "eval_exports"
    promptfoo_rows = _read_jsonl(out / "promptfoo_cases.jsonl")
    ragas_rows = _read_jsonl(out / "ragas_samples.jsonl")
    trace_rows = _read_jsonl(out / "trace_events.jsonl")

    assert promptfoo_rows
    assert {"case_id", "prompt", "output", "metadata"} <= set(promptfoo_rows[0].keys())
    assert ragas_rows
    assert {"sample_id", "question", "answer", "contexts", "ground_truth"} <= set(ragas_rows[0].keys())
    assert trace_rows
    assert {"trace_id", "event_index", "event_type", "payload"} <= set(trace_rows[0].keys())
