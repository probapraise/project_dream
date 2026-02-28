# Persona Pack Casting Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Pack 기반 참가자 캐스팅과 `render_voice` API를 추가해 시뮬레이션의 페르소나 일관성을 높인다.

**Architecture:** `persona_service.py`에 캐스팅/보이스 제약 로직을 집중한다. `sim_orchestrator.py`는 packs 전달만 추가한다.

**Tech Stack:** Python, pytest

---

### Task 1: RED Tests for Persona Casting

**Files:**
- Create: `tests/test_persona_service.py`
- Modify: `tests/test_phase2_simulation_context.py`

**Step 1: Write failing tests**

- packs 기반 선택 시 board/zone 우선 페르소나가 먼저 나오는지 검증
- `render_voice`가 constraint 필드를 반환하는지 검증
- 시뮬레이션 결과의 `persona_id`가 packs 사용 시 `P` 접두를 갖는지 검증

**Step 2: Run tests to confirm fail**

Run: `./.venv/bin/python -m pytest tests/test_persona_service.py tests/test_phase2_simulation_context.py -q`  
Expected: FAIL (`render_voice` 미구현, 기존 캐스팅 로직 미충족)

### Task 2: Implement Persona Service Enhancement

**Files:**
- Modify: `src/project_dream/persona_service.py`
- Modify: `src/project_dream/sim_orchestrator.py`

**Step 1: Pack-aware select_participants**

- `packs` optional 인자 추가
- 후보군 우선순위(보드+존 > 보드 > 기타)
- seed/round 해시 기반 결정론적 회전

**Step 2: Add render_voice**

- archetype 스타일별 템플릿 사전 정의
- `sentence_length/endings/frequent_words/taboo_words` 반환

**Step 3: Orchestrator wiring**

- `select_participants(..., packs=packs)`로 연동

**Step 4: Run targeted tests**

Run: `./.venv/bin/python -m pytest tests/test_persona_service.py tests/test_phase2_simulation_context.py -q`  
Expected: PASS

### Task 3: Full Verification and Commit

**Step 1: Full suite**

Run: `./.venv/bin/python -m pytest -q`  
Expected: all tests pass

**Step 2: Commit**

```bash
git add src/project_dream/persona_service.py src/project_dream/sim_orchestrator.py tests/test_persona_service.py tests/test_phase2_simulation_context.py docs/plans/2026-02-28-persona-pack-casting-design.md docs/plans/2026-02-28-persona-pack-casting-implementation.md
git commit -m "feat: add pack-aware persona casting and voice constraints"
```
