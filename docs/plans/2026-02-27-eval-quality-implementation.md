# Project Dream Eval Quality V1 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** `evaluate`에 품질 지표 세트 v1을 추가하고 향후 v2 확장을 위한 레지스트리 구조를 도입한다.

**Architecture:** `eval_suite` 내부 metric-set registry + CLI option forwarding.

**Tech Stack:** Python, pytest

---

### Task 1
- v1 지표 테스트 추가 (RED)

### Task 2
- metric registry와 v1 계산기 구현 (GREEN)

### Task 3
- CLI `--metric-set` 옵션 추가 및 eval 결과 반영

### Task 4
- 전체 회귀 테스트 및 simulate/evaluate 실검증
