# Project Dream Report V1 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** JSON-first 작가용 리포트(`ReportV1`)를 도입하고 simulate 출력을 새 스키마로 전환한다.

**Architecture:** `ReportV1` 모델 + 규칙 기반 빌더 + Markdown 렌더러.

**Tech Stack:** Python, Pydantic, pytest

---

### Task 1
- `ReportV1` 스키마 테스트 추가 (RED)

### Task 2
- 모델 및 리포트 빌더 구현 (GREEN)

### Task 3
- `storage.py` Markdown 렌더링 확장

### Task 4
- CLI/E2E 테스트 갱신 + 전체 검증
