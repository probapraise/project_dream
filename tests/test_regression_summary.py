import json
from pathlib import Path

from project_dream.regression_summary import (
    find_latest_regression_summary,
    render_missing_summary_markdown,
    render_summary_markdown,
    write_job_summary,
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
            "cross_inflow_runs": 6,
            "cross_inflow_rate": 0.6,
            "meme_flow_runs": 8,
            "meme_flow_rate": 0.8,
            "avg_culture_dial_alignment_rate": 0.7,
            "avg_culture_weight": 1.1,
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
    assert "cross_inflow_runs: `6`" in markdown
    assert "cross_inflow_rate: `0.6`" in markdown
    assert "meme_flow_runs: `8`" in markdown
    assert "meme_flow_rate: `0.8`" in markdown
    assert "avg_culture_dial_alignment_rate: `0.7`" in markdown
    assert "avg_culture_weight: `1.1`" in markdown
    assert "`format_missing_zero`" in markdown


def test_render_markdown_includes_regress_live_diff_path_when_present():
    summary = {
        "schema_version": "regression.v1",
        "metric_set": "v2",
        "pass_fail": True,
        "totals": {},
        "gates": {},
        "summary_path": "runs/regressions/regression-1.json",
        "regress_live_diff_path": "runs/regressions/regress-live-diff.md",
    }

    markdown = render_summary_markdown(summary)

    assert "regress_live_diff_path: `runs/regressions/regress-live-diff.md`" in markdown


def test_render_markdown_includes_regress_live_diff_brief_when_present():
    summary = {
        "schema_version": "regression.v1",
        "metric_set": "v2",
        "pass_fail": True,
        "totals": {},
        "gates": {},
        "regress_live_diff_brief": {
            "status": "FAIL",
            "top_failures": [
                "eval_pass_rate: current=0.5000 baseline=1.0000 allowed_drop=0.0000",
                "unique_communities: current=1 baseline=3 allowed_drop=0",
            ],
        },
    }

    markdown = render_summary_markdown(summary)

    assert "### Regress-Live Diff Brief" in markdown
    assert "status: **FAIL**" in markdown
    assert "eval_pass_rate: current=0.5000 baseline=1.0000 allowed_drop=0.0000" in markdown
    assert "unique_communities: current=1 baseline=3 allowed_drop=0" in markdown


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


def test_write_job_summary_includes_regress_live_diff_link_when_file_exists(tmp_path: Path):
    regressions_dir = tmp_path / "runs" / "regressions"
    regressions_dir.mkdir(parents=True, exist_ok=True)

    summary_file = regressions_dir / "regression-20260227-010102-000001.json"
    summary_file.write_text(
        json.dumps(
            {
                "schema_version": "regression.v1",
                "metric_set": "v2",
                "pass_fail": True,
                "totals": {"seed_runs": 1, "eval_pass_runs": 1},
                "gates": {"format_missing_zero": True},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    diff_file = regressions_dir / "regress-live-diff.md"
    diff_file.write_text("## Regress-Live Baseline Diff\n", encoding="utf-8")

    out = tmp_path / "summary.md"
    write_job_summary(regressions_dir, out)
    content = out.read_text(encoding="utf-8")

    assert "regress_live_diff_path" in content
    assert str(diff_file) in content


def test_write_job_summary_includes_regress_live_diff_brief_when_failures_exist(tmp_path: Path):
    regressions_dir = tmp_path / "runs" / "regressions"
    regressions_dir.mkdir(parents=True, exist_ok=True)

    summary_file = regressions_dir / "regression-20260227-010102-000001.json"
    summary_file.write_text(
        json.dumps(
            {
                "schema_version": "regression.v1",
                "metric_set": "v2",
                "pass_fail": True,
                "totals": {"seed_runs": 1, "eval_pass_runs": 1},
                "gates": {"format_missing_zero": True},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    diff_file = regressions_dir / "regress-live-diff.md"
    diff_file.write_text(
        "\n".join(
            [
                "## Regress-Live Baseline Diff",
                "",
                "- status: **FAIL**",
                "",
                "### Failures",
                "- eval_pass_rate: current=0.5000 baseline=1.0000 allowed_drop=0.0000",
                "- unique_communities: current=1 baseline=3 allowed_drop=0",
                "",
            ]
        ),
        encoding="utf-8",
    )

    out = tmp_path / "summary.md"
    write_job_summary(regressions_dir, out)
    content = out.read_text(encoding="utf-8")

    assert "### Regress-Live Diff Brief" in content
    assert "status: **FAIL**" in content
    assert "eval_pass_rate: current=0.5000 baseline=1.0000 allowed_drop=0.0000" in content
