# Vector Backend Abstraction Handoff (2026-02-28)

## 1) Done in this session

- Target: 인프라 고도화 2차 시작 (벡터 인덱스 백엔드 추상화)
- Implemented in `kb_index`:
  - `build_index(..., vector_backend, vector_db_path)` 시그니처 확장
    - `vector_backend`: `memory` (default), `sqlite`
    - `vector_db_path`: sqlite backend 파일 경로
  - dense vector backend 분기 도입
    - `memory`: 기존 in-memory dense vector 사용
    - `sqlite`: dense vector를 sqlite 테이블(`dense_vectors`)에 upsert 후 조회 캐시로 점수 계산
  - backend 검증 추가 (`unknown` 값은 `ValueError`)
  - index 메타 필드 추가
    - `vector_backend`
    - `vector_db_path`

## 2) Files changed

- `src/project_dream/kb_index.py`
- `tests/test_kb_index.py`
- `docs/plans/2026-02-28-vector-backend-abstraction-implementation.md` (new)
- `docs/plans/2026-02-28-vector-backend-abstraction-handoff.md` (new)

## 3) Verification

- Targeted:
  - `python -m pytest tests/test_kb_index.py -q`
  - result: `9 passed`
- Integration:
  - `python -m pytest tests/test_web_api.py tests/test_app_service_kb_context.py tests/test_kb_index.py -q`
  - result: `25 passed`
- Full:
  - `python -m pytest -q`
  - result: `171 passed`

## 4) Notes

- 기본 backend는 `memory`라 기존 호출 경로와 하위 호환을 유지한다.
- sqlite backend는 확장 포인트 확보 목적의 1차 구현이며, 추후 provider/remote vector DB 연동 전환에 대비한 구조다.

## 5) Next recommended step

- 2차 후속:
  - `ProjectDreamAPI`/CLI에 `vector_backend`, `vector_db_path` 옵션 노출
  - 시뮬레이션/회귀 경로에서 backend 선택을 전달해 운영에서 실제 토글 가능하게 확장
