# KB Index Context Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Pack 기반 `kb_index`를 추가하고, 시뮬레이션 경로에서 retrieve된 문맥을 실제 게이트 입력 `corpus`로 사용한다.

**Architecture:** `kb_index.py`에서 인덱스 구성/검색/문맥 번들을 담당한다. `app_service.py`는 인덱스를 생성하고 `run_simulation` 호출 시 검색 corpus를 주입한다.

**Tech Stack:** Python, pytest

---

### Task 1: RED Tests for `kb_index`

**Files:**
- Create: `tests/test_kb_index.py`

**Step 1: Write failing tests**

- `search`가 `board_id`, `zone_id`, `kind` 필터를 반영하는지 검증
- `retrieve_context`가 `bundle`/`corpus`를 반환하고, board/persona 관련 텍스트가 포함되는지 검증

**Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_kb_index.py -q`  
Expected: FAIL (`project_dream.kb_index` 모듈 없음)

### Task 2: Implement Minimal `kb_index`

**Files:**
- Create: `src/project_dream/kb_index.py`

**Step 1: Build index from packs**

- boards/communities/rules/orgs/chars/personas/thread_templates를 passage로 평탄화
- 각 passage에 `kind`, `item_id`, `board_id`, `zone_id`, `persona_id` 메타데이터 부여

**Step 2: Implement search**

- 필터 매칭 + 토큰 겹침 기반 점수
- 점수 내림차순 + 동점 시 안정 정렬

**Step 3: Implement retrieve_context**

- task/seed/board/zone/persona 기반 질의 생성
- `evidence`, `policy`, `organization`, `hierarchy` 카테고리별 top-k 검색
- prompt-ready bundle + simulation용 corpus 반환

**Step 4: Run targeted tests**

Run: `./.venv/bin/python -m pytest tests/test_kb_index.py -q`  
Expected: PASS

### Task 3: Wire Into Simulation Path

**Files:**
- Modify: `src/project_dream/app_service.py`
- Create: `tests/test_app_service_kb_context.py`

**Step 1: Write failing integration test**

- `simulate_and_persist` 실행 시 `run_simulation`이 빈 `corpus` 대신 retrieve된 corpus를 받는지 검증

**Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_app_service_kb_context.py -q`  
Expected: FAIL (현재는 `corpus=[]`)

**Step 3: Minimal implementation**

- `build_index(packs)` 호출
- `retrieve_context(...)` 호출
- 반환된 corpus를 `run_simulation(..., corpus=...)`에 전달

**Step 4: Run targeted tests**

Run: `./.venv/bin/python -m pytest tests/test_app_service_kb_context.py tests/test_phase2_simulation_context.py -q`  
Expected: PASS

### Task 4: Full Verification and Commit

**Step 1: Full suite**

Run: `./.venv/bin/python -m pytest -q`  
Expected: all tests pass

**Step 2: Commit**

```bash
git add src/project_dream/kb_index.py src/project_dream/app_service.py tests/test_kb_index.py tests/test_app_service_kb_context.py docs/plans/2026-02-28-kb-index-context-design.md docs/plans/2026-02-28-kb-index-context-implementation.md
git commit -m "feat: add kb index retrieval and wire simulation context"
```
