# src/freya/config.py
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

try:
    # Pydantic v2
    from pydantic import BaseModel, Field
except Exception:  # pragma: no cover
    # fallback pydantic v1 style if needed
    from pydantic import BaseModel, Field  # type: ignore


def _pick_default_managed_root() -> Path:
    # Priorité: env > chemin que tu utilises déjà > cwd/.freya
    env = os.environ.get("FREYA_MANAGED_ROOT")
    if env:
        return Path(env)

    preferred = Path(r"H:\Code\Local LLM\.freya")
    if preferred.exists():
        return preferred

    return Path.cwd() / ".freya"


class SafetyConfig(BaseModel):
    managed_root: Path = Field(default_factory=_pick_default_managed_root)
    disk_free_min_gb: int = int(os.environ.get("FREYA_DISK_FREE_MIN_GB", "40"))


class OllamaConfig(BaseModel):
    base_url: str = os.environ.get("FREYA_OLLAMA_URL", "http://localhost:11434")


class LlamaCppConfig(BaseModel):
    llama_server_exe: Path = Field(
        default_factory=lambda: Path(
            os.environ.get(
                "FREYA_LLAMACPP_EXE",
                r"H:\Code\llama.cpp\build\bin\Release\llama-server.exe",
            )
        )
    )
    gguf_dir: Path = Field(
        default_factory=lambda: Path(os.environ.get("FREYA_GGUF_DIR", r"H:\Models\gguf"))
    )
    host: str = os.environ.get("FREYA_LLAMACPP_HOST", "127.0.0.1")
    port: int = int(os.environ.get("FREYA_LLAMACPP_PORT", "8001"))
    ctx_size: int = int(os.environ.get("FREYA_LLAMACPP_CTX", "8192"))
    threads: int = int(os.environ.get("FREYA_LLAMACPP_THREADS", "8"))
    ngl: int = int(os.environ.get("FREYA_LLAMACPP_NGL", "999"))


class FreyaConfig(BaseModel):
    safety: SafetyConfig = Field(default_factory=SafetyConfig)
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    llamacpp: LlamaCppConfig = Field(default_factory=LlamaCppConfig)

    # BMAD root: env > managed_root/bmad/BMAD-METHOD (ton sync-bmad) > fallback
    bmad_root: Path = Field(
        default_factory=lambda: Path(
            os.environ.get(
                "FREYA_BMAD_ROOT",
                str(_pick_default_managed_root() / "bmad" / "BMAD-METHOD"),
            )
        )
    )

    @property
    def managed_root(self) -> Path:
        return self.safety.managed_root

    @property
    def artifacts_root(self) -> Path:
        return self.managed_root / "artifacts"

    @property
    def logs_root(self) -> Path:
        return self.managed_root / "logs"

    @property
    def cache_root(self) -> Path:
        return self.managed_root / "cache"

    @property
    def reports_root(self) -> Path:
        return self.managed_root / "reports"

    @property
    def tmp_root(self) -> Path:
        return self.managed_root / "tmp"

    @classmethod
    def load(cls) -> "FreyaConfig":
        """
        Canonical entry point used by CLI/TUI.
        Keeps it simple: env-driven + sensible defaults.
        """
        cfg = cls()
        # ensure roots exist
        cfg.managed_root.mkdir(parents=True, exist_ok=True)
        cfg.cache_root.mkdir(parents=True, exist_ok=True)
        cfg.logs_root.mkdir(parents=True, exist_ok=True)
        cfg.reports_root.mkdir(parents=True, exist_ok=True)
        cfg.tmp_root.mkdir(parents=True, exist_ok=True)
        return cfg
