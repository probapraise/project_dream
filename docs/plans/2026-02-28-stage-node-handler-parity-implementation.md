# Stage Node Handler Parity Implementation Plan

**Goal:** manual/langgraph 백엔드가 동일 stage helper 함수를 실행하도록 `orchestrator_runtime`를 정렬한다.

**Architecture:** runtime에 stage helper + handler resolver를 두고, manual pipeline/langgraph pipeline이 공통 handler를 호출해 stage payload를 조립한다.

**Tech Stack:** Python, pytest

---

## Task 1: RED Tests

### Files

- Modify: `tests/test_orchestrator_runtime.py`

### Step 1: Add failing tests

- manual 백엔드에서 `_run_stage_node_thread_candidate`, `_run_stage_node_end_condition` monkeypatch 결과가 최종 payload에 반영되는지 검증
- langgraph 백엔드에서도 동일 monkeypatch 결과가 반영되는지 검증

### Step 2: Run tests and confirm fail

Run:

```bash
/home/ljhljh/project_dream/.venv/bin/python -m pytest tests/test_orchestrator_runtime.py -q
```

Observed: `AttributeError` (stage helper 함수 미존재)로 2개 테스트 실패.

---

## Task 2: GREEN Implementation

### Files

- Modify: `src/project_dream/orchestrator_runtime.py`

### Step 1: Add stage helper functions

- `_run_stage_node_thread_candidate`
- `_run_stage_node_round_loop`
- `_run_stage_node_moderation`
- `_run_stage_node_end_condition`
- payload 안전 복사를 위한 `_coerce_stage_payload` 추가

### Step 2: Add handler resolver and manual pipeline

- `_resolve_stage_node_handler(node_id)` 추가
- `_run_manual_stage_pipeline(stage_payloads)` 추가
- manual 분기에서 직접 stage helper 실행하도록 변경

### Step 3: Align langgraph pipeline with same handlers

- `_run_langgraph_stage_pipeline` 내부 node 함수에서 동일 handler resolver 결과를 호출하도록 변경

### Step 4: Run targeted tests

Run:

```bash
/home/ljhljh/project_dream/.venv/bin/python -m pytest tests/test_orchestrator_runtime.py tests/test_sim_orchestrator_stage_nodes.py -q
```

Observed: PASS (`14 passed`).

---

## Task 3: Verification

### Step 1: Full regression

Run:

```bash
/home/ljhljh/project_dream/.venv/bin/python -m pytest -q
```

Observed: PASS (`156 passed`).
