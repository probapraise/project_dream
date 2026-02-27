import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4


def persist_run(output_dir: Path, sim_result: dict, report: dict) -> Path:
    run_id = datetime.now(UTC).strftime("run-%Y%m%d-%H%M%S") + f"-{uuid4().hex[:6]}"
    run_dir = output_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    with (run_dir / "runlog.jsonl").open("w", encoding="utf-8") as fp:
        for row in sim_result["rounds"]:
            fp.write(json.dumps({"type": "round", **row}, ensure_ascii=False) + "\n")
        for row in sim_result.get("gate_logs", []):
            fp.write(json.dumps({"type": "gate", **row}, ensure_ascii=False) + "\n")
        for row in sim_result.get("action_logs", []):
            fp.write(json.dumps({"type": "action", **row}, ensure_ascii=False) + "\n")

    (run_dir / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (run_dir / "report.md").write_text(f"# Report\n\n{report['summary']}\n", encoding="utf-8")
    return run_dir
