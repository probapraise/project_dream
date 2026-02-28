from pathlib import Path

import pytest

import project_dream.cli as cli


def _summary(
    *,
    pass_fail: bool = True,
    seed_runs: int = 2,
    eval_pass_runs: int = 2,
    conflict_frame_runs: int = 2,
    moderation_hook_runs: int = 2,
    validation_warning_runs: int = 2,
    unique_communities: int = 3,
    avg_stage_trace_coverage_rate: float = 1.0,
) -> dict:
    return {
        "pass_fail": pass_fail,
        "metric_set": "v2",
        "totals": {
            "seed_runs": seed_runs,
            "eval_pass_runs": eval_pass_runs,
            "conflict_frame_runs": conflict_frame_runs,
            "moderation_hook_runs": moderation_hook_runs,
            "validation_warning_runs": validation_warning_runs,
            "unique_communities": unique_communities,
            "avg_stage_trace_coverage_rate": avg_stage_trace_coverage_rate,
        },
    }


def test_cli_regress_live_temporarily_overrides_llm_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.setenv("PROJECT_DREAM_LLM_PROVIDER", "echo")
    monkeypatch.setenv("PROJECT_DREAM_LLM_MODEL", "old-model")
    monkeypatch.setenv("PROJECT_DREAM_LLM_RESPONSE_MODE", "prompt_passthrough")
    monkeypatch.setenv("PROJECT_DREAM_LLM_TIMEOUT_SEC", "99")

    seen = {}

    def fake_run_regression_batch(**kwargs):
        seen["provider"] = cli.os.environ.get("PROJECT_DREAM_LLM_PROVIDER")
        seen["model"] = cli.os.environ.get("PROJECT_DREAM_LLM_MODEL")
        seen["response_mode"] = cli.os.environ.get("PROJECT_DREAM_LLM_RESPONSE_MODE")
        seen["timeout"] = cli.os.environ.get("PROJECT_DREAM_LLM_TIMEOUT_SEC")
        seen["kwargs"] = kwargs
        return _summary()

    monkeypatch.setattr(cli, "run_regression_batch", fake_run_regression_batch)

    rc = cli.main(
        [
            "regress-live",
            "--seeds-dir",
            str(tmp_path / "seeds"),
            "--packs-dir",
            "packs",
            "--output-dir",
            str(tmp_path / "runs"),
        ]
    )

    assert rc == 0
    assert seen["provider"] == "google"
    assert seen["model"] == "gemini-3.1-flash"
    assert seen["response_mode"] == "model_output"
    assert seen["timeout"] == "60"
    assert seen["kwargs"]["max_seeds"] == 2
    assert seen["kwargs"]["metric_set"] == "v2"

    assert cli.os.environ.get("PROJECT_DREAM_LLM_PROVIDER") == "echo"
    assert cli.os.environ.get("PROJECT_DREAM_LLM_MODEL") == "old-model"
    assert cli.os.environ.get("PROJECT_DREAM_LLM_RESPONSE_MODE") == "prompt_passthrough"
    assert cli.os.environ.get("PROJECT_DREAM_LLM_TIMEOUT_SEC") == "99"


def test_cli_regress_live_returns_nonzero_when_regression_fails(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(cli, "run_regression_batch", lambda **kwargs: _summary(pass_fail=False))
    rc = cli.main(["regress-live"])
    assert rc == 2


def test_cli_regress_live_updates_baseline_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    baseline = tmp_path / "baseline.json"
    monkeypatch.setattr(cli, "run_regression_batch", lambda **kwargs: _summary())

    rc = cli.main(
        [
            "regress-live",
            "--baseline-file",
            str(baseline),
            "--update-baseline",
        ]
    )

    assert rc == 0
    assert baseline.exists()
    payload = cli.json.loads(baseline.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "regress_live_baseline.v1"
    assert payload["metrics"]["eval_pass_rate"] == 1.0
    assert payload["metrics"]["unique_communities"] == 3


def test_cli_regress_live_returns_nonzero_when_baseline_degrades(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    baseline = tmp_path / "baseline.json"
    baseline.write_text(
        cli.json.dumps(
            {
                "schema_version": "regress_live_baseline.v1",
                "metrics": {
                    "eval_pass_rate": 1.0,
                    "conflict_frame_rate": 1.0,
                    "moderation_hook_rate": 1.0,
                    "validation_warning_rate": 1.0,
                    "avg_stage_trace_coverage_rate": 1.0,
                    "unique_communities": 3,
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        cli,
        "run_regression_batch",
        lambda **kwargs: _summary(
            eval_pass_runs=1,
            conflict_frame_runs=1,
            moderation_hook_runs=1,
            validation_warning_runs=1,
            unique_communities=1,
            avg_stage_trace_coverage_rate=0.5,
        ),
    )

    rc = cli.main(
        [
            "regress-live",
            "--baseline-file",
            str(baseline),
            "--allowed-rate-drop",
            "0.0",
            "--allowed-community-drop",
            "0",
        ]
    )

    assert rc == 3
