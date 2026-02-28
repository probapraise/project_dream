# Voice Constraints Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** `render_voice` 결과를 댓글 생성 프롬프트에 반영해 페르소나 말투 제약이 런타임에 사용되도록 만든다.

**Architecture:** `sim_orchestrator`가 보이스 제약을 생성하고 `gen_engine.generate_comment`에 전달한다. `gen_engine`은 compact voice hint를 prompt에 부착한다.

**Tech Stack:** Python, pytest

---

### Task 1: RED Tests

**Files:**
- Modify: `tests/test_generator.py`
- Create: `tests/test_voice_constraints_integration.py`

**Step 1: Add failing tests**

- generator가 `voice_constraints`를 prompt 힌트로 포함하는지
- orchestrator가 `render_voice` 결과를 generate 호출로 넘기는지

**Step 2: Run and confirm fail**

Run: `./.venv/bin/python -m pytest tests/test_generator.py tests/test_voice_constraints_integration.py -q`  
Expected: FAIL (`voice_constraints` 미지원)

### Task 2: Implement Integration

**Files:**
- Modify: `src/project_dream/gen_engine.py`
- Modify: `src/project_dream/sim_orchestrator.py`

**Step 1: `generate_comment` 확장**

- `voice_constraints` optional 인자 추가
- compact voice hint 문자열을 prompt에 추가

**Step 2: `sim_orchestrator` 연결**

- `render_voice` import 및 호출
- `generate_comment(..., voice_constraints=...)` 전달
- round log에 `voice_style` 필드 기록

**Step 3: Run targeted tests**

Run: `./.venv/bin/python -m pytest tests/test_generator.py tests/test_voice_constraints_integration.py -q`  
Expected: PASS

### Task 3: Full Verification and Commit

**Step 1: Full suite**

Run: `./.venv/bin/python -m pytest -q`  
Expected: all tests pass

**Step 2: Commit**

```bash
git add src/project_dream/gen_engine.py src/project_dream/sim_orchestrator.py tests/test_generator.py tests/test_voice_constraints_integration.py docs/plans/2026-02-28-voice-constraints-integration-design.md docs/plans/2026-02-28-voice-constraints-integration-implementation.md
git commit -m "feat: integrate voice constraints into simulation generation path"
```
