# Round Summary Stage Implementation Plan

**Goal:** 라운드별 요약 산출물(`round_summaries`)을 시뮬레이션 결과와 runlog에 기록한다.

**Architecture:** `sim_orchestrator`에서 라운드/액션 로그를 후행 집계하고, `storage.persist_run`이 JSONL 이벤트로 직렬화한다.

**Tech Stack:** Python, pytest

---

## Task 1: RED Tests

### Files

- Modify: `tests/test_phase2_simulation_context.py`
- Modify: `tests/test_infra_store.py`

### Step 1: Add failing tests

- 시뮬레이션 결과에 `round_summaries` 존재 검증
- 종료 라운드와 요약 개수 일치 검증
- 저장소가 `round_summary` 타입을 runlog에 기록하는지 검증

### Step 2: Run tests and confirm fail

Run:

```bash
/home/ljhljh/project_dream/.venv/bin/python -m pytest tests/test_phase2_simulation_context.py tests/test_infra_store.py -q
```

Expected: FAIL (`round_summaries`/`round_summary` 미구현)

---

## Task 2: GREEN Implementation

### Files

- Modify: `src/project_dream/sim_orchestrator.py`
- Modify: `src/project_dream/storage.py`

### Step 1: Simulation round summary aggregation

- `_build_round_summaries(round_logs, action_logs)` 추가
- 라운드별 필드 산출
  - `round`
  - `participant_count`
  - `report_events`
  - `policy_events`
  - `status`
  - `max_score`
- 반환 payload에 `round_summaries` 반영

### Step 2: Runlog persistence

- `persist_run`에서 `round_summary` 이벤트 저장

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
