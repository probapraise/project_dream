# Data Ingest + Corpus Formalization Design

## Goal
`packs/*`를 정형 코퍼스(`reference/refined/generated`)로 일관 변환하는 CLI 경로를 추가해, 이후 검색/검증/회귀 파이프라인이 동일 입력 형식을 사용할 수 있게 한다.

## Scope
- 신규 모듈 `data_ingest.py`에서 pack 기반 corpus row 생성
- CLI 서브커맨드 `ingest` 추가
- 산출물 파일 4종 고정
  - `corpus/reference.jsonl`
  - `corpus/refined.jsonl`
  - `corpus/generated.jsonl`
  - `corpus/manifest.json`

## Data Model
각 row는 아래 필드를 필수로 가진다.
- 메타: `zone_id`, `board_id`, `source_type`, `doc_type`, `doc_id`
- 스레드: `thread_id`, `parent_id`, `thread_template_id`, `comment_flow_id`
- 화자/의도: `dial`, `persona_archetype_id`, `author_role`, `stance`, `intent`, `emotion`
- 분류/안전: `topic_tags`, `style_tags`, `toxicity_flag`, `pii_flag`
- 본문: `text`, `notes`

## Mapping Rules
- board pack: `reference` + `refined` 1개씩 생성
- community pack: `reference` + `refined` 1개씩 생성
- rule pack: `reference` 1개 생성
- `generated`는 현재 비워두고 향후 실데이터 적재 경로로 확장

## Error Handling
- `load_packs(..., enforce_phase1_minimums=True)`로 입력 최소조건 미달 시 즉시 실패
- 없는 corpus 파일은 빈 리스트로 처리(`load_corpus_texts`)

## Verification
- 단위 테스트: 파일 생성/스키마 키/카운트 검증
- CLI E2E 테스트: `main(["ingest", ...])` 경로 검증
- 회귀 확인: 전체 `pytest -q`
