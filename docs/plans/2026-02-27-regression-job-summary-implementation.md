# Regression Job Summary Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** CI 실행 시 regression 결과를 `$GITHUB_STEP_SUMMARY`에 Markdown으로 남긴다.

**Architecture:** `src/project_dream/regression_summary.py`를 추가해 summary JSON 로딩/렌더링/파일쓰기 책임을 캡슐화하고, workflow에서 모듈 엔트리포인트를 호출한다.

**Tech Stack:** Python, argparse, pytest, GitHub Actions

---

### Task 1: RED Tests for Summary Renderer

**Files:**
- Create: `tests/test_regression_summary.py`
- Test: `tests/test_regression_summary.py`

**Step 1: Write failing tests**

```python
def test_render_markdown_contains_gate_and_totals(tmp_path: Path):
    ...
    markdown = render_summary_markdown(summary)
    assert "Regression Gate Summary" in markdown
```

```python
def test_render_markdown_fallback_when_summary_missing():
    markdown = render_missing_summary_markdown()
    assert "No regression summary found" in markdown
```

**Step 2: Run test to verify fail**

Run: `./.venv/bin/python -m pytest tests/test_regression_summary.py -q`  
Expected: FAIL because module does not exist

### Task 2: GREEN Implementation

**Files:**
- Create: `src/project_dream/regression_summary.py`

**Step 1: Implement minimal functionality**

- latest summary file 선택
- markdown 렌더링 함수
- fallback 메시지 렌더링
- CLI entrypoint (`python -m project_dream.regression_summary`)

**Step 2: Run targeted tests**

Run: `./.venv/bin/python -m pytest tests/test_regression_summary.py -q`  
Expected: PASS

### Task 3: Wire GitHub Workflow

**Files:**
- Modify: `.github/workflows/regression-gate.yml`

**Step 1: Add always-run summary step**

- regress 단계 이후 `if: always()`로 summary 렌더링 step 추가
- output file: `${GITHUB_STEP_SUMMARY}`

**Step 2: Verify full suite**

Run: `./.venv/bin/python -m pytest -q`  
Expected: all tests pass

### Task 4: Commit

```bash
git add src/project_dream/regression_summary.py tests/test_regression_summary.py .github/workflows/regression-gate.yml docs/plans/2026-02-27-regression-job-summary-design.md docs/plans/2026-02-27-regression-job-summary-implementation.md
git commit -m "feat: add regression job summary output for github actions"
```
