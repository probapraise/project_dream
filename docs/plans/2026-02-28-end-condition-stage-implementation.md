# End Condition Stage Implementation Plan

**Goal:** 시뮬레이션 종료 사유/종료 라운드를 결과와 runlog에 기록한다.

**Architecture:** `sim_orchestrator`에서 종료 조건을 결정하고, `storage.persist_run`에서 `end_condition` 이벤트를 직렬화한다.

**Tech Stack:** Python, pytest

---

## Task 1: RED Tests

### Files

- Modify: `tests/test_phase2_simulation_context.py`
- Modify: `tests/test_infra_store.py`

### Step 1: Add failing tests

- 기본 종료 시 `thread_state.termination_reason == round_limit`
- 잠금 상태 도달 시 조기 종료 + `termination_reason == moderation_lock`
- 저장소가 `end_condition` 타입을 runlog에 기록

### Step 2: Run tests and confirm fail

Run:

```bash
/home/ljhljh/project_dream/.venv/bin/python -m pytest tests/test_phase2_simulation_context.py tests/test_infra_store.py -q
```

Expected: FAIL (종료 필드/이벤트 미구현)

---

## Task 2: GREEN Implementation

### Files

- Modify: `src/project_dream/sim_orchestrator.py`
- Modify: `src/project_dream/storage.py`

### Step 1: Simulation end-condition logic

- 상태가 `locked/ghost/sanctioned`면 즉시 조기 종료
- 종료 메타데이터 생성
  - `termination_reason`
  - `ended_round`
  - `ended_early`
  - `status`
- 결과 payload 및 `thread_state`에 반영

### Step 2: Runlog persistence

- `persist_run`에서 `end_condition` 이벤트 저장

### Step 3: Run targeted tests

Run:

```bash
/home/ljhljh/project_dream/.venv/bin/python -m pytest tests/test_phase2_simulation_context.py tests/test_infra_store.py -q
```

Expected: PASS

---

## Task 3: Verification

### Step 1: Regression-sensitive tests

Run:

```bash
/home/ljhljh/project_dream/.venv/bin/python -m pytest tests/test_orchestrator.py tests/test_cli_simulate_e2e.py tests/test_web_api.py tests/test_web_api_http_server.py tests/test_eval_suite.py tests/test_regression_runner.py -q
```

Expected: PASS

### Step 2: Full suite

Run:

```bash
/home/ljhljh/project_dream/.venv/bin/python -m pytest -q
```

Expected: all tests pass
