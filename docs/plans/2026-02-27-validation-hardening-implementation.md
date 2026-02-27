# Validation Hardening Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Safety/Similarity/Lore 게이트를 강화하고 진단 정보(top-k/checklist/warnings)를 제공한다.

**Architecture:** `gate_pipeline.py`의 `run_gates`를 확장해 게이트별 상세 정보를 추가한다. 인터페이스는 유지한다.

**Tech Stack:** Python, pytest, RapidFuzz

---

### Task 1: RED Tests for Hardened Gates

**Files:**
- Modify: `tests/test_gate_pipeline.py`
- Create: `tests/test_gate_pipeline_hardening.py`

**Step 1: Add failing tests**

```python
def test_similarity_gate_reports_top_k_metadata():
    result = run_gates("같은 문장", corpus=["같은 문장", "유사 문장", "다른"], similarity_threshold=85)
    similarity = ...
    assert "top_k" in similarity
```

```python
def test_lore_gate_adds_checklist_and_fails_without_evidence():
    result = run_gates("그냥 느낌", corpus=[])
    lore = ...
    assert lore["checklist"]["evidence_keyword_found"] is False
```

**Step 2: Run tests and confirm fail**

Run: `./.venv/bin/python -m pytest tests/test_gate_pipeline.py tests/test_gate_pipeline_hardening.py -q`  
Expected: FAIL (missing new fields/behavior)

### Task 2: Implement Hardened Gate Logic

**Files:**
- Modify: `src/project_dream/gate_pipeline.py`

**Step 1: Safety warnings metadata**

- `warnings` 필드 추가

**Step 2: Similarity top-k metadata**

- top-k 계산/기록
- 임계치 실패 시 재작성

**Step 3: Lore checklist**

- evidence/context 체크리스트 계산
- evidence 부재 시 실패 + 재작성

**Step 4: Run targeted tests**

Run: `./.venv/bin/python -m pytest tests/test_gate_pipeline.py tests/test_gate_pipeline_hardening.py -q`  
Expected: PASS

### Task 3: Full Verification and Commit

**Step 1: Full suite**

Run: `./.venv/bin/python -m pytest -q`  
Expected: all tests pass

**Step 2: Commit**

```bash
git add src/project_dream/gate_pipeline.py tests/test_gate_pipeline.py tests/test_gate_pipeline_hardening.py docs/plans/2026-02-27-validation-hardening-design.md docs/plans/2026-02-27-validation-hardening-implementation.md
git commit -m "feat: harden safety similarity lore validation gates"
```
