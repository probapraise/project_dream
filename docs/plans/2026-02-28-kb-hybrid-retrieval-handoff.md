# KB Hybrid Retrieval Handoff (2026-02-28)

## 1) Done in this session

- Target: `P1-6 KB retrieval hybrid 고도화`
- Implemented in `kb_index`:
  - sparse score: BM25-lite (`idf + tf + length normalization`)
  - dense score: char n-gram cosine similarity (space-variant robust)
  - hybrid score: `0.65*sparse_norm + 0.35*dense + phrase_bonus`
  - result metadata:
    - `score` (hybrid)
    - `score_sparse`
    - `score_dense`
    - `score_hybrid`
  - indexing precompute:
    - token/tf/doc_len/dense vector/normalized text
    - corpus-level stats(df, avg_doc_len, doc_count)
  - `thread_template` text index에 runtime fields 추가:
    - `title_patterns`, `trigger_tags`, `taboos`

## 2) Files changed

- `src/project_dream/kb_index.py`
- `tests/test_kb_index.py`

## 3) Verification

- Targeted:
  - `pytest tests/test_kb_index.py -q`
  - result: `6 passed`
- Integration:
  - `pytest tests/test_web_api.py tests/test_app_service_kb_context.py tests/test_kb_index.py -q`
  - result: `17 passed`
- Full:
  - `pytest -q`
  - result: `125 passed`

## 4) Behavior notes

- 기존 `score` 필드는 유지되며 의미만 hybrid 점수로 확장됨.
- spacing variant query(예: `정렬이 진실` vs `정렬이진실`)에서 dense 신호로 회복됨.

## 5) Next recommended step

- `P1-7`: Report 생성 결과에 대한 post-generation gate 추가
  - report quality rule failure 시 저장 전 fail-fast/marking 전략 결정
  - regression summary에 report gate 상태 집계 노출.
