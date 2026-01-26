from __future__ import annotations

import os
from pathlib import Path
from pydantic import BaseModel, Field


def _env_path(name: str, default: Path) -> Path:
    v = os.environ.get(name, "").strip()
    return Path(v).expanduser() if v else default


def _env_str(name: str, default: str) -> str:
    v = os.environ.get(name, "").strip()
    return v or default


def _env_int(name: str, default: int) -> int:
    v = os.environ.get(name, "").strip()
    try:
        return int(v)
    except Exception:
        return default


class SafetyConfig(BaseModel):
    """
    Safety / sandbox settings.

    Orchestrator expects:
      cfg.safety.workspace_root
      cfg.safety.protected_names
    """
    workspace_root: Path = Field(default_factory=lambda: Path.cwd())
    protected_names: list[str] = Field(
        default_factory=lambda: [
            ".git",
            ".venv",
            ".freya",
            "node_modules",
            "__pycache__",
        ]
    )


class OllamaConfig(BaseModel):
    base_url: str = Field(default="http://localhost:11434")
    timeout_sec: int = Field(default=120)


class LlamaCppConfig(BaseModel):
    """
    Optional llama.cpp server settings.
    (Server itself is handled by src/freya/llamacpp_server.py)
    """
    base_url: str = Field(default="http://127.0.0.1:8001")
    exe: Path = Field(default_factory=lambda: Path(r"H:\Code\llama.cpp\build\bin\Release\llama-server.exe"))
    gguf_dir: Path = Field(default_factory=lambda: Path(r"E:\Models\gguf"))
    ctx_size: int = Field(default=8192)
    threads: int = Field(default=8)
    ngl: int = Field(default=999)


class ModelsConfig(BaseModel):
    """
    Default per-role models (overridable by routing.json produced by bench).
    """
    analyst: str = Field(default="llama3.1:8b")
    pm: str = Field(default="llama3.1:8b")
    architect: str = Field(default="llama3.1:8b")
    po: str = Field(default="llama3.1:8b")
    sm: str = Field(default="llama3.1:8b")
    dev: str = Field(default="deepseek-coder-v2:latest")
    qa: str = Field(default="llama3.1:8b")


class FreyaConfig(BaseModel):
    """
    Central config object loaded by FreyaConfig.load().

    TUI expects:
      prompts_root
      output_root
      routing_override_path
    """
    managed_root: Path
    cache_root: Path
    artifacts_root: Path
    bmad_root: Path

    # Added for TUI + UX
    prompts_root: Path
    output_root: Path
    routing_override_path: Path

    # Where Orchestrator reads role routing decisions
    routing_path: Path

    safety: SafetyConfig = Field(default_factory=SafetyConfig)
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    llamacpp: LlamaCppConfig = Field(default_factory=LlamaCppConfig)
    models: ModelsConfig = Field(default_factory=ModelsConfig)

    @classmethod
    def load(cls) -> "FreyaConfig":
        # Default managed root (Windows friendly)
        default_managed = Path.home() / ".freya"
        managed_root = _env_path("FREYA_MANAGED_ROOT", default_managed)

        cache_root = _env_path("FREYA_CACHE_ROOT", managed_root / "cache")
        artifacts_root = _env_path("FREYA_ARTIFACTS_ROOT", managed_root / "artifacts")
        bmad_root = _env_path("FREYA_BMAD_ROOT", managed_root / "bmad")

        # workspace (code-writing sandbox)
        workspace_root = _env_path("FREYA_WORKSPACE_ROOT", managed_root / "workspace")

        # prompts + output for TUI flows
        prompts_root = _env_path("FREYA_PROMPTS_ROOT", managed_root / "config" / "prompts")
        output_root = _env_path("FREYA_OUTPUT_ROOT", artifacts_root / "projects")

        # routing files
        routing_path = _env_path("FREYA_ROUTING_PATH", cache_root / "routing.json")
        routing_override_path = _env_path("FREYA_ROUTING_OVERRIDE_PATH", cache_root / "routing_override.json")

        # Ollama
        ollama_url = _env_str("FREYA_OLLAMA_URL", "http://localhost:11434")
        ollama_timeout = _env_int("FREYA_OLLAMA_TIMEOUT_SEC", 120)

        # Default per-role models (fallback only; dynamic routing is via routing.json)
        def _m(key: str, default: str) -> str:
            return _env_str(key, default)

        models = ModelsConfig(
            analyst=_m("FREYA_MODEL_ANALYST", "llama3.1:8b"),
            pm=_m("FREYA_MODEL_PM", "llama3.1:8b"),
            architect=_m("FREYA_MODEL_ARCHITECT", "llama3.1:8b"),
            po=_m("FREYA_MODEL_PO", "llama3.1:8b"),
            sm=_m("FREYA_MODEL_SM", "llama3.1:8b"),
            dev=_m("FREYA_MODEL_DEV", "deepseek-coder-v2:latest"),
            qa=_m("FREYA_MODEL_QA", "llama3.1:8b"),
        )

        # llama.cpp defaults can be overridden too
        llamacpp = LlamaCppConfig(
            base_url=_env_str("FREYA_LLAMACPP_URL", "http://127.0.0.1:8001"),
            exe=_env_path("FREYA_LLAMACPP_EXE", Path(r"H:\Code\llama.cpp\build\bin\Release\llama-server.exe")),
            gguf_dir=_env_path("FREYA_GGUF_DIR", Path(r"E:\Models\gguf")),
            ctx_size=_env_int("FREYA_LLAMACPP_CTX", 8192),
            threads=_env_int("FREYA_LLAMACPP_THREADS", 8),
            ngl=_env_int("FREYA_LLAMACPP_NGL", 999),
        )

        cfg = cls(
            managed_root=managed_root,
            cache_root=cache_root,
            artifacts_root=artifacts_root,
            bmad_root=bmad_root,
            prompts_root=prompts_root,
            output_root=output_root,
            routing_override_path=routing_override_path,
            routing_path=routing_path,
            safety=SafetyConfig(workspace_root=workspace_root),
            ollama=OllamaConfig(base_url=ollama_url, timeout_sec=ollama_timeout),
            llamacpp=llamacpp,
            models=models,
        )

        cfg.ensure_dirs()
        return cfg

    def ensure_dirs(self) -> None:
        self.managed_root.mkdir(parents=True, exist_ok=True)
        self.cache_root.mkdir(parents=True, exist_ok=True)
        self.artifacts_root.mkdir(parents=True, exist_ok=True)
        self.bmad_root.mkdir(parents=True, exist_ok=True)
        self.safety.workspace_root.mkdir(parents=True, exist_ok=True)

        self.prompts_root.mkdir(parents=True, exist_ok=True)
        self.output_root.mkdir(parents=True, exist_ok=True)

        (self.managed_root / "tmp").mkdir(parents=True, exist_ok=True)
        (self.cache_root / "bench_runs").mkdir(parents=True, exist_ok=True)
