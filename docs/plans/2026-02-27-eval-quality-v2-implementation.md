# Eval Quality V2 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** `metric_set=v2`를 추가해 `v1` 지표를 포함한 확장 지표 3개를 제공한다.

**Architecture:** `eval_suite.py`의 metric registry 확장. v2 계산기는 v1 계산기를 재사용하고 신규 지표를 merge한다.

**Tech Stack:** Python, pytest

---

### Task 1: V2 RED Tests

**Files:**
- Modify: `tests/test_eval_quality_metrics.py`
- Test: `tests/test_eval_quality_metrics.py`

**Step 1: Write the failing test**

```python
def test_eval_quality_v2_metrics_include_v1_and_new_metrics(tmp_path: Path):
    result = evaluate_run(run_dir, metric_set="v2")
    assert result["metric_set"] == "v2"
    assert "moderation_intervention_rate" in result["metrics"]
    assert "lore_pass_rate" in result["metrics"]
```

**Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_eval_quality_metrics.py -q`  
Expected: FAIL because `v2` is unknown

**Step 3: Write minimal implementation**

- `eval_suite.py`에 `_quality_metrics_v2(...)` 추가
- `METRIC_SET_REGISTRY["v2"]` 등록

**Step 4: Run test to verify it passes**

Run: `./.venv/bin/python -m pytest tests/test_eval_quality_metrics.py -q`  
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_eval_quality_metrics.py src/project_dream/eval_suite.py
git commit -m "feat: add eval quality metric-set v2"
```

### Task 2: Unknown Metric Set Contract Test

**Files:**
- Modify: `tests/test_eval_quality_metrics.py`

**Step 1: Adjust unknown metric-set test**

- unknown 값은 `v99`로 변경

**Step 2: Verify**

Run: `./.venv/bin/python -m pytest tests/test_eval_quality_metrics.py -q`  
Expected: PASS with unknown test still raising `ValueError`

**Step 3: Commit**

```bash
git add tests/test_eval_quality_metrics.py
git commit -m "test: keep unknown metric-set contract after v2"
```

### Task 3: Full Regression Verification

**Files:**
- Modify: `README.md` (optional usage line for v2)

**Step 1: Run full test suite**

Run: `./.venv/bin/python -m pytest -q`  
Expected: all tests pass

**Step 2: Smoke evaluate with v2**

Run: `./.venv/bin/python -m project_dream.cli evaluate --runs-dir runs --metric-set v2`  
Expected: latest run에 `metric_set: "v2"` 및 신규 지표 포함

**Step 3: Commit**

```bash
git add README.md
git commit -m "docs: note evaluate metric-set v2 usage"
```
