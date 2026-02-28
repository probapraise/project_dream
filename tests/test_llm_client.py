import json
from urllib.error import HTTPError
from pathlib import Path

import pytest

import project_dream.llm_client as llm_client


class _FakeHTTPResponse:
    def __init__(self, payload: dict):
        self._raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    def read(self) -> bytes:
        return self._raw

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return None


def test_build_default_llm_client_falls_back_to_echo(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("PROJECT_DREAM_LLM_PROVIDER", raising=False)
    monkeypatch.delenv("PROJECT_DREAM_LLM_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    client = llm_client.build_default_llm_client()

    assert isinstance(client, llm_client.EchoLLMClient)


def test_build_default_llm_client_uses_google_with_prompt_passthrough_and_cache(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    calls: list[dict] = []

    def fake_urlopen(req, timeout=0):
        calls.append({"url": req.full_url, "timeout": timeout})
        return _FakeHTTPResponse(
            {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {"text": "MODEL TEXT"},
                            ]
                        }
                    }
                ]
            }
        )

    cache_path = tmp_path / "llm_cache.json"
    monkeypatch.setenv("PROJECT_DREAM_LLM_PROVIDER", "google")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.setenv("PROJECT_DREAM_LLM_MODEL", "gemini-3.1-flash")
    monkeypatch.setenv("PROJECT_DREAM_LLM_RESPONSE_MODE", "prompt_passthrough")
    monkeypatch.setenv("PROJECT_DREAM_LLM_CACHE_PATH", str(cache_path))
    monkeypatch.setattr(llm_client.request, "urlopen", fake_urlopen)

    client = llm_client.build_default_llm_client()
    out1 = client.generate("prompt-1", task="comment_generation")
    out2 = client.generate("prompt-1", task="comment_generation")

    assert out1 == "prompt-1"
    assert out2 == "prompt-1"
    assert len(calls) == 1
    assert "gemini-3.1-flash" in calls[0]["url"]
    assert cache_path.exists()


def test_google_client_returns_model_output_when_response_mode_is_model_output(
    monkeypatch: pytest.MonkeyPatch,
):
    def fake_urlopen(req, timeout=0):
        return _FakeHTTPResponse(
            {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {"text": "MODEL OUTPUT"},
                            ]
                        }
                    }
                ]
            }
        )

    monkeypatch.setattr(llm_client.request, "urlopen", fake_urlopen)
    client = llm_client.GoogleAIStudioLLMClient(
        api_key="test-key",
        model="gemini-3.1-flash",
        response_mode="model_output",
        cache_path=None,
    )

    output = client.generate("prompt-2", task="report_summary")

    assert output == "MODEL OUTPUT"


def test_google_client_falls_back_when_model_returns_404(monkeypatch: pytest.MonkeyPatch):
    calls: list[str] = []

    def fake_urlopen(req, timeout=0):
        calls.append(req.full_url)
        if "gemini-3.1-flash:generateContent" in req.full_url:
            raise HTTPError(req.full_url, 404, "Not Found", hdrs=None, fp=None)
        return _FakeHTTPResponse(
            {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {"text": "FALLBACK OUTPUT"},
                            ]
                        }
                    }
                ]
            }
        )

    monkeypatch.setattr(llm_client.request, "urlopen", fake_urlopen)
    client = llm_client.GoogleAIStudioLLMClient(
        api_key="test-key",
        model="gemini-3.1-flash",
        response_mode="model_output",
        cache_path=None,
    )

    output = client.generate("prompt-3", task="report_summary")

    assert output == "FALLBACK OUTPUT"
    assert any("gemini-3.1-flash:generateContent" in url for url in calls)
    assert any("gemini-3-flash-preview:generateContent" in url for url in calls)


def test_prompt_passthrough_probes_model_once_then_returns_prompt(
    monkeypatch: pytest.MonkeyPatch,
):
    calls: list[str] = []

    def fake_urlopen(req, timeout=0):
        calls.append(req.full_url)
        return _FakeHTTPResponse(
            {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {"text": "MODEL OUTPUT"},
                            ]
                        }
                    }
                ]
            }
        )

    monkeypatch.setattr(llm_client.request, "urlopen", fake_urlopen)
    client = llm_client.GoogleAIStudioLLMClient(
        api_key="test-key",
        model="gemini-3-flash-preview",
        response_mode="prompt_passthrough",
        cache_path=None,
    )

    out1 = client.generate("prompt-A", task="comment_generation")
    out2 = client.generate("prompt-B", task="comment_generation")

    assert out1 == "prompt-A"
    assert out2 == "prompt-B"
    assert len(calls) == 1


def test_build_default_llm_client_reuses_same_instance_for_same_google_settings(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    calls: list[str] = []

    def fake_urlopen(req, timeout=0):
        calls.append(req.full_url)
        return _FakeHTTPResponse(
            {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {"text": "MODEL OUTPUT"},
                            ]
                        }
                    }
                ]
            }
        )

    cache_path = tmp_path / "singleton_cache.json"
    monkeypatch.setenv("PROJECT_DREAM_LLM_PROVIDER", "google")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.setenv("PROJECT_DREAM_LLM_MODEL", "gemini-3-flash-preview")
    monkeypatch.setenv("PROJECT_DREAM_LLM_RESPONSE_MODE", "prompt_passthrough")
    monkeypatch.setenv("PROJECT_DREAM_LLM_CACHE_PATH", str(cache_path))
    monkeypatch.setattr(llm_client.request, "urlopen", fake_urlopen)

    c1 = llm_client.build_default_llm_client()
    c2 = llm_client.build_default_llm_client()
    assert c1 is c2

    out1 = c1.generate("prompt-C", task="comment_generation")
    out2 = c2.generate("prompt-D", task="comment_generation")

    assert out1 == "prompt-C"
    assert out2 == "prompt-D"
    assert len(calls) == 1
