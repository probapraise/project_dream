# Regression CI Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** PR/메인 푸시 시 `pytest` + `regress`를 자동 실행하고 결과 artifact를 보존한다.

**Architecture:** GitHub Actions 단일 workflow job에서 테스트와 회귀 게이트를 직렬 실행한다.

**Tech Stack:** GitHub Actions, Python 3.12, pip

---

### Task 1: Add Regression Gate Workflow

**Files:**
- Create: `.github/workflows/regression-gate.yml`

**Step 1: Create workflow skeleton**

- `name`, `on`, `jobs` 기본 틀 작성

**Step 2: Add CI steps**

- checkout
- setup-python 3.12
- pip upgrade + `pip install -e .`
- `python -m pytest -q`
- `python -m project_dream.cli regress ... --metric-set v2`

**Step 3: Add artifact upload**

- `actions/upload-artifact`
- 실패 시에도 업로드(`if: always()`)

**Step 4: Local sanity check**

Run:
- `./.venv/bin/python -m pytest -q`
- `./.venv/bin/python -m project_dream.cli regress --seeds-dir examples/seeds/regression --output-dir runs --max-seeds 10 --metric-set v2`

Expected:
- tests pass
- regress exit code 0

### Task 2: Update Readme CI Note

**Files:**
- Modify: `README.md`

**Step 1: Add short CI section**

- PR에서 자동 회귀 게이트가 동작한다는 안내

**Step 2: Re-run verification**

Run: `./.venv/bin/python -m pytest -q`  
Expected: all tests pass

### Task 3: Commit

**Step 1: Commit workflow and docs**

```bash
git add .github/workflows/regression-gate.yml README.md docs/plans/2026-02-27-regression-ci-design.md docs/plans/2026-02-27-regression-ci-implementation.md
git commit -m "ci: add regression gate workflow for pytest and regress"
```
