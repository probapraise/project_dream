# P1-4 Register Switch Dataization Implementation (2026-03-01)

## 1) Goal

- 페르소나 레지스터 전환(트리거 -> 화법 전환)을 `persona_pack` 데이터로 관리하도록 전환한다.
- 기본 동작은 유지하고, 규칙 매칭 시에만 프로필 오버레이를 적용해 향후 고도화(P1/P2) 확장 여지를 남긴다.

---

## 2) Data Contract

- `persona_pack.json` 확장:
  - `archetypes[].default_register_profile_id`
  - `register_profiles[]`
  - `register_switch_rules[]`
- 스키마 반영:
  - `ArchetypeRow`, `RegisterProfileRow`, `RegisterSwitchRuleRow`

---

## 3) Runtime Design

- `render_voice()`는 기존 화법 반환을 유지한다.
- 새 함수 `apply_register_switch()`가 런타임 컨텍스트를 받아 규칙 매칭:
  - 입력 컨텍스트: `round_idx`, `dial_dominant_axis`, `meme_phase`, `status`, `total_reports`, `evidence_hours_left`
  - 매칭 순서: `priority desc`, `id asc`
  - 매칭 시 `register_profile`을 오버레이하고 메타 필드 기록
- 시뮬레이터 반영:
  - round row에 `register_profile_id`, `register_rule_id`, `register_switch_applied` 기록

---

## 4) Extensibility Guarantees

- 프로필과 규칙이 pack 데이터로 분리되어 있어, 코드 수정 없이 아래 확장이 가능:
  - 신규 프로필 추가
  - 트리거 조합 변경(상태/증거/밈/다이얼)
  - 우선순위 조정
- 현재는 규칙 매칭 시에만 실제 화법을 바꾸므로 기존 출력 회귀 리스크를 최소화했다.

---

## 5) Verification

타깃:

```bash
./.venv/bin/python -m pytest -q tests/test_persona_service.py tests/test_phase2_simulation_context.py tests/test_pack_service.py tests/test_pack_service_schema_validation.py
```

- 결과: `38 passed`

전체:

```bash
./.venv/bin/python -m pytest -q
```

- 결과: `214 passed`

---

## 6) Changed Files

- `packs/persona_pack.json`
- `packs/pack_manifest.json`
- `src/project_dream/pack_schemas.py`
- `src/project_dream/pack_service.py`
- `src/project_dream/persona_service.py`
- `src/project_dream/sim_orchestrator.py`
- `tests/test_persona_service.py`
- `tests/test_phase2_simulation_context.py`
- `tests/test_pack_service.py`
- `tests/test_pack_service_schema_validation.py`
