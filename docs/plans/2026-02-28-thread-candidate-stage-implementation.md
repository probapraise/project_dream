# Thread Candidate Stage Implementation Plan

**Goal:** `run_simulation`에 thread 후보 생성/선정 단계를 추가하고, 저장소 runlog에 해당 이벤트를 기록한다.

**Architecture:** `sim_orchestrator`가 후보/선정 산출물을 만들고, `storage.persist_run`이 JSONL 이벤트로 직렬화한다.

**Tech Stack:** Python, pytest

---

## Task 1: RED Tests

### Files

- Modify: `tests/test_phase2_simulation_context.py`
- Modify: `tests/test_infra_store.py`

### Step 1: Add failing tests

- 시뮬레이션 결과에 `thread_candidates`와 `selected_thread`가 포함되는지 검증
- round row에 `thread_candidate_id`가 들어가는지 검증
- 저장소가 `thread_candidate`/`thread_selected` 타입을 runlog에 저장하는지 검증

### Step 2: Run tests and confirm fail

Run:

```bash
/home/ljhljh/project_dream/.venv/bin/python -m pytest tests/test_phase2_simulation_context.py tests/test_infra_store.py -q
```

Expected: FAIL (`thread_candidates` 미존재, runlog 타입 미기록)

---

## Task 2: GREEN Implementation

### Files

- Modify: `src/project_dream/sim_orchestrator.py`
- Modify: `src/project_dream/storage.py`

### Step 1: Simulation candidate stage

- `_build_thread_candidates` 추가 (기본 3개 deterministic 후보)
- `_select_thread_candidate` 추가 (점수 최대 후보 선택)
- 반환 payload에 `thread_candidates`, `selected_thread` 추가
- round row에 `thread_candidate_id` 추가

### Step 2: Runlog persistence

- `persist_run`에서 `thread_candidate` 이벤트 저장
- `persist_run`에서 `thread_selected` 이벤트 저장

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
