# Project Dream Regression Summary List Filters Design

## Goal

`/regressions` 목록 조회를 DB 인덱스 중심으로 확장해 `offset/metric_set/pass_fail` 필터와 일관된 페이지 응답(`count/total/limit/offset`)을 제공한다.

## Scope

- `RunRepository.list_regression_summaries(...)` 계약 확장
  - `limit`, `offset`, `metric_set`, `pass_fail`
- `FileRunRepository`/`SQLiteRunRepository` 구현 확장
- `ProjectDreamAPI.list_regression_summaries(...)` 확장
- HTTP `GET /regressions` query 확장
- 테스트 보강
  - `tests/test_infra_store.py`
  - `tests/test_infra_store_sqlite.py`
  - `tests/test_web_api.py`
  - `tests/test_web_api_http_server.py`

## Query Contract

- Query params:
  - `limit` (optional)
  - `offset` (default: 0)
  - `metric_set` (optional)
  - `pass_fail` (optional: `true/false/1/0/yes/no`)
- Response fields:
  - `count`, `total`, `limit`, `offset`, `items`

## Approach

### 1) Repository-first filtering/pagination (Recommended)

- 필터/페이지 계산을 저장소 계층에서 수행하고 API/HTTP는 전달만 담당
- 장점: backend(file/sqlite)별 차이를 캡슐화하고 상위 계층 단순화
- 단점: file backend는 여전히 JSON 스캔 비용이 존재

### 2) HTTP/API에서 필터 처리

- 장점: 저장소 인터페이스 변경 최소
- 단점: 백엔드별 분기가 API 계층으로 노출되어 결합 증가

선택: 1번.
