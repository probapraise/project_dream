import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4


def render_report_markdown(report: dict) -> str:
    lines = [
        "# Writer Report",
        "",
        f"- schema: {report.get('schema_version', 'unknown')}",
        f"- seed_id: {report.get('seed_id', 'unknown')}",
        f"- title: {report.get('title', '')}",
        "",
        "## Summary",
        report.get("summary", ""),
        "",
        "## Lens Summaries",
    ]
    for item in report.get("lens_summaries", []):
        lines.append(f"- {item.get('community_id')}: {item.get('summary')}")

    lines.extend(["", "## Highlights Top10"])
    for item in report.get("highlights_top10", []):
        lines.append(f"- R{item.get('round')} {item.get('persona_id')}: {item.get('text')}")

    conflict = report.get("conflict_map", {})
    lines.extend(
        [
            "",
            "## Conflict Map",
            f"- claim_a: {conflict.get('claim_a', '')}",
            f"- claim_b: {conflict.get('claim_b', '')}",
            f"- third_interest: {conflict.get('third_interest', '')}",
            "- mediation_points:",
        ]
    )
    for point in conflict.get("mediation_points", []):
        lines.append(f"  - {point}")

    lines.extend(["", "## Dialogue Candidates"])
    for item in report.get("dialogue_candidates", []):
        lines.append(f"- {item.get('speaker')} ({item.get('tone')}): {item.get('line')}")

    lines.extend(["", "## Foreshadowing"])
    for text in report.get("foreshadowing", []):
        lines.append(f"- {text}")

    lines.extend(["", "## Risk Checks"])
    for item in report.get("risk_checks", []):
        lines.append(f"- [{item.get('severity')}] {item.get('category')}: {item.get('details')}")
    lines.append("")
    return "\n".join(lines)


def persist_run(output_dir: Path, sim_result: dict, report: dict) -> Path:
    run_id = datetime.now(UTC).strftime("run-%Y%m%d-%H%M%S") + f"-{uuid4().hex[:6]}"
    run_dir = output_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    with (run_dir / "runlog.jsonl").open("w", encoding="utf-8") as fp:
        context_bundle = sim_result.get("context_bundle")
        if context_bundle is not None:
            fp.write(
                json.dumps(
                    {
                        "type": "context",
                        "bundle": context_bundle,
                        "corpus": sim_result.get("context_corpus", []),
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

        for row in sim_result.get("thread_candidates", []):
            fp.write(json.dumps({"type": "thread_candidate", **row}, ensure_ascii=False) + "\n")

        selected_thread = sim_result.get("selected_thread")
        if selected_thread is not None:
            fp.write(json.dumps({"type": "thread_selected", **selected_thread}, ensure_ascii=False) + "\n")

        for row in sim_result["rounds"]:
            fp.write(json.dumps({"type": "round", **row}, ensure_ascii=False) + "\n")
        for row in sim_result.get("gate_logs", []):
            fp.write(json.dumps({"type": "gate", **row}, ensure_ascii=False) + "\n")
        for row in sim_result.get("action_logs", []):
            fp.write(json.dumps({"type": "action", **row}, ensure_ascii=False) + "\n")

        for row in sim_result.get("round_summaries", []):
            fp.write(json.dumps({"type": "round_summary", **row}, ensure_ascii=False) + "\n")

        for row in sim_result.get("moderation_decisions", []):
            fp.write(json.dumps({"type": "moderation_decision", **row}, ensure_ascii=False) + "\n")

        end_condition = sim_result.get("end_condition")
        if end_condition is not None:
            fp.write(json.dumps({"type": "end_condition", **end_condition}, ensure_ascii=False) + "\n")

    (run_dir / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (run_dir / "report.md").write_text(render_report_markdown(report), encoding="utf-8")
    return run_dir


def persist_eval(run_dir: Path, eval_result: dict) -> Path:
    output = run_dir / "eval.json"
    output.write_text(json.dumps(eval_result, ensure_ascii=False, indent=2), encoding="utf-8")
    return output
