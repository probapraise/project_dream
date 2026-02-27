# Report Quality Rules Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** `evaluate`에 report 내용 품질 규칙 4개를 추가하고 pass/fail에 반영한다.

**Architecture:** `eval_suite.py`에 `_report_quality_checks_v1(report)` 함수를 추가해 `EvalCheck` 리스트를 반환하고, `evaluate_run`에서 기존 체크 뒤에 합친다.

**Tech Stack:** Python, pytest

---

### Task 1: RED Tests for Report Quality Rules

**Files:**
- Create: `tests/test_eval_report_quality_rules.py`
- Test: `tests/test_eval_report_quality_rules.py`

**Step 1: Write failing tests**

```python
def test_evaluate_includes_report_quality_checks(tmp_path: Path):
    result = evaluate_run(run_dir, metric_set="v1")
    names = {c["name"] for c in result["checks"]}
    assert "report.conflict_map.mediation_points_count" in names
```

```python
def test_evaluate_fails_when_risk_severity_is_invalid(tmp_path: Path):
    ...
    assert result["pass_fail"] is False
```

**Step 2: Run test to verify fails**

Run: `./.venv/bin/python -m pytest tests/test_eval_report_quality_rules.py -q`  
Expected: FAIL because quality checks not implemented

**Step 3: Minimal implementation**

- `eval_suite.py`에 품질 규칙 함수 추가
- `evaluate_run`에서 기존 checks 리스트에 추가

**Step 4: Run test to verify pass**

Run: `./.venv/bin/python -m pytest tests/test_eval_report_quality_rules.py -q`  
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_eval_report_quality_rules.py src/project_dream/eval_suite.py
git commit -m "feat: add report quality checks to evaluate"
```

### Task 2: Full Regression Verification

**Files:**
- Modify: `README.md` (optional note)

**Step 1: Run full tests**

Run: `./.venv/bin/python -m pytest -q`  
Expected: all tests pass

**Step 2: Smoke evaluate**

Run: `./.venv/bin/python -m project_dream.cli evaluate --runs-dir runs --metric-set v2`  
Expected: eval 출력에 report quality check 항목 포함

**Step 3: Commit**

```bash
git add README.md
git commit -m "docs: note report quality checks in evaluate"
```
