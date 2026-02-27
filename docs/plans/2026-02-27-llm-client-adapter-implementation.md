# LLM Client Adapter Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 템플릿 기반 comment 생성 경로에 LLM client 어댑터 경계를 추가한다.

**Architecture:** `src/project_dream/llm_client.py`에 `LLMClient` protocol + `EchoLLMClient`를 정의하고, `gen_engine.generate_comment`에서 이를 사용한다.

**Tech Stack:** Python, pytest

---

### Task 1: RED Tests

**Files:**
- Modify: `tests/test_generator.py`

**Step 1: Add failing tests**

- custom fake client를 `generate_comment`에 주입해 결과와 호출 기록을 검증

**Step 2: Run and confirm fail**

Run: `./.venv/bin/python -m pytest tests/test_generator.py -q`  
Expected: FAIL (new parameter/module missing)

### Task 2: Implement Adapter

**Files:**
- Create: `src/project_dream/llm_client.py`
- Modify: `src/project_dream/gen_engine.py`

**Step 1: Add protocol + echo implementation**

**Step 2: Wire generate_comment**

- template prompt 생성 후 llm client로 위임

**Step 3: Run target tests**

Run: `./.venv/bin/python -m pytest tests/test_generator.py -q`  
Expected: PASS

### Task 3: Full Verification + Commit

**Step 1: Run full suite**

Run: `./.venv/bin/python -m pytest -q`  
Expected: all tests pass

**Step 2: Commit**

```bash
git add src/project_dream/llm_client.py src/project_dream/gen_engine.py tests/test_generator.py docs/plans/2026-02-27-llm-client-adapter-design.md docs/plans/2026-02-27-llm-client-adapter-implementation.md
git commit -m "feat: add llm client adapter boundary for comment generation"
```
