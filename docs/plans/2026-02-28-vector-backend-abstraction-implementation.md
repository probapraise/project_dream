# Vector Backend Abstraction Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** KB hybrid retrieval의 dense score 경로를 memory/sqlite 백엔드로 분리해 인프라 확장 포인트를 만든다.

**Architecture:** `kb_index`에 dense backend 프로토콜을 도입하고, 기본값은 기존과 동일한 in-memory backend로 유지한다. sqlite backend는 dense vector를 sqlite 테이블에 적재/조회해 점수를 계산한다.

**Tech Stack:** Python, sqlite3, pytest

---

### Task 1: RED Tests For Backend Abstraction

**Files:**
- Modify: `tests/test_kb_index.py`

**Step 1: Write the failing tests**

- `build_index(..., vector_backend=\"sqlite\", vector_db_path=<tmp>)`가 동작하고 검색 결과를 반환하는지 검증
- memory/sqlite backend 간 대표 쿼리 top 결과 동등성 검증
- 미지원 backend 값 입력 시 `ValueError` 검증

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_kb_index.py -q`

Expected: `build_index` 신규 인자 미지원으로 FAIL.

### Task 2: GREEN Implementation In KB Index

**Files:**
- Modify: `src/project_dream/kb_index.py`

**Step 1: Write minimal implementation**

- dense backend 선택 함수 추가 (`memory`, `sqlite`)
- sqlite backend 헬퍼 추가
  - table 생성
  - dense vector upsert
  - row별 dense vector 조회 + cosine score 계산
- `build_index` 시그니처 확장
  - `vector_backend: str = "memory"`
  - `vector_db_path: Path | None = None`
- `search`에서 dense score를 backend 경로로 계산
- 인덱스 메타에 backend 정보 기록

**Step 2: Run test to verify it passes**

Run: `python -m pytest tests/test_kb_index.py -q`

Expected: PASS.

### Task 3: Integration Verification

**Files:**
- Modify: `docs/plans/2026-02-28-vector-backend-abstraction-handoff.md` (new)

**Step 1: Run integration tests**

Run: `python -m pytest tests/test_web_api.py tests/test_app_service_kb_context.py tests/test_kb_index.py -q`

Expected: PASS.

**Step 2: Run full regression**

Run: `python -m pytest -q`

Expected: PASS.

**Step 3: Commit and prepare PR**

- 변경/검증 결과 handoff 문서 기록
- 커밋, 푸시, PR 생성
