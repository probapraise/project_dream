# Project Dream Server Control Script Design

## Goal

서버 운영 동작을 단일 스크립트로 표준화해 환경 변경 시에도 start/stop/check 흐름을 일관되게 유지한다.

## Scope

- `scripts/server_ctl.sh` 추가
- 명령: `start|stop|status|restart|logs|check`
- PID 파일/로그 파일 관리
- `check`에서 `smoke_api.sh` 자동 연동

## Runtime Contract

- runtime 경로: `.runtime/`
  - PID: `.runtime/project_dream_server.pid`
  - 로그: `.runtime/project_dream_server.log`
- `start`:
  - 이미 실행 중이면 재기동하지 않음
  - `dev_serve.sh`를 백그라운드로 시작
  - startup wait 후 프로세스 생존 확인
- `stop`:
  - graceful stop 시도 후 timeout 시 강제 종료
- `status`:
  - 실행 중이면 0, 미실행이면 1
- `check`:
  - 서버가 꺼져 있으면 먼저 시작
  - 이후 `smoke_api.sh` 실행

## Compatibility

- 기존 `dev_serve.sh`/`smoke_api.sh` 계약 유지
- API/CLI 로직 변경 없음

## Testing Strategy

- shell syntax: `bash -n`
- 기존 테스트: `pytest -q`
- 실동작: `start -> status -> check -> stop` 시나리오 검증
