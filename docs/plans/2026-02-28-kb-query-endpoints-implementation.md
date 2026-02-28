# KB Query Endpoints Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** KB 검색/컨텍스트/Pack 조회를 HTTP API로 제공한다.

**Architecture:** `infra/web_api.py`에 KB 래퍼 메서드를 추가하고 `infra/http_server.py` 라우팅에 매핑한다.

**Tech Stack:** Python, pytest

---

### Task 1: RED Tests

**Files:**
- Modify: `tests/test_web_api.py`
- Modify: `tests/test_web_api_http_server.py`

**Step 1: Add failing tests**

- Web API 메서드 3종(search/get_pack_item/retrieve_context_bundle) 검증
- HTTP 엔드포인트(`/kb/search`, `/kb/context`, `/packs/{pack}/{id}`) 검증

**Step 2: Run and confirm fail**

Run: `./.venv/bin/python -m pytest tests/test_web_api.py tests/test_web_api_http_server.py -q`  
Expected: FAIL (메서드/라우트 미구현)

### Task 2: Implement Endpoints

**Files:**
- Modify: `src/project_dream/infra/web_api.py`
- Modify: `src/project_dream/infra/http_server.py`

**Step 1: Web API methods**

- packs 로드 + index 구성 헬퍼 추가
- `search_knowledge`
- `get_pack_item`
- `retrieve_context_bundle`

**Step 2: HTTP routes**

- `POST /kb/search`
- `POST /kb/context`
- `GET /packs/{pack}/{id}`

**Step 3: Run targeted tests**

Run: `./.venv/bin/python -m pytest tests/test_web_api.py tests/test_web_api_http_server.py -q`  
Expected: PASS

### Task 3: Full Verification and Commit

**Step 1: Full suite**

Run: `./.venv/bin/python -m pytest -q`  
Expected: all tests pass

**Step 2: Commit**

```bash
git add src/project_dream/infra/web_api.py src/project_dream/infra/http_server.py tests/test_web_api.py tests/test_web_api_http_server.py docs/plans/2026-02-28-kb-query-endpoints-design.md docs/plans/2026-02-28-kb-query-endpoints-implementation.md
git commit -m "feat: add kb query and pack lookup http endpoints"
```
