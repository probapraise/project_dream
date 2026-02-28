# Project Dream SQLite Regression Summary Index Design

## Goal

`P2-9` 후속으로 SQLite 저장소에서 회귀 summary 조회 경로를 파일 스캔 의존에서 DB 인덱스 중심으로 전환한다.

## Scope

- `RunRepository`에 `persist_regression_summary(summary)` 계약 추가
- `SQLiteRunRepository`에 `regression_summaries` 인덱스 테이블 추가
- summary payload를 DB에 함께 저장해 파일 유실 시에도 API 조회 가능하게 보강
- `app_service.regress_and_persist`에서 summary 인덱싱 호출
- 회귀 테스트 보강
  - `tests/test_infra_store_sqlite.py`
  - `tests/test_web_api.py`

## Approach

### 1) DB-first with file-sync fallback (Recommended)

- SQLite는 summary 메타/원문 payload를 DB에 upsert
- 조회 시 DB를 우선 사용하고, 디스크의 `regressions/*.json`은 동기화 소스로 사용
- 장점: API 응답 안정성 향상, 파일 스캔 비용 감소, 파일 유실 내성 확보
- 단점: DB-파일 이중 저장으로 복잡도 소폭 증가

### 2) 파일 스캔 유지 + 캐시만 추가

- 장점: 구조 단순
- 단점: 파일 유실/부분 손상 복구력 낮고 조회 성능 개선 한계

선택: 1번.

## Data Contract

- 신규 table: `regression_summaries`
  - `summary_id` (PK)
  - `summary_path`
  - `generated_at_utc`
  - `metric_set`
  - `pass_fail`
  - `seed_runs`
  - `payload_json`
  - `indexed_at_utc`
