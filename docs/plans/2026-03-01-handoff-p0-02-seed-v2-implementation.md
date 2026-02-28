# Handoff P0-02 Seed V2 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Expand seed contract so hidden/public facts and constraints are preserved through simulation, persisted per run, and reflected in gate/report outputs.

**Architecture:** Keep existing `SeedInput` compatibility while introducing `EpisodeSeed`-level fields as optional defaults. Propagate seed payload into `sim_result` and run artifacts (`seed.json`, context row). Extend gate/report with minimal seed-constraint hooks so constraints are observable in outputs without breaking current schema contracts.

**Tech Stack:** Python 3.12, Pydantic v2, pytest

---

### Task 1: Seed Model Contract Extension

**Files:**
- Modify: `src/project_dream/models.py`
- Test: `tests/test_models.py`

**Step 1: Write the failing test**

- Add test asserting `SeedInput` accepts and stores:
  - `public_facts`
  - `hidden_facts`
  - `stakeholders`
  - `forbidden_terms`
  - `sensitivity_tags`

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_models.py::test_seed_input_v2_fields_are_supported -v`
Expected: FAIL (unknown fields or missing assertions)

**Step 3: Write minimal implementation**

- Add `EpisodeSeed` model with legacy fields + optional v2 fields.
- Keep `SeedInput` as compatibility subclass of `EpisodeSeed`.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_models.py::test_seed_input_v2_fields_are_supported -v`
Expected: PASS

### Task 2: Persist Seed Raw Payload Per Run

**Files:**
- Modify: `src/project_dream/app_service.py`
- Modify: `src/project_dream/regression_runner.py`
- Modify: `src/project_dream/storage.py`
- Test: `tests/test_cli_simulate_e2e.py`

**Step 1: Write the failing test**

- Extend simulate e2e test to assert:
  - `seed.json` exists in run dir
  - stored `seed_id` matches input

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli_simulate_e2e.py::test_cli_simulate_writes_run_outputs -v`
Expected: FAIL (`seed.json` not found)

**Step 3: Write minimal implementation**

- Add `sim_result["seed"] = seed.model_dump()` in simulate/regress flows before persist.
- In `storage.persist_run`, if `sim_result["seed"]` exists:
  - write `seed.json`
  - include seed payload under context row when context exists.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli_simulate_e2e.py::test_cli_simulate_writes_run_outputs -v`
Expected: PASS

### Task 3: Reflect Seed Constraints in Gate/Report

**Files:**
- Modify: `src/project_dream/gate_pipeline.py`
- Modify: `src/project_dream/sim_orchestrator.py`
- Modify: `src/project_dream/report_generator.py`
- Test: `tests/test_gate_pipeline.py`
- Test: `tests/test_report_v1.py`

**Step 1: Write the failing tests**

- Add gate test: forbidden term configured in seed triggers safety violation.
- Add report test: seed with v2 fields produces `seed_constraints` summary payload.

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_gate_pipeline.py::test_gate_pipeline_blocks_seed_forbidden_term tests/test_report_v1.py::test_report_v1_includes_seed_constraints_summary -v`
Expected: FAIL (unsupported args / missing report field)

**Step 3: Write minimal implementation**

- `run_gates(..., forbidden_terms=None, sensitivity_tags=None)`:
  - detect forbidden term hits
  - emit standardized safety violation
- pass seed-based constraints from orchestrator into gate calls.
- in report builder add `seed_constraints` payload and corresponding risk check when constraints exist.

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_gate_pipeline.py::test_gate_pipeline_blocks_seed_forbidden_term tests/test_report_v1.py::test_report_v1_includes_seed_constraints_summary -v`
Expected: PASS

### Task 4: Regression Safety Check

**Files:**
- Test: existing touched tests only

**Step 1: Run targeted suite**

Run:
- `pytest tests/test_models.py tests/test_gate_pipeline.py tests/test_report_v1.py tests/test_cli_simulate_e2e.py -q`

**Step 2: Run broader smoke**

Run:
- `pytest tests/test_app_service_kb_context.py tests/test_web_api.py -q`

