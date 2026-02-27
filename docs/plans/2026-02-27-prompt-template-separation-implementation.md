# Prompt Template Separation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 생성/요약/검증 문구를 템플릿 모듈로 분리해 교체 가능한 프롬프트 세트 구조를 만든다.

**Architecture:** `src/project_dream/prompt_templates.py`에 레지스트리/렌더러를 추가하고, `gen_engine`, `report_generator`, `gate_pipeline`에서 해당 렌더러를 호출한다.

**Tech Stack:** Python, pytest

---

### Task 1: RED Tests for Prompt Template Module

**Files:**
- Create: `tests/test_prompt_templates.py`

**Step 1: Write failing tests**

```python
def test_render_prompt_comment_generation_v1():
    text = render_prompt("comment_generation", {...}, template_set="v1")
    assert "R1" in text
```

```python
def test_render_prompt_raises_on_unknown_template_set():
    with pytest.raises(ValueError):
        render_prompt("comment_generation", {}, template_set="v99")
```

**Step 2: Run tests and confirm fail**

Run: `./.venv/bin/python -m pytest tests/test_prompt_templates.py -q`  
Expected: FAIL (`ModuleNotFoundError`)

### Task 2: GREEN Template Module

**Files:**
- Create: `src/project_dream/prompt_templates.py`

**Step 1: Implement registry + renderer**

- `PROMPT_TEMPLATE_REGISTRY`
- `render_prompt(...)`
- unknown set/key 예외 처리

**Step 2: Run targeted tests**

Run: `./.venv/bin/python -m pytest tests/test_prompt_templates.py -q`  
Expected: PASS

### Task 3: Integrate Existing Modules

**Files:**
- Modify: `src/project_dream/gen_engine.py`
- Modify: `src/project_dream/report_generator.py`
- Modify: `src/project_dream/gate_pipeline.py`

**Step 1: Replace hardcoded strings with templates**

- comment 생성 템플릿 호출
- report summary 템플릿 호출
- lore gate reason 템플릿 호출

**Step 2: Run related tests**

Run:
- `./.venv/bin/python -m pytest tests/test_generator.py tests/test_gate_pipeline.py tests/test_report_v1.py -q`

Expected: PASS

### Task 4: Full Verification and Commit

**Step 1: Full suite**

Run: `./.venv/bin/python -m pytest -q`  
Expected: all tests pass

**Step 2: Commit**

```bash
git add src/project_dream/prompt_templates.py src/project_dream/gen_engine.py src/project_dream/report_generator.py src/project_dream/gate_pipeline.py tests/test_prompt_templates.py docs/plans/2026-02-27-prompt-template-separation-design.md docs/plans/2026-02-27-prompt-template-separation-implementation.md
git commit -m "feat: separate prompt templates for generation and validation"
```
