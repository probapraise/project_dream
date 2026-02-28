# Data Ingest + Corpus Formalization Implementation

## Summary
`packs`를 corpus JSONL로 변환하는 ingest 파이프라인을 추가했다. 변환 규칙은 deterministic 하게 고정했으며, CLI에서 단일 명령으로 재생성할 수 있다.

## Files Changed
- `src/project_dream/data_ingest.py` (new)
  - `build_corpus_from_packs(...)`
  - `load_corpus_texts(...)`
- `src/project_dream/cli.py`
  - `ingest` 서브커맨드 및 실행 분기 추가
- `tests/test_data_ingest.py` (new)
- `tests/test_cli_ingest_e2e.py` (new)
- `tests/test_cli_smoke.py`
  - `ingest` parser 기본값 검증 추가
- `README.md`
  - quickstart/ingest 사용법 및 생성 파일 문서화

## Verification Log
- `./.venv/bin/python -m pytest tests/test_data_ingest.py tests/test_cli_ingest_e2e.py tests/test_cli_smoke.py -q`
- `./.venv/bin/python -m pytest -q`
- `PYTHONPATH=src ./.venv/bin/python -m project_dream.cli ingest --packs-dir packs --corpus-dir corpus`

## Current Output Example
- `reference_count=37`
- `refined_count=22`
- `generated_count=0`

## Notes
- `generated.jsonl`은 현재 빈 파일로 유지한다. 추후 외부/실행 결과 데이터를 수집해 채우는 단계에서 동일 스키마를 재사용한다.
- 코퍼스는 `ingest` 명령으로 언제든 재생성 가능하다.
