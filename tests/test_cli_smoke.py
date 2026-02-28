import pytest

from project_dream.cli import build_parser, main


def test_cli_supports_simulate_command():
    parser = build_parser()
    args = parser.parse_args(["simulate", "--seed", "seed.json"])
    assert args.command == "simulate"
    assert args.seed == "seed.json"


def test_cli_supports_regress_live_command_with_defaults():
    parser = build_parser()
    args = parser.parse_args(["regress-live"])
    assert args.command == "regress-live"
    assert args.seeds_dir == "examples/seeds/regression"
    assert args.output_dir == "runs"
    assert args.max_seeds == 2
    assert args.metric_set == "v2"
    assert args.llm_model == "gemini-3.1-flash"


def test_cli_serve_requires_api_token_when_not_set(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("PROJECT_DREAM_API_TOKEN", raising=False)

    with pytest.raises(SystemExit):
        main(["serve", "--runs-dir", "runs", "--packs-dir", "packs"])
