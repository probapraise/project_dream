import pytest

from project_dream.cli import build_parser, main


def test_cli_supports_simulate_command():
    parser = build_parser()
    args = parser.parse_args(["simulate", "--seed", "seed.json"])
    assert args.command == "simulate"
    assert args.seed == "seed.json"
    assert args.corpus_dir == "corpus"
    assert args.repo_backend == "file"
    assert args.sqlite_db_path is None
    assert args.orchestrator_backend == "manual"
    assert args.vector_backend == "memory"
    assert args.vector_db_path is None


def test_cli_supports_ingest_command():
    parser = build_parser()
    args = parser.parse_args(["ingest"])
    assert args.command == "ingest"
    assert args.packs_dir == "packs"
    assert args.corpus_dir == "corpus"


def test_cli_supports_compile_command():
    parser = build_parser()
    args = parser.parse_args(["compile"])
    assert args.command == "compile"
    assert args.authoring_dir == "authoring"
    assert args.packs_dir == "packs"
    assert args.world_master_export_file is None
    assert args.world_master_export_dir is None


def test_cli_supports_regress_command():
    parser = build_parser()
    args = parser.parse_args(["regress"])
    assert args.command == "regress"
    assert args.corpus_dir == "corpus"
    assert args.orchestrator_backend == "manual"
    assert args.vector_backend == "memory"
    assert args.vector_db_path is None


def test_cli_supports_eval_export_command():
    parser = build_parser()
    args = parser.parse_args(["eval-export"])
    assert args.command == "eval-export"
    assert args.runs_dir == "runs"
    assert args.run_id is None
    assert args.output_dir is None
    assert args.max_contexts == 5
    assert args.repo_backend == "file"
    assert args.sqlite_db_path is None


def test_cli_supports_repository_backend_flags():
    parser = build_parser()

    sim_args = parser.parse_args(
        [
            "simulate",
            "--seed",
            "seed.json",
            "--repo-backend",
            "sqlite",
            "--sqlite-db-path",
            "runs/custom.sqlite3",
            "--vector-backend",
            "sqlite",
            "--vector-db-path",
            "runs/vectors.sqlite3",
        ]
    )
    assert sim_args.repo_backend == "sqlite"
    assert sim_args.sqlite_db_path == "runs/custom.sqlite3"
    assert sim_args.vector_backend == "sqlite"
    assert sim_args.vector_db_path == "runs/vectors.sqlite3"

    eval_args = parser.parse_args(
        [
            "evaluate",
            "--repo-backend",
            "sqlite",
            "--sqlite-db-path",
            "runs/custom.sqlite3",
        ]
    )
    assert eval_args.repo_backend == "sqlite"
    assert eval_args.sqlite_db_path == "runs/custom.sqlite3"

    serve_args = parser.parse_args(
        [
            "serve",
            "--api-token",
            "token",
            "--repo-backend",
            "sqlite",
            "--sqlite-db-path",
            "runs/custom.sqlite3",
            "--vector-backend",
            "sqlite",
            "--vector-db-path",
            "runs/vectors.sqlite3",
        ]
    )
    assert serve_args.repo_backend == "sqlite"
    assert serve_args.sqlite_db_path == "runs/custom.sqlite3"
    assert serve_args.vector_backend == "sqlite"
    assert serve_args.vector_db_path == "runs/vectors.sqlite3"


def test_cli_rejects_unknown_repository_backend():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["simulate", "--seed", "seed.json", "--repo-backend", "unknown"])


def test_cli_supports_orchestrator_backend_flags():
    parser = build_parser()

    sim_args = parser.parse_args(
        [
            "simulate",
            "--seed",
            "seed.json",
            "--orchestrator-backend",
            "langgraph",
        ]
    )
    assert sim_args.orchestrator_backend == "langgraph"

    regress_args = parser.parse_args(
        [
            "regress",
            "--orchestrator-backend",
            "langgraph",
        ]
    )
    assert regress_args.orchestrator_backend == "langgraph"

    regress_live_args = parser.parse_args(
        [
            "regress-live",
            "--orchestrator-backend",
            "langgraph",
        ]
    )
    assert regress_live_args.orchestrator_backend == "langgraph"


def test_cli_rejects_unknown_orchestrator_backend():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["simulate", "--seed", "seed.json", "--orchestrator-backend", "unknown"])


def test_cli_rejects_unknown_vector_backend():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["simulate", "--seed", "seed.json", "--vector-backend", "unknown"])


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
    assert args.diff_output_file == "runs/regressions/regress-live-diff.md"
    assert args.orchestrator_backend == "manual"
    assert args.vector_backend == "memory"
    assert args.vector_db_path is None


def test_cli_vector_defaults_can_be_loaded_from_environment(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PROJECT_DREAM_VECTOR_BACKEND", "sqlite")
    monkeypatch.setenv("PROJECT_DREAM_VECTOR_DB_PATH", "runs/env-vectors.sqlite3")

    parser = build_parser()
    sim_args = parser.parse_args(["simulate", "--seed", "seed.json"])
    regress_args = parser.parse_args(["regress"])
    regress_live_args = parser.parse_args(["regress-live"])
    serve_args = parser.parse_args(["serve", "--api-token", "token"])

    assert sim_args.vector_backend == "sqlite"
    assert sim_args.vector_db_path == "runs/env-vectors.sqlite3"
    assert regress_args.vector_backend == "sqlite"
    assert regress_args.vector_db_path == "runs/env-vectors.sqlite3"
    assert regress_live_args.vector_backend == "sqlite"
    assert regress_live_args.vector_db_path == "runs/env-vectors.sqlite3"
    assert serve_args.vector_backend == "sqlite"
    assert serve_args.vector_db_path == "runs/env-vectors.sqlite3"


def test_cli_rejects_unknown_vector_backend_from_environment(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PROJECT_DREAM_VECTOR_BACKEND", "unknown")
    with pytest.raises(ValueError):
        build_parser()


def test_cli_serve_requires_api_token_when_not_set(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("PROJECT_DREAM_API_TOKEN", raising=False)

    with pytest.raises(SystemExit):
        main(["serve", "--runs-dir", "runs", "--packs-dir", "packs"])
