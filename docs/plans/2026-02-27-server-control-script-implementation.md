# Server Control Script Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 운영 제어 명령을 `server_ctl.sh` 하나로 통합해 원클릭 점검 루틴을 제공한다.

**Architecture:** `dev_serve.sh`를 백그라운드로 감싸는 제어 레이어를 스크립트로 추가하고, pid/log/runtime 파일을 통해 상태를 관리한다.

**Tech Stack:** Bash, curl

---

### Task 1: Add Control Script

**Files:**
- Create: `scripts/server_ctl.sh`
- Modify: `.gitignore` (`.runtime/`)

### Task 2: Update Docs

**Files:**
- Modify: `README.md`

### Task 3: Verification + Commit

**Step 1: Verification commands**

- `bash -n scripts/dev_serve.sh scripts/smoke_api.sh scripts/server_ctl.sh`
- `/home/ljhljh/project_dream/.venv/bin/python -m pytest -q`
- 실동작: `server_ctl.sh start/status/check/stop`

**Step 2: Commit**

```bash
git add .gitignore scripts/server_ctl.sh README.md docs/plans/2026-02-27-server-control-script-design.md docs/plans/2026-02-27-server-control-script-implementation.md
git commit -m "feat: add server control script for local ops"
```
