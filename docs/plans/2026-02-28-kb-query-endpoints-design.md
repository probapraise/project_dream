# Project Dream KB Query Endpoints Design

## Goal

`dev_spec` 6.2의 조회 API(`search`, `get_pack_item`, `retrieve_context`)를 Web API/HTTP 레이어에서 사용할 수 있도록 노출한다.

## Scope

- `ProjectDreamAPI`에 KB 조회 메서드 추가
  - `search_knowledge`
  - `get_pack_item`
  - `retrieve_context_bundle`
- HTTP 엔드포인트 추가
  - `POST /kb/search`
  - `POST /kb/context`
  - `GET /packs/{pack}/{id}`
- 테스트 추가
  - `tests/test_web_api.py`
  - `tests/test_web_api_http_server.py`

## Approach

### 1) Thin API Wrapper (Recommended)

- 설명: 기존 `kb_index` 함수를 그대로 호출하는 얇은 래퍼를 Web API에 추가
- 장점: 중복 최소, 계약 명확, 구현 속도 빠름
- 단점: 요청마다 packs/index 재구성이 발생

### 2) Stateful Cache Layer

- 설명: API 객체 내부에 index 캐시를 두고 재사용
- 장점: 반복 조회 성능 개선
- 단점: 캐시 무효화 정책 필요

선택: 1번.

## Error Handling

- pack/id 미존재: `FileNotFoundError` -> HTTP 404
- body 필수 필드 누락: `ValueError` -> HTTP 400
- 토큰 인증 규칙은 기존과 동일

## Testing Strategy

- Web API 단위 테스트에서 검색/pack 조회/context 번들 반환 검증
- HTTP 통합 테스트에서 인증 포함 엔드포인트 동작 검증
