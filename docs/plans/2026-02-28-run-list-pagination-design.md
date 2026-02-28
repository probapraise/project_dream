# Project Dream Run List Pagination Design

## Goal

`P2-9` 후속으로 run 메타데이터 조회에 필터/페이지네이션을 도입해, 파일/SQLite 백엔드 모두에서 동일한 조회 계약을 제공한다.

## Scope

- `RunRepository`에 `list_runs(...)` 계약 추가
- `FileRunRepository`/`SQLiteRunRepository` 구현
- `ProjectDreamAPI`에 `list_runs` 노출
- HTTP `GET /runs` 엔드포인트 추가
- 테스트 보강
  - `tests/test_infra_store.py`
  - `tests/test_infra_store_sqlite.py`
  - `tests/test_web_api.py`
  - `tests/test_web_api_http_server.py`

## Query Contract

- query params
  - `limit` (default: 20)
  - `offset` (default: 0)
  - `seed_id` (optional)
  - `board_id` (optional)
  - `status` (optional)
- response
  - `count`, `total`, `limit`, `offset`, `items[]`

## Approach

### 1) Repository-level unified list API (Recommended)

- 저장소 계층에서 필터/페이지네이션을 처리하고 API/HTTP는 단순 전달만 수행
- 장점: 백엔드별 구현 차이를 repository에 캡슐화, 상위 계층 단순화
- 단점: file backend는 runlog/report 스캔이 필요해 조회 비용이 상대적으로 큼

### 2) API 계층에서 필터/페이지네이션 처리

- 장점: 저장소 인터페이스 변경 최소화
- 단점: backend별 데이터 접근 방식 분기가 API로 새어 나와 결합 증가

선택: 1번.
