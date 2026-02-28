from __future__ import annotations

import json
from pathlib import Path


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fp:
        for row in rows:
            fp.write(json.dumps(row, ensure_ascii=False) + "\n")


def _context_corpus(runlog_rows: list[dict], max_contexts: int) -> list[str]:
    for row in runlog_rows:
        if row.get("type") != "context":
            continue
        corpus = row.get("corpus")
        if isinstance(corpus, list):
            out = [str(item) for item in corpus if str(item).strip()]
            return out[: max(1, max_contexts)]
    return []


def build_promptfoo_cases(run_id: str, runlog_rows: list[dict]) -> list[dict]:
    rows = [row for row in runlog_rows if row.get("type") == "round"]
    cases: list[dict] = []
    for idx, row in enumerate(rows, start=1):
        stage2 = row.get("generation_stage2", {})
        prompt = ""
        if isinstance(stage2, dict):
            prompt = str(stage2.get("prompt", "")).strip()
        if not prompt:
            prompt = f"[{row.get('board_id', '')}/{row.get('community_id', '')}] round={row.get('round', idx)}"
        case_id = f"{run_id}-r{row.get('round', idx)}-{row.get('persona_id', 'unknown')}"
        cases.append(
            {
                "case_id": case_id,
                "prompt": prompt,
                "output": str(row.get("text", "")),
                "metadata": {
                    "run_id": run_id,
                    "round": int(row.get("round", idx)),
                    "persona_id": row.get("persona_id"),
                    "board_id": row.get("board_id"),
                    "community_id": row.get("community_id"),
                },
            }
        )
    return cases


def build_ragas_samples(
    run_id: str,
    runlog_rows: list[dict],
    report: dict,
    *,
    max_contexts: int = 5,
) -> list[dict]:
    rows = [row for row in runlog_rows if row.get("type") == "round"]
    contexts = _context_corpus(runlog_rows, max_contexts=max_contexts)
    ground_truth = str(report.get("summary", "")).strip()

    samples: list[dict] = []
    for idx, row in enumerate(rows, start=1):
        stage2 = row.get("generation_stage2", {})
        question = ""
        if isinstance(stage2, dict):
            question = str(stage2.get("prompt", "")).strip()
        if not question:
            question = f"{report.get('title', '')} R{row.get('round', idx)}"
        samples.append(
            {
                "sample_id": f"{run_id}-ragas-r{row.get('round', idx)}-{row.get('persona_id', 'unknown')}",
                "question": question,
                "answer": str(row.get("text", "")),
                "contexts": list(contexts),
                "ground_truth": ground_truth,
                "metadata": {
                    "run_id": run_id,
                    "round": int(row.get("round", idx)),
                    "persona_id": row.get("persona_id"),
                    "seed_id": report.get("seed_id"),
                },
            }
        )
    return samples


def build_trace_events(run_id: str, runlog_rows: list[dict]) -> list[dict]:
    events: list[dict] = []
    for idx, row in enumerate(runlog_rows, start=1):
        events.append(
            {
                "trace_id": f"{run_id}-e{idx}",
                "run_id": run_id,
                "event_index": idx,
                "event_type": str(row.get("type", "unknown")),
                "round": int(row.get("round", 0)) if row.get("round") is not None else 0,
                "payload": row,
            }
        )
    return events


def export_external_eval_bundle(
    run_dir: Path,
    *,
    output_dir: Path | None = None,
    max_contexts: int = 5,
) -> dict:
    run_id = run_dir.name
    runlog_rows = _read_jsonl(run_dir / "runlog.jsonl")
    report = _read_json(run_dir / "report.json")
    eval_payload = _read_json(run_dir / "eval.json")

    promptfoo_cases = build_promptfoo_cases(run_id, runlog_rows)
    ragas_samples = build_ragas_samples(run_id, runlog_rows, report, max_contexts=max_contexts)
    trace_events = build_trace_events(run_id, runlog_rows)

    out_dir = output_dir if output_dir is not None else (run_dir / "eval_exports")
    out_dir.mkdir(parents=True, exist_ok=True)

    promptfoo_path = out_dir / "promptfoo_cases.jsonl"
    ragas_path = out_dir / "ragas_samples.jsonl"
    trace_path = out_dir / "trace_events.jsonl"
    manifest_path = out_dir / "manifest.json"

    _write_jsonl(promptfoo_path, promptfoo_cases)
    _write_jsonl(ragas_path, ragas_samples)
    _write_jsonl(trace_path, trace_events)

    manifest = {
        "schema_version": "external_eval_export.v1",
        "run_id": run_id,
        "run_dir": str(run_dir),
        "generated_from": {
            "has_report": bool(report),
            "has_eval": bool(eval_payload),
            "runlog_rows": len(runlog_rows),
        },
        "counts": {
            "promptfoo_cases": len(promptfoo_cases),
            "ragas_samples": len(ragas_samples),
            "trace_events": len(trace_events),
        },
        "outputs": {
            "promptfoo_cases": str(promptfoo_path),
            "ragas_samples": str(ragas_path),
            "trace_events": str(trace_path),
        },
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest["manifest_path"] = str(manifest_path)
    return manifest
