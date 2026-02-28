from pathlib import Path

import pytest

import project_dream.cli as cli


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
        return {"pass_fail": True}

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
    monkeypatch.setattr(cli, "run_regression_batch", lambda **kwargs: {"pass_fail": False})
    rc = cli.main(["regress-live"])
    assert rc == 2
