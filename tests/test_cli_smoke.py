import pytest

from project_dream.cli import build_parser, main


def test_cli_supports_simulate_command():
    parser = build_parser()
    args = parser.parse_args(["simulate", "--seed", "seed.json"])
    assert args.command == "simulate"
    assert args.seed == "seed.json"


def test_cli_serve_requires_api_token_when_not_set(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("PROJECT_DREAM_API_TOKEN", raising=False)

    with pytest.raises(SystemExit):
        main(["serve", "--runs-dir", "runs", "--packs-dir", "packs"])
