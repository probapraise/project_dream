# Project Dream Run Context Persistence Design

## Goal

시뮬레이션 실행 시 사용한 KB 컨텍스트를 runlog에 함께 저장해, 결과의 재현성과 디버깅 가능성을 높인다.

## Scope

- `simulate_and_persist`/`run_regression_batch`에서 컨텍스트 번들을 `sim_result`에 포함
- `storage.persist_run`이 컨텍스트 row(`type=context`)를 runlog에 기록
- read API 테스트에서 context row 존재 확인

## Approach

### 1) Context Row in runlog (Recommended)

- 설명: 기존 `runlog.jsonl`에 `context` 타입 row를 추가
- 장점: 저장 포맷 추가 최소, read endpoint 변경 없이 즉시 조회 가능
- 단점: runlog 파일 크기 증가 가능

### 2) Separate context.json Artifact

- 설명: run 디렉터리에 별도 파일 저장
- 장점: runlog와 분리되어 가독성 좋음
- 단점: 파일 계약이 늘고 로딩 경로가 분산됨

선택: 1번.

## Data Contract

- runlog context row 예시:
  - `type`: `"context"`
  - `bundle`: retrieve_context 반환 bundle
  - `corpus`: retrieve_context 반환 corpus

## Testing Strategy

- `tests/test_infra_store.py`에 context row 저장 테스트 추가
- `tests/test_web_api.py` read endpoint 테스트에서 context row 존재 검증
