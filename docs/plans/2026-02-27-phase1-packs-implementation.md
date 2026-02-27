# Project Dream Phase 1 Packs Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Phase 1 MVP 최소 요구(B01~B18, 4개 커뮤니티, 15+ 룰, 5+ 조직/10+ 인물)를 Pack 파일과 로더 검증으로 구현한다.

**Architecture:** 파일 기반 Pack(JSON) + `pack_service` 검증 계층으로 구성한다. 검증은 참조 무결성과 개수 조건을 보장한다.

**Tech Stack:** Python 3.12+, pytest, stdlib json/dataclass

---

### Task 1: Pack Integration Tests First
- Add failing tests for:
  - pack load success from `packs/`
  - minimum count checks (boards 18, communities 4, rules 15, orgs 5, chars 10)
  - reference checks (community.board_id in boards, persona.main_com in communities)

### Task 2: Expand `pack_service`
- Extend `LoadedPacks` to include all pack domains.
- Load all six pack files from `packs/`.
- Validate:
  - min counts
  - ID uniqueness
  - cross references

### Task 3: Author Phase 1 Pack Data
- Create six pack files with required IDs and minimum data.
- Ensure IDs align with `dev_spec`.

### Task 4: Verification
- Run `pytest -q`.
- Run a direct pack-load smoke command.
- Commit with clear scope message.
