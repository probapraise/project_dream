# Local Ops Automation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 로컬 환경 이동 시 서버 실행/검증을 단일 명령 세트로 고정한다.

**Architecture:** env loader를 가진 bash 스크립트 2개(`dev_serve`, `smoke_api`)를 추가하고, README에 재현 가능한 3분 셋업을 문서화한다.

**Tech Stack:** Bash, curl, Python CLI

---

### Task 1: Add Environment/Script Artifacts

**Files:**
- Modify: `.gitignore`
- Create: `.env.example`
- Create: `scripts/dev_serve.sh`
- Create: `scripts/smoke_api.sh`

### Task 2: Update Documentation

**Files:**
- Modify: `README.md`

### Task 3: Verification + Commit

**Step 1: Verification commands**

Run: `bash -n scripts/dev_serve.sh scripts/smoke_api.sh`  
Run: `/home/ljhljh/project_dream/.venv/bin/python -m pytest -q`  
Run: `PROJECT_DREAM_ENV_FILE=<temp-env> ./scripts/dev_serve.sh` + `./scripts/smoke_api.sh` 실동작 검증

**Step 2: Commit**

```bash
git add .gitignore .env.example scripts/dev_serve.sh scripts/smoke_api.sh README.md docs/plans/2026-02-27-local-ops-automation-design.md docs/plans/2026-02-27-local-ops-automation-implementation.md
git commit -m "feat: add local ops automation scripts for serve and smoke checks"
```
