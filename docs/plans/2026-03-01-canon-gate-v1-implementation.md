# Canon Gate v1 Implementation (2026-03-01)

## 1) Goal

- 세계관 정합성 게이트(`Canon Gate`)를 추가해 시뮬레이션 이전에 하드 실패시키는 보호막을 만든다.
- 검증 범위:
  - 참조 무결성(ID 존재)
  - 타임라인 일관성(`valid_from/valid_to/era`)
  - 설정 관계 충돌
  - 금칙어(세계관/seed) 위반

---

## 2) Scope

- 신규 모듈:
  - `src/project_dream/canon_gate.py`
- 엔진 연결:
  - `src/project_dream/app_service.py`
  - `src/project_dream/regression_runner.py`
- 스키마/데이터:
  - `src/project_dream/pack_schemas.py`
  - `src/project_dream/pack_service.py`
  - `packs/world_pack.json`
  - `packs/pack_manifest.json`
- 테스트:
  - `tests/test_canon_gate.py`
  - `tests/test_app_service_kb_context.py`
  - `tests/test_regression_runner.py`
  - `tests/test_pack_service.py`

---

## 3) Data Contract Updates

`world_schema.v1` 확장:

- `forbidden_terms: list[str]`
- `relation_conflict_rules: list[{id, relation_type_a, relation_type_b}]`

`world_pack.json`에 기본 값 반영:

- 금칙어: `금서 원문`, `실명 주소`, `인장 위조법`
- 충돌 규칙 예시:
  - `regulates` vs `hostile_to`
  - `allied_with` vs `hostile_to`

---

## 4) Canon Gate Checks

- `canon.reference_integrity`
  - relation/from/to, timeline/entity/location, world_rule/scope 참조 확인
- `canon.timeline_consistency`
  - `valid_from > valid_to` 금지
  - `era` 포맷/범위 일관성 검증
- `canon.relation_conflicts`
  - 동일 edge에서 충돌 relation type 동시 존재 검출
- `canon.glossary_conflicts`
  - 동일 term/alias가 서로 다른 정의를 가지는지 검출
- `canon.seed_forbidden_terms`
  - world/seed 금칙어가 seed 텍스트에 포함되면 실패

실패 시:

- `enforce_canon_gate(...)`가 `ValueError("Canon gate failed: ...")` 발생
- simulate/regress 경로 모두 즉시 중단(하드 게이트)

---

## 5) RED -> GREEN

RED 테스트 추가 후 확인:

```bash
./.venv/bin/pytest -q tests/test_canon_gate.py tests/test_app_service_kb_context.py tests/test_regression_runner.py tests/test_pack_service.py tests/test_pack_service_schema_validation.py
```

GREEN 구현 후 결과:

- `36 passed`

전체 회귀:

```bash
./.venv/bin/pytest -q
```

- `235 passed`

---

## 6) Result

- 엔진은 이제 세계관 스키마 이상/설정 충돌/금칙어 위반을 시뮬레이션 전에 차단한다.
- 대량 세계관 데이터 투입 전 “잘못된 캐논 입력이 runtime까지 전파되는 문제”를 구조적으로 줄였다.
