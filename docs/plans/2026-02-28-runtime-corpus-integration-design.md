# Runtime Corpus Integration Design

## Goal
`ingest`로 생성한 `corpus/*.jsonl`를 실제 실행 경로(`simulate`, `regress`, `regress-live`)에 주입해, 게이트/회귀가 pack-only 문맥이 아니라 정형 코퍼스까지 참조하도록 만든다.

## Scope
- `app_service.simulate_and_persist`에 `corpus_dir` 입력 추가
- `regression_runner.run_regression_batch`에 `corpus_dir` 입력 추가
- CLI에 `--corpus-dir` 옵션 추가 (`simulate`, `regress`, `regress-live`)

## Data Flow
1. 기존 `retrieve_context(...).corpus`를 생성
2. `load_corpus_texts(corpus_dir)`로 ingest 코퍼스 로딩
3. 두 목록을 순서 유지 + 중복 제거 방식으로 병합
4. 병합 corpus를 `run_simulation(..., corpus=...)`와 `context_corpus`에 동일 반영

## Compatibility
- `corpus_dir` 기본값은 `corpus`
- 디렉토리/파일이 없으면 빈 리스트로 처리되어 기존 동작(pack-only)과 호환
- 기존 API 호출부는 기본값으로 동작

## Verification
- app service: retrieved + ingested 병합 전달 검증
- regression runner: batch 경로 병합 전달 검증
- CLI smoke/live: `--corpus-dir` 파싱/전달 검증
- 전체 회귀: `pytest -q`
