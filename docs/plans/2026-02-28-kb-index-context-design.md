# Project Dream KB Index Context Design

## Goal

`dev_spec` 6.2 요구사항에 맞춰 Pack 기반 지식 검색(`search`)과 시뮬레이션용 문맥 번들(`retrieve_context`)을 MVP 수준으로 제공한다.

## Scope

- 신규 `kb_index` 모듈 추가
  - Pack 데이터에서 검색 가능한 passage 인덱스 구성
  - `search(query, filters, top_k)` 제공
  - `retrieve_context(task, seed, board_id, zone_id, persona_ids, top_k)` 제공
- `app_service.simulate_and_persist`에서 문맥을 로드해 `run_simulation`의 `corpus`로 전달
- 테스트 추가로 검색/문맥 번들/연동 동작 보장

## Approaches

### 1) Lexical-Only Local Index (Recommended)

- 설명: Pack 필드 문자열을 passage로 평탄화하고, 토큰 겹침 기반 점수로 필터 검색
- 장점: 의존성 없이 즉시 구현 가능, 교체 비용 낮음
- 단점: 의미 기반 검색 정확도는 제한적

### 2) BM25 라이브러리 도입

- 설명: BM25 스코어링 라이브러리로 랭킹 품질 개선
- 장점: lexical 검색 품질 개선
- 단점: 의존성 증가, 지금 단계 대비 과도

### 3) Vector/Hybrid 즉시 도입

- 설명: 임베딩 + ANN + 하이브리드 검색
- 장점: 장기 정확도/확장성 우수
- 단점: 현재 MVP 범위 초과

선택: 1번. 이후 2/3번 교체를 위해 인터페이스(`search`, `retrieve_context`)는 고정한다.

## Data Flow

1. `load_packs`로 런타임 Pack 로드
2. `build_index(packs)`로 passage 인덱스 생성
3. `retrieve_context(...)`에서 board/zone/persona 필터와 task 키워드 기반 검색 수행
4. 결과를 `context_bundle` + `corpus` 문자열 목록으로 반환
5. `simulate_and_persist`가 해당 `corpus`를 `run_simulation`으로 전달

## Error Handling

- query가 비어도 필터 기반으로 top-k 반환
- 필터에 맞는 문서가 없으면 빈 결과 반환
- persona가 누락돼도 board/zone 기반 문맥은 유지

## Testing Strategy

- `tests/test_kb_index.py`
  - 필터 검색이 board/zone/type 조건을 반영하는지 검증
  - `retrieve_context`가 prompt-ready bundle과 non-empty corpus를 반환하는지 검증
- `tests/test_app_service_kb_context.py`
  - `simulate_and_persist`가 retrieved corpus를 `run_simulation`으로 전달하는지 검증
