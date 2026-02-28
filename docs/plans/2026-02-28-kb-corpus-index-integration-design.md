# KB Corpus Index Integration Design

## Goal
`ingest`로 생성된 코퍼스를 KB 인덱스에 포함해, 검색(`search_knowledge`)과 문맥 조회(`retrieve_context_bundle`)가 pack-only가 아니라 ingest 코퍼스도 직접 활용하도록 확장한다.

## Scope
- `kb_index.build_index`에 `corpus_dir` 옵션 추가
- 코퍼스 row를 `kind="corpus"` passage로 인덱스에 적재
- `retrieve_context`의 evidence 검색 범위에 `corpus` kind 포함
- `ProjectDreamAPI`에 `corpus_dir` 옵션 추가 및 KB 인덱스 생성 경로 연결

## Data Model
`kind="corpus"` passage 필드:
- `item_id` (`doc_id` 기반)
- `board_id`, `zone_id`
- `source_type` (`reference/refined/generated`)
- `doc_type`
- `text`

## Compatibility
- `corpus_dir` 기본값은 `corpus`
- 코퍼스 파일이 없거나 비어 있어도 기존 pack 기반 검색/문맥은 그대로 동작

## Verification
- `test_kb_index`: corpus passage 인덱싱/검색, retrieve_context 반영 검증
- `test_web_api`: API 경로에서 corpus 검색/문맥 반영 검증
- 전체 회귀: `pytest -q`
