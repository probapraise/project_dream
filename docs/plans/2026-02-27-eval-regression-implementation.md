# Project Dream Eval Regression Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 구조 회귀 평가를 자동화하여 시뮬레이션 산출물의 안정성을 보장한다.

**Architecture:** `eval_suite.py` + `EvalResult` 모델 + CLI `evaluate`.

**Tech Stack:** Python, pytest, json

---

### Task 1
- 회귀 평가 테스트 추가 (RED)

### Task 2
- `EvalResult` 모델 및 `eval_suite` 구현 (GREEN)

### Task 3
- CLI에 `evaluate` 커맨드 연결 + `eval.json` 저장

### Task 4
- end-to-end 검증 및 문서 갱신
