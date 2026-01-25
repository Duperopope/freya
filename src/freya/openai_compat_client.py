from __future__ import annotations

import time
import requests
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ChatResult:
    response: str
    duration_ms: int


class OpenAICompatClient:
    """
    Minimal OpenAI-compatible chat client.
    llama.cpp server exposes OpenAI-like endpoints depending on build/version.
    We'll target /v1/chat/completions.
    """
    def __init__(self, base_url: str, timeout_sec: int = 300) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_sec = timeout_sec

    def chat(self, model: str, system: str, prompt: str, options: dict[str, Any] | None = None) -> ChatResult:
        # llama.cpp often ignores "model" if only one is loaded; we still send it.
        payload: dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "temperature": (options or {}).get("temperature", 0.0),
            "top_p": (options or {}).get("top_p", 1.0),
            "max_tokens": (options or {}).get("num_predict", 700),
        }

        t0 = time.time()
        r = requests.post(f"{self.base_url}/v1/chat/completions", json=payload, timeout=self.timeout_sec)
        r.raise_for_status()
        dt = int((time.time() - t0) * 1000)
        j = r.json()
        # OpenAI format
        content = (((j.get("choices") or [{}])[0].get("message") or {}).get("content")) or ""
        return ChatResult(response=str(content), duration_ms=dt)
