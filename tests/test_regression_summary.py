import json
from pathlib import Path

from project_dream.regression_summary import (
    find_latest_regression_summary,
    render_missing_summary_markdown,
    render_summary_markdown,
)


def test_render_markdown_contains_gate_and_totals():
    summary = {
        "schema_version": "regression.v1",
        "metric_set": "v2",
        "pass_fail": True,
        "totals": {
            "seed_runs": 10,
            "eval_pass_runs": 10,
            "unique_communities": 4,
            "story_checklist_pass_runs": 10,
            "register_switch_runs": 5,
            "register_switch_rate": 0.5,
        },
        "gates": {
            "format_missing_zero": True,
            "community_coverage": True,
            "conflict_frame_runs": True,
            "moderation_hook_runs": True,
            "validation_warning_runs": True,
        },
        "summary_path": "runs/regressions/regression-1.json",
    }

    markdown = render_summary_markdown(summary)

    assert "Regression Gate Summary" in markdown
    assert "PASS" in markdown
    assert "metric_set: `v2`" in markdown
    assert "seed_runs: `10`" in markdown
    assert "story_checklist_pass_runs: `10`" in markdown
    assert "register_switch_runs: `5`" in markdown
    assert "register_switch_rate: `0.5`" in markdown
    assert "`format_missing_zero`" in markdown


def test_render_markdown_fallback_when_summary_missing():
    markdown = render_missing_summary_markdown()

    assert "No regression summary found" in markdown


def test_find_latest_regression_summary_returns_latest_file(tmp_path: Path):
    regressions_dir = tmp_path / "runs" / "regressions"
    regressions_dir.mkdir(parents=True, exist_ok=True)

    old_file = regressions_dir / "regression-20260227-010101-000001.json"
    new_file = regressions_dir / "regression-20260227-010102-000001.json"
    old_file.write_text(json.dumps({"schema_version": "regression.v1"}), encoding="utf-8")
    new_file.write_text(json.dumps({"schema_version": "regression.v1"}), encoding="utf-8")

    latest = find_latest_regression_summary(regressions_dir)

    assert latest == new_file
