import pytest

from project_dream.cli import build_parser, main


def test_cli_supports_simulate_command():
    parser = build_parser()
    args = parser.parse_args(["simulate", "--seed", "seed.json"])
    assert args.command == "simulate"
    assert args.seed == "seed.json"
    assert args.corpus_dir == "corpus"


def test_cli_supports_ingest_command():
    parser = build_parser()
    args = parser.parse_args(["ingest"])
    assert args.command == "ingest"
    assert args.packs_dir == "packs"
    assert args.corpus_dir == "corpus"


def test_cli_supports_regress_command():
    parser = build_parser()
    args = parser.parse_args(["regress"])
    assert args.command == "regress"
    assert args.corpus_dir == "corpus"


def test_cli_supports_eval_export_command():
    parser = build_parser()
    args = parser.parse_args(["eval-export"])
    assert args.command == "eval-export"
    assert args.runs_dir == "runs"
    assert args.run_id is None
    assert args.output_dir is None
    assert args.max_contexts == 5


def test_cli_supports_regress_live_command_with_defaults():
    parser = build_parser()
    args = parser.parse_args(["regress-live"])
    assert args.command == "regress-live"
    assert args.seeds_dir == "examples/seeds/regression"
    assert args.output_dir == "runs"
    assert args.corpus_dir == "corpus"
    assert args.max_seeds == 2
    assert args.metric_set == "v2"
    assert args.llm_model == "gemini-3.1-flash"
    assert args.baseline_file == "runs/regressions/regress-live-baseline.json"


def test_cli_serve_requires_api_token_when_not_set(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("PROJECT_DREAM_API_TOKEN", raising=False)

    with pytest.raises(SystemExit):
        main(["serve", "--runs-dir", "runs", "--packs-dir", "packs"])
