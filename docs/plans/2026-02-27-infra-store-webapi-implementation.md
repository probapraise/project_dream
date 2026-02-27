# Infra Store + Web API Scaffold Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 파일 저장소 인터페이스와 Web API 파사드를 추가하고 CLI가 공용 서비스 레이어를 사용하게 만든다.

**Architecture:** `infra/store.py`(repository) + `app_service.py`(use-case) + `infra/web_api.py`(API facade) 구조.

**Tech Stack:** Python, pytest

---

### Task 1: RED Tests for Store + API

**Files:**
- Create: `tests/test_infra_store.py`
- Create: `tests/test_web_api.py`

**Step 1: Add failing tests**

- `FileRunRepository`가 run/eval 저장 및 조회를 수행하는지 검증
- `ProjectDreamAPI`가 `health/simulate/evaluate`를 수행하는지 검증

**Step 2: Run and confirm fail**

Run: `./.venv/bin/python -m pytest tests/test_infra_store.py tests/test_web_api.py -q`  
Expected: FAIL (modules not found)

### Task 2: Implement Infra + Service + API

**Files:**
- Create: `src/project_dream/infra/__init__.py`
- Create: `src/project_dream/infra/store.py`
- Create: `src/project_dream/app_service.py`
- Create: `src/project_dream/infra/web_api.py`

**Step 1: Implement repository interface and file implementation**

**Step 2: Implement service layer functions**

**Step 3: Implement web API facade methods**

### Task 3: Wire CLI to Service Layer

**Files:**
- Modify: `src/project_dream/cli.py`

**Step 1: Replace direct simulate/evaluate flow with service calls**

**Step 2: Keep CLI contract unchanged**

### Task 4: Verification + Commit

**Step 1: Run full tests**

Run: `./.venv/bin/python -m pytest -q`  
Expected: all tests pass

**Step 2: Commit**

```bash
git add src/project_dream/infra/__init__.py src/project_dream/infra/store.py src/project_dream/infra/web_api.py src/project_dream/app_service.py src/project_dream/cli.py tests/test_infra_store.py tests/test_web_api.py docs/plans/2026-02-27-infra-store-webapi-design.md docs/plans/2026-02-27-infra-store-webapi-implementation.md
git commit -m "feat: add infra store and web api scaffolding with shared service layer"
```
