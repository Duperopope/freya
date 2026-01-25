from __future__ import annotations

import time
import json
import subprocess
import shutil
import requests
from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class OllamaGenerateResult:
    model: str
    response: str
    duration_ms: int


class OllamaClient:
    """
    Minimal Ollama HTTP client.
    Endpoints:
    - GET  /api/tags
    - POST /api/generate
    - POST /api/pull (stream)
    - POST /api/show
    - POST /api/delete (if supported)
    """
    def __init__(self, base_url: str, timeout_sec: int = 120) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_sec = timeout_sec

    def tags(self) -> list[dict[str, Any]]:
        r = requests.get(f"{self.base_url}/api/tags", timeout=self.timeout_sec)
        r.raise_for_status()
        return (r.json().get("models", []) or [])

    def show(self, model: str) -> dict[str, Any]:
        r = requests.post(f"{self.base_url}/api/show", json={"name": model}, timeout=self.timeout_sec)
        r.raise_for_status()
        return r.json()

    def generate(
        self,
        model: str,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.0,
        top_p: float = 1.0,
        num_ctx: int | None = None,
        options_extra: dict[str, Any] | None = None,
        timeout_sec: int | None = None,
    ) -> OllamaGenerateResult:
        options: dict[str, Any] = {"temperature": temperature, "top_p": top_p}
        if num_ctx is not None:
            options["num_ctx"] = num_ctx
        if options_extra:
            options.update(options_extra)

        payload: dict[str, Any] = {"model": model, "prompt": prompt, "stream": False, "options": options}
        if system:
            payload["system"] = system

        t0 = time.time()
        r = requests.post(
            f"{self.base_url}/api/generate",
            json=payload,
            timeout=(timeout_sec if timeout_sec is not None else self.timeout_sec),
        )
        r.raise_for_status()
        dt = int((time.time() - t0) * 1000)
        j = r.json()
        return OllamaGenerateResult(model=model, response=(j.get("response") or ""), duration_ms=dt)

    def pull_stream(self, model: str) -> Iterable[dict[str, Any]]:
        payload = {"name": model, "stream": True}
        with requests.post(f"{self.base_url}/api/pull", json=payload, stream=True, timeout=self.timeout_sec) as r:
            r.raise_for_status()
            for line in r.iter_lines(decode_unicode=True):
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except Exception:
                    continue

    def delete(self, model: str) -> None:
        try:
            r = requests.post(f"{self.base_url}/api/delete", json={"name": model}, timeout=self.timeout_sec)
            if r.status_code in (200, 204):
                return
            if r.status_code in (404, 405):
                raise RuntimeError("HTTP delete not supported")
            r.raise_for_status()
            return
        except Exception:
            pass

        exe = shutil.which("ollama")
        if not exe:
            raise RuntimeError("Cannot delete model: ollama CLI not found and HTTP delete unavailable.")
        cp = subprocess.run([exe, "rm", model], capture_output=True, text=True)
        if cp.returncode != 0:
            raise RuntimeError(f"ollama rm failed: {cp.stderr.strip() or cp.stdout.strip()}")
