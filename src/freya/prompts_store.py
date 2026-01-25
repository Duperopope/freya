from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, Field


def _pick_default_managed_root() -> Path:
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


class WebSearchConfig(BaseModel):
    # Provider: "brave" (API key) or "wikipedia" (free)
    provider: str = os.environ.get("FREYA_WEB_PROVIDER", "wikipedia")
    brave_api_key: str = os.environ.get("BRAVE_API_KEY", "")
    user_agent: str = os.environ.get("FREYA_WEB_UA", "Freya/1.0")


class FreyaConfig(BaseModel):
    safety: SafetyConfig = Field(default_factory=SafetyConfig)
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    web: WebSearchConfig = Field(default_factory=WebSearchConfig)

    # Where BMAD repo is synced
    bmad_root: Path = Field(
        default_factory=lambda: Path(
            os.environ.get(
                "FREYA_BMAD_ROOT",
                str(_pick_default_managed_root() / "bmad" / "BMAD-METHOD"),
            )
        )
    )

    # Default output dir for generated projects / artifacts
    output_root: Path = Field(
        default_factory=lambda: Path(
            os.environ.get(
                "FREYA_OUTPUT_ROOT",
                str(_pick_default_managed_root() / "artifacts"),
            )
        )
    )

    @property
    def managed_root(self) -> Path:
        return self.safety.managed_root

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

    @property
    def prompts_root(self) -> Path:
        return self.managed_root / "config" / "prompts"

    @property
    def routing_override_path(self) -> Path:
        return self.managed_root / "config" / "routing_override.json"

    @classmethod
    def load(cls) -> "FreyaConfig":
        cfg = cls()
        cfg.managed_root.mkdir(parents=True, exist_ok=True)
        cfg.logs_root.mkdir(parents=True, exist_ok=True)
        cfg.cache_root.mkdir(parents=True, exist_ok=True)
        cfg.reports_root.mkdir(parents=True, exist_ok=True)
        cfg.tmp_root.mkdir(parents=True, exist_ok=True)
        cfg.prompts_root.mkdir(parents=True, exist_ok=True)
        cfg.output_root.mkdir(parents=True, exist_ok=True)
        return cfg
