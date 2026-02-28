from __future__ import annotations

import hashlib
import json
import os
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol
from urllib import error, parse, request


def _normalize_env_value(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    if (normalized.startswith('"') and normalized.endswith('"')) or (
        normalized.startswith("'") and normalized.endswith("'")
    ):
        normalized = normalized[1:-1]
    return normalized


def _read_local_env(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    env_map: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = _normalize_env_value(value)
        if not key or value is None:
            continue
        if value.startswith("$"):
            value = env_map.get(value[1:], value)
        env_map[key] = value
    return env_map


def _get_setting(name: str, *, default: str | None = None) -> str | None:
    env_value = _normalize_env_value(os.getenv(name))
    if env_value is not None:
        return env_value

    file_env = _read_local_env(Path.cwd() / ".env")
    value = file_env.get(name)
    if value is not None:
        return value
    return default


class LLMClient(Protocol):
    def generate(self, prompt: str, *, task: str) -> str:
        ...


class EchoLLMClient:
    def generate(self, prompt: str, *, task: str) -> str:
        return prompt


_DEFAULT_CLIENT_LOCK = threading.Lock()
_DEFAULT_CLIENT_SIGNATURE: tuple[object, ...] | None = None
_DEFAULT_CLIENT_INSTANCE: LLMClient | None = None


@dataclass
class GoogleAIStudioLLMClient:
    api_key: str
    model: str = "gemini-3.1-flash"
    response_mode: str = "model_output"
    timeout_sec: float = 60.0
    cache_path: Path | None = Path(".runtime/llm_cache.json")
    _cache: dict[str, str] = field(default_factory=dict, init=False)
    _cache_loaded: bool = field(default=False, init=False)
    _prompt_passthrough_probe_done: bool = field(default=False, init=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False)

    def _cache_key(self, prompt: str, task: str) -> str:
        raw = f"{self.model}\n{task}\n{prompt}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _load_cache(self) -> None:
        if self.cache_path is None or self._cache_loaded:
            return
        if self.cache_path.exists():
            try:
                payload = json.loads(self.cache_path.read_text(encoding="utf-8"))
                if isinstance(payload, dict):
                    self._cache = {str(k): str(v) for k, v in payload.items()}
            except (json.JSONDecodeError, OSError):
                self._cache = {}
        self._cache_loaded = True

    def _persist_cache(self) -> None:
        if self.cache_path is None:
            return
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(
            json.dumps(self._cache, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _resolve_model_candidates(self) -> list[str]:
        requested = self.model.strip()
        # Some Google accounts do not expose gemini-3.1-flash for text generateContent yet.
        if requested == "gemini-3.1-flash":
            return [
                requested,
                "gemini-3-flash-preview",
                "gemini-flash-latest",
                "gemini-2.5-flash",
            ]
        return [requested]

    def _request_model_output(self, prompt: str) -> str:
        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.0},
        }
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
        api_key = parse.quote(self.api_key, safe="")

        last_http_error: error.HTTPError | None = None
        for model_name in self._resolve_model_candidates():
            model_id = parse.quote(model_name, safe="")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={api_key}"
            req = request.Request(
                url,
                data=payload,
                method="POST",
                headers={"Content-Type": "application/json"},
            )
            try:
                with request.urlopen(req, timeout=self.timeout_sec) as resp:
                    raw = resp.read().decode("utf-8")
            except error.HTTPError as exc:
                last_http_error = exc
                if exc.code == 404:
                    continue
                raise

            parsed = json.loads(raw)
            candidates = parsed.get("candidates", [])
            if not candidates:
                raise RuntimeError("Gemini response has no candidates")
            content = candidates[0].get("content", {})
            parts = content.get("parts", []) if isinstance(content, dict) else []
            texts = [str(part.get("text", "")).strip() for part in parts if isinstance(part, dict)]
            output = "\n".join(text for text in texts if text).strip()
            if not output:
                raise RuntimeError("Gemini response text is empty")
            return output

        if last_http_error is not None:
            raise last_http_error
        raise RuntimeError("Gemini request failed without HTTP error")

    def generate(self, prompt: str, *, task: str) -> str:
        key = self._cache_key(prompt, task)
        should_probe = False

        with self._lock:
            self._load_cache()
            if key in self._cache:
                return self._cache[key]
            if self.response_mode == "prompt_passthrough" and not self._prompt_passthrough_probe_done:
                # Probe the configured model once per process, then keep tests deterministic/fast.
                self._prompt_passthrough_probe_done = True
                should_probe = True

        if self.response_mode == "prompt_passthrough":
            if should_probe:
                try:
                    self._request_model_output(prompt)
                except Exception:
                    # In passthrough mode, model probe failures should not fail local test runs.
                    pass
            final_output = prompt
        else:
            model_output = self._request_model_output(prompt)
            final_output = model_output

        with self._lock:
            self._cache[key] = final_output
            self._persist_cache()
        return final_output


def build_default_llm_client() -> LLMClient:
    global _DEFAULT_CLIENT_SIGNATURE, _DEFAULT_CLIENT_INSTANCE
    provider = (_get_setting("PROJECT_DREAM_LLM_PROVIDER", default="echo") or "echo").lower()
    if provider not in {"google", "gemini"}:
        signature: tuple[object, ...] = ("echo",)
        with _DEFAULT_CLIENT_LOCK:
            if _DEFAULT_CLIENT_SIGNATURE == signature and _DEFAULT_CLIENT_INSTANCE is not None:
                return _DEFAULT_CLIENT_INSTANCE
            client = EchoLLMClient()
            _DEFAULT_CLIENT_SIGNATURE = signature
            _DEFAULT_CLIENT_INSTANCE = client
            return client

    api_key = (
        _get_setting("PROJECT_DREAM_LLM_API_KEY")
        or _get_setting("GOOGLE_API_KEY")
        or _get_setting("GEMINI_API_KEY")
    )
    if not api_key:
        raise RuntimeError("Google LLM provider selected but API key is missing")

    model = _get_setting("PROJECT_DREAM_LLM_MODEL", default="gemini-3.1-flash") or "gemini-3.1-flash"
    response_mode = _get_setting("PROJECT_DREAM_LLM_RESPONSE_MODE", default="model_output") or "model_output"
    timeout_raw = _get_setting("PROJECT_DREAM_LLM_TIMEOUT_SEC", default="60") or "60"
    cache_path_raw = _get_setting("PROJECT_DREAM_LLM_CACHE_PATH", default=".runtime/llm_cache.json")
    timeout_sec = float(timeout_raw)
    cache_path = Path(cache_path_raw) if cache_path_raw else None
    signature = (
        "google",
        api_key,
        model,
        response_mode,
        timeout_raw,
        cache_path_raw,
    )

    with _DEFAULT_CLIENT_LOCK:
        if _DEFAULT_CLIENT_SIGNATURE == signature and _DEFAULT_CLIENT_INSTANCE is not None:
            return _DEFAULT_CLIENT_INSTANCE
        client = GoogleAIStudioLLMClient(
            api_key=api_key,
            model=model,
            response_mode=response_mode,
            timeout_sec=timeout_sec,
            cache_path=cache_path,
        )
        _DEFAULT_CLIENT_SIGNATURE = signature
        _DEFAULT_CLIENT_INSTANCE = client
        return client
