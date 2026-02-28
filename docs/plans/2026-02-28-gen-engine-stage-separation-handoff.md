# Gen Engine Stage Separation Handoff (2026-02-28)

## 1) Done in this session

- Target: `P0-2 생성 엔진 Stage1/Stage2 분리`
- Implemented:
  - Stage1 planning step added in `gen_engine`:
    - structured payload fields: `claim`, `evidence`, `intent`, `dial`
    - task route: `comment_stage1`
    - JSON output parsing + deterministic fallback
  - Stage2 rendering step added:
    - renders final comment text from Stage1 structure
    - voice/style + memory + dial hint reflected in prompt
    - task route remains `comment_generation` for compatibility
  - Stage trace capture wired:
    - `gen_engine` stores last generation trace
    - `sim_orchestrator` writes `generation_stage1`, `generation_stage2` into each round log row
  - Prompt templates extended:
    - `comment_stage1_plan`
    - `comment_stage2_render`

## 2) Files changed

- `src/project_dream/gen_engine.py`
- `src/project_dream/prompt_templates.py`
- `src/project_dream/sim_orchestrator.py`
- `tests/test_generator.py`
- `tests/test_prompt_templates.py`
- `tests/test_phase2_simulation_context.py`

## 3) Root-cause fix during implementation

- Symptom:
  - 일부 Phase2 테스트에서 신고/정책 전이 이벤트가 사라짐
- Root cause:
  - Stage1 fallback evidence 문구가 lore gate 키워드를 항상 포함해 (`근거`) 신고가 누적되지 않음
- Fix:
  - fallback evidence 문구를 lore 키워드 비포함 표현으로 조정
  - 기존 시뮬레이션 전이 동작 회복

## 4) Verification

- Focused:
  - `pytest tests/test_generator.py tests/test_prompt_templates.py tests/test_phase2_simulation_context.py::test_simulation_emits_generation_stage_trace_fields -q`
  - `11 passed`
  - `pytest tests/test_persona_memory_loop.py tests/test_voice_constraints_integration.py tests/test_phase2_simulation_context.py -q`
  - `12 passed`
- Full:
  - `pytest -q`
  - `112 passed`

## 5) Current status against P0

- `P0-1 env_engine 확장`: done
- `P0-2 생성 엔진 Stage1/Stage2 분리`: done (this session)
- Next recommended: `P0-3 Gate pipeline 고도화`
  - rule-id 기반 정합성 리포트 정밀화
  - consistency checker를 룰/엔티티 참조형으로 보강

