from typing import Protocol


class LLMClient(Protocol):
    def generate(self, prompt: str, *, task: str) -> str:
        ...


class EchoLLMClient:
    def generate(self, prompt: str, *, task: str) -> str:
        return prompt
