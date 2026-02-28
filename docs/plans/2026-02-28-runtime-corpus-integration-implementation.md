# Runtime Corpus Integration Implementation

## Summary
시뮬레이션/회귀 실행 시 ingest 코퍼스를 자동 병합하도록 런타임 경로를 확장했다.

## Code Changes
- `src/project_dream/app_service.py`
  - `simulate_and_persist(..., corpus_dir=Path("corpus"))`
  - `regress_and_persist(..., corpus_dir=Path("corpus"))`
  - retrieved corpus + ingested corpus 병합 후 시뮬레이션 전달
- `src/project_dream/regression_runner.py`
  - `run_regression_batch(..., corpus_dir=Path("corpus"))`
  - 배치 시작 시 ingest corpus 로딩, seed별 retrieved corpus와 병합
  - summary `config.corpus_dir` 기록
- `src/project_dream/cli.py`
  - `simulate`, `regress`, `regress-live`에 `--corpus-dir` 옵션 추가
  - 각 실행 경로에서 하위 서비스로 `corpus_dir` 전달

## Tests Added/Updated
- `tests/test_app_service_kb_context.py`
  - `test_simulate_and_persist_merges_ingested_corpus`
- `tests/test_regression_runner.py`
  - `test_run_regression_batch_merges_ingested_corpus`
  - 기존 context 테스트를 corpus-dir 고립 경로로 보정
- `tests/test_cli_smoke.py`
  - `simulate/regress/regress-live`의 `corpus_dir` 기본값 검증
- `tests/test_cli_regress_live.py`
  - live 경로에서 `run_regression_batch` 호출 kwargs에 `corpus_dir` 전달 검증

## Verification
- `./.venv/bin/python -m pytest tests/test_app_service_kb_context.py tests/test_regression_runner.py tests/test_cli_smoke.py tests/test_cli_regress_live.py -q`
- `./.venv/bin/python -m pytest -q`

Result: 전체 `101 passed`.
