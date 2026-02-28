# Env Engine Policy Matrix Handoff (2026-02-28)

## 1) Done in this session

- Branch/worktree:
  - branch: `feat/env-engine-policy-matrix`
  - worktree: `/home/ljhljh/project_dream/.worktrees/feat-env-engine-policy-matrix`
- Implemented `P0-1 env_engine 확장` baseline:
  - account type policy (`public/alias/mask`) reflected in score and action cost
  - sanction level model (`L1~L5`) with report/severity/status floor
  - appeal matrix handling (`accepted/rejected`) in policy transition
  - tab-specific ranking helper for
    - `latest`
    - `weekly_hot`
    - `evidence_first`
    - `preserve_first`
- Wired simulation loop with minimal policy context:
  - account type / verified / sort tab / sanction level are now propagated into score + transition
  - run outputs include policy-related fields for traceability

## 2) Changed files

- `src/project_dream/env_engine.py`
  - added:
    - `compute_action_cost(...)`
    - `compute_sanction_level(...)`
    - `rank_threads_for_tab(...)`
  - extended:
    - `compute_score(...)` (account_type/sanction_level/sort_tab optional args)
    - `apply_policy_transition(...)` (policy matrix kwargs + sanction level in event)
- `src/project_dream/sim_orchestrator.py`
  - pass account/sanction/tab context into env engine
  - persist policy fields in round/action/moderation/thread state outputs
- `tests/test_env_engine_policy_matrix.py` (new)
  - validates required matrix scenarios from plan

## 3) Verification evidence

- Focused tests:
  - `/home/ljhljh/project_dream/.venv/bin/python -m pytest tests/test_env_engine.py tests/test_env_state_machine.py tests/test_env_engine_policy_matrix.py -q`
  - result: `9 passed`
- Full regression:
  - `/home/ljhljh/project_dream/.venv/bin/python -m pytest -q`
  - result: `108 passed`

## 4) Notes / compatibility

- Existing behavior-dependent tests were preserved.
- `apply_policy_transition(...)` default account type is set to `alias` to keep legacy thresholds unchanged for old call sites.
- New helpers are additive and do not break existing public APIs.

## 5) Recommended next task

- Next planned item from gap register: `P0-2 생성 엔진 Stage1/Stage2 분리`
  - test-first:
    - Stage1 structured output (`claim/evidence/intent`)
    - Stage2 rendering applies voice/style and dial controls
  - then wire into `sim_orchestrator` and update regression assertions.

## 6) Quick resume commands

```bash
cd /home/ljhljh/project_dream/.worktrees/feat-env-engine-policy-matrix
git status
/home/ljhljh/project_dream/.venv/bin/python -m pytest -q
```
