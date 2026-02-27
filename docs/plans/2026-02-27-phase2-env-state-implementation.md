# Project Dream Phase 2A Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 환경 규칙 상태 전이와 근거 로그를 코드와 테스트로 고정한다.

**Architecture:** `env_engine` 상태 전이 함수 중심으로 `sim_orchestrator`가 이벤트를 생성한다.

**Tech Stack:** Python, pytest

---

### Task 1
- 상태/액션 전이 테스트 추가 (RED)

### Task 2
- `env_engine` 상태 전이 API 구현 (GREEN)

### Task 3
- `sim_orchestrator` 연동 + 로그 필드 확장

### Task 4
- E2E 검증 + 커밋
