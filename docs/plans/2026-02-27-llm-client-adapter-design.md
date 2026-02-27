# Project Dream LLM Client Adapter Design

## Goal

`infra/llm_client` 경계를 코드에 도입해, 현재 stub 생성기를 유지하면서도 향후 실제 LLM 공급자(OpenAI 등)로 교체 가능한 인터페이스를 확보한다.

## Scope

- `LLMClient` 프로토콜/기본 구현(`EchoLLMClient`) 추가
- `gen_engine.generate_comment`가 템플릿 렌더링 후 LLM client를 호출하도록 변경
- 기본 동작은 기존 출력과 동일하게 유지(하위호환)
- 커스텀 client 주입 테스트 추가

## Approach

### 1) Protocol + Echo Stub (Recommended)

- 장점: 의존성 최소, 테스트 용이, 기존 흐름 영향 작음
- 단점: 실제 네트워크 호출 기능은 아직 없음

### 2) 즉시 실제 API 클라이언트 도입

- 장점: 빠르게 실서비스 연동 가능
- 단점: 키 관리/요금/에러처리 복잡도 급상승

선택: 1번.

## Interface Contract

- `LLMClient.generate(prompt: str, *, task: str) -> str`
- `EchoLLMClient`는 입력 prompt를 그대로 반환
- `generate_comment(..., llm_client=None)`:
  - prompt 템플릿 렌더링
  - client 없으면 `EchoLLMClient` 사용
  - `task="comment_generation"`으로 호출

## Compatibility

- 기존 orchestrator 호출부 수정 없이 동작
- 기존 생성 문자열 포맷 유지

## Testing Strategy

- 기본 echo 클라이언트로 기존 결정론 유지
- custom fake client 주입 시 호출 인자(task/prompt) 검증
