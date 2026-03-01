# World Schema v1 Implementation (2026-03-01)

## 1) Goal

- 세계관 데이터를 대량 작성하기 전에 엔진이 요구하는 `World Schema v1` 계약을 고정한다.
- 핵심 메타(`id`, `source`, `valid_from`, `valid_to`, `evidence_grade`)를 모든 세계관 단위에 강제한다.

---

## 2) Scope

- 신규 pack: `packs/world_pack.json`
- schema/loader 반영:
  - `src/project_dream/pack_schemas.py`
  - `src/project_dream/pack_service.py`
  - `packs/pack_manifest.json` checksum 갱신
- 테스트:
  - `tests/test_pack_service.py`
  - `tests/test_pack_service_schema_validation.py`

---

## 3) Data Contract (world_schema.v1)

- top-level
  - `schema_version`, `version`
  - `entities`, `relations`, `timeline_events`, `world_rules`, `glossary`
- 공통 canonical 메타
  - `source`: 근거 출처
  - `valid_from`, `valid_to`: 시점 유효 범위
  - `evidence_grade`: `A/B/C`
- 엔티티 연결
  - entity -> `linked_org_id`, `linked_char_id`, `linked_board_id` (선택)
  - relation/event/rule -> `world entity id` 참조

---

## 4) Runtime Validation Added

- manifest 검증 대상 파일에 `world_pack.json` 포함
- world schema 참조 무결성 검증:
  - relation의 `from_entity_id`, `to_entity_id`
  - timeline event의 `entity_ids`, `location_entity_id`
  - world rule의 `scope_entity_ids`
- 기존 엔진 객체 `LoadedPacks`에 `world_schema` 노출

---

## 5) RED -> GREEN

RED 테스트 추가:

- world schema 로드 계약 검증
- invalid `evidence_grade` 거부
- unknown world relation entity 참조 거부

GREEN 구현 후 확인:

```bash
./.venv/bin/pytest -q tests/test_pack_service.py tests/test_pack_service_schema_validation.py
```

- 결과: `17 passed`

연관:

```bash
./.venv/bin/pytest -q tests/test_phase1_pack_requirements.py tests/test_data_ingest.py tests/test_cli_simulate_e2e.py tests/test_cli_regress_e2e.py
```

- 결과: `11 passed`

전체:

```bash
./.venv/bin/pytest -q
```

- 결과: `228 passed`

---

## 6) Result

- 이제 엔진은 세계관 데이터 입력 시 `world_schema.v1` 계약을 기준으로 구조/참조/근거 메타를 검증한다.
- 다음 단계에서 대규모 세계관 작성 시 “데이터는 많지만 구조가 흔들리는 문제”를 초기에 차단할 수 있다.
