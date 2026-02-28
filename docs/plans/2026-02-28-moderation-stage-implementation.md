# Moderation Stage Implementation Plan

**Goal:** 시뮬레이션 라운드별 운영 판단을 `moderation_decisions`로 산출하고 runlog에 기록한다.

**Architecture:** `sim_orchestrator`가 라운드 단위 운영 판단을 집계하고, `storage.persist_run`이 `moderation_decision` 이벤트로 직렬화한다.

**Tech Stack:** Python, pytest

---

## Task 1: RED Tests

### Files

- Modify: `tests/test_phase2_simulation_context.py`
- Modify: `tests/test_infra_store.py`

### Step 1: Add failing tests

- 시뮬레이션 결과에 `moderation_decisions`가 존재하는지 검증
- 종료 라운드 수와 결정 수가 일치하는지 검증
- 저장소가 `moderation_decision` 타입을 runlog에 기록하는지 검증

### Step 2: Run tests and confirm fail

Run:

```bash
/home/ljhljh/project_dream/.venv/bin/python -m pytest tests/test_phase2_simulation_context.py tests/test_infra_store.py -q
```

Expected: FAIL (`moderation_decisions`/`moderation_decision` 미구현)

---

## Task 2: GREEN Implementation

### Files

- Modify: `src/project_dream/sim_orchestrator.py`
- Modify: `src/project_dream/storage.py`

### Step 1: Simulation moderation aggregation

- 결과 리스트 `moderation_decisions` 추가
- 라운드 시작 시 `status_before` 저장
- 라운드 내 정책전이 발생 시 마지막 액션/룰 ID 갱신
- 라운드 종료 시 1건 결정 레코드 append

### Step 2: Runlog persistence

- `persist_run`에서 `moderation_decision` 이벤트 저장

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
