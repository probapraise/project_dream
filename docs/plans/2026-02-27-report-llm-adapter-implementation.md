# Report LLM Adapter Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** report 요약/대화후보 생성에 llm client 경계를 추가한다.

**Architecture:** `report_generator.py`에 `llm_client` optional parameter를 도입하고, summary/dialogue line 생성 시 `LLMClient.generate(...)`를 호출한다.

**Tech Stack:** Python, pytest

---

### Task 1: RED Tests

**Files:**
- Modify: `tests/test_report_v1.py`

**Step 1: Add failing test**

- custom fake client 주입 시:
  - summary가 fake output을 사용
  - dialogue candidate line이 fake output을 사용
  - task 호출 기록이 `report_summary`, `report_dialogue_candidate`를 포함

**Step 2: Run and confirm fail**

Run: `./.venv/bin/python -m pytest tests/test_report_v1.py -q`  
Expected: FAIL (build_report_v1 has no llm_client parameter)

### Task 2: GREEN Implementation

**Files:**
- Modify: `src/project_dream/report_generator.py`
- Modify: `src/project_dream/prompt_templates.py`

**Step 1: Add llm client injection**

- `build_report_v1(..., llm_client=None, template_set="v1")`
- summary/dialogue generation 경로에서 client 호출

**Step 2: Add template key**

- `report_dialogue_candidate`

**Step 3: Run target test**

Run: `./.venv/bin/python -m pytest tests/test_report_v1.py -q`  
Expected: PASS

### Task 3: Full Verification + Commit

**Step 1: Full suite**

Run: `./.venv/bin/python -m pytest -q`  
Expected: all tests pass

**Step 2: Commit**

```bash
git add src/project_dream/report_generator.py src/project_dream/prompt_templates.py tests/test_report_v1.py docs/plans/2026-02-27-report-llm-adapter-design.md docs/plans/2026-02-27-report-llm-adapter-implementation.md
git commit -m "feat: extend llm client boundary to report generation"
```
