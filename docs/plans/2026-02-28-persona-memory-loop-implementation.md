# Persona Memory Loop Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 시뮬레이션 루프에 페르소나 메모를 누적하고 다음 라운드 생성에 반영한다.

**Architecture:** `sim_orchestrator`에서 메모를 관리하고 `gen_engine`의 `generate_comment`에 힌트를 전달한다.

**Tech Stack:** Python, pytest

---

### Task 1: RED Tests for Memory Loop

**Files:**
- Create: `tests/test_persona_memory_loop.py`
- Modify: `tests/test_generator.py`

**Step 1: Write failing tests**

- 2라운드 시뮬레이션에서 동일 페르소나의 2라운드 `memory_hint`가 채워지는지 검증
- `generate_comment`가 `memory_hint`를 프롬프트에 포함하는지 검증

**Step 2: Run tests to confirm fail**

Run: `./.venv/bin/python -m pytest tests/test_persona_memory_loop.py tests/test_generator.py -q`  
Expected: FAIL (`memory_hint` 시그니처/동작 미구현)

### Task 2: Implement Memory Loop

**Files:**
- Modify: `src/project_dream/gen_engine.py`
- Modify: `src/project_dream/sim_orchestrator.py`

**Step 1: `generate_comment` 확장**

- `memory_hint` optional 인자 추가
- 값이 있으면 prompt 뒤에 `memory=...`로 부착

**Step 2: `sim_orchestrator` 메모 누적**

- `persona_memory` dict 추가
- `memory_before`를 생성 호출에 전달
- 라운드 종료 후 `memory_after` 갱신 및 로그 기록
- 반환 payload에 `persona_memory` 포함

**Step 3: Run targeted tests**

Run: `./.venv/bin/python -m pytest tests/test_persona_memory_loop.py tests/test_generator.py -q`  
Expected: PASS

### Task 3: Full Verification and Commit

**Step 1: Full suite**

Run: `./.venv/bin/python -m pytest -q`  
Expected: all tests pass

**Step 2: Commit**

```bash
git add src/project_dream/gen_engine.py src/project_dream/sim_orchestrator.py tests/test_persona_memory_loop.py tests/test_generator.py docs/plans/2026-02-28-persona-memory-loop-design.md docs/plans/2026-02-28-persona-memory-loop-implementation.md
git commit -m "feat: add persona memory loop across simulation rounds"
```
