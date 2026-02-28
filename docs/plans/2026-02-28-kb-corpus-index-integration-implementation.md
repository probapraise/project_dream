# KB Corpus Index Integration Implementation

## Summary
KB 인덱스 빌드 경로에 ingest 코퍼스를 연결해 `search`/`retrieve_context`에서 `kind="corpus"` 결과를 사용할 수 있게 했다. Web API에서도 동일 corpus_dir를 통해 반영된다.

## Code Changes
- `src/project_dream/data_ingest.py`
  - `load_corpus_rows(...)` 추가
- `src/project_dream/kb_index.py`
  - `build_index(packs, corpus_dir=None)`로 확장
  - 코퍼스 row를 `kind="corpus"` passage로 적재
  - `retrieve_context` evidence 검색에 `corpus` kind 포함
- `src/project_dream/infra/web_api.py`
  - `ProjectDreamAPI(..., corpus_dir=Path("corpus"))`
  - `simulate/regress/_build_kb_index`에서 corpus_dir 전달

## Tests Added
- `tests/test_kb_index.py`
  - `test_build_index_includes_ingested_corpus_passages`
  - `test_retrieve_context_includes_ingested_corpus_when_available`
- `tests/test_web_api.py`
  - `test_web_api_kb_query_uses_ingested_corpus`

## Verification
- `./.venv/bin/python -m pytest tests/test_kb_index.py tests/test_web_api.py -q`
- `./.venv/bin/python -m pytest -q`

Result: 전체 `104 passed`.
