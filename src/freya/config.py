from __future__ import annotations

import os
from pathlib import Path
from typing import Any
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


def _env_float(name: str, default: float) -> float:
    v = os.environ.get(name, "").strip()
    try:
        return float(v)
    except Exception:
        return default


def _env_bool(name: str, default: bool) -> bool:
    v = os.environ.get(name, "").strip().lower()
    if v in ("true", "1", "yes", "on"):
        return True
    if v in ("false", "0", "no", "off"):
        return False
    return default


# =============================================================================
# HYBRID ROUTING CONFIGURATION
# =============================================================================

# Remote provider definitions with free tier limits (updated Jan 2026)
# References:
# - HuggingFace: https://huggingface.co/docs/inference-providers/en/pricing
# - Together AI: https://docs.together.ai/docs/rate-limits
# - Groq: https://console.groq.com/docs/rate-limits

PROVIDERS: dict[str, dict[str, Any]] = {
    "hf": {
        "name": "Hugging Face",
        "base_url": "https://api-inference.huggingface.co",
        "api_key_env": "HF_API_KEY",
        "usage_url": "https://huggingface.co/api/usage",  # For checking usage
        "free_tier": {
            "monthly_credits_usd": 0.10,  # Free users get $0.10/month
            "pro_credits_usd": 2.00,  # PRO users get $2.00/month
        },
        "rate_limits": {
            "requests_per_minute": 60,
            "tokens_per_minute": 50000,
        },
        "models": {
            "analyst": "meta-llama/Meta-Llama-3.1-8B-Instruct",
            "pm": "meta-llama/Meta-Llama-3.1-8B-Instruct",
            "architect": "Qwen/Qwen2.5-72B-Instruct",
            "po": "meta-llama/Meta-Llama-3.1-8B-Instruct",
            "sm": "meta-llama/Meta-Llama-3.1-8B-Instruct",
            "dev": "deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct",
            "qa": "meta-llama/Meta-Llama-3.1-8B-Instruct",
        },
        "enabled": True,
        "priority": 2,  # Lower = higher priority
    },
    "together": {
        "name": "Together AI",
        "base_url": "https://api.together.xyz/v1",
        "api_key_env": "TOGETHER_API_KEY",
        "usage_url": "https://api.together.xyz/v1/usage",
        "free_tier": {
            "signup_credits_usd": 25.00,  # $25 free credits on signup
            "requires_payment": True,  # Requires $5 minimum purchase
        },
        "rate_limits": {
            # Tier 1 (after $5 paid)
            "requests_per_minute": 600,
            "tokens_per_minute": 180000,
        },
        "models": {
            "analyst": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
            "pm": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
            "architect": "Qwen/Qwen2.5-72B-Instruct-Turbo",
            "po": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
            "sm": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
            "dev": "deepseek-ai/deepseek-coder-33b-instruct",
            "qa": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
        },
        "enabled": True,
        "priority": 3,
    },
    "groq": {
        "name": "Groq",
        "base_url": "https://api.groq.com/openai/v1",
        "api_key_env": "GROQ_API_KEY",
        "usage_url": None,  # Usage tracked via headers
        "free_tier": {
            "free_forever": True,  # Free tier with rate limits
            "no_credit_card": True,
        },
        "rate_limits": {
            # Free tier limits (varies by model)
            "requests_per_minute": 30,
            "requests_per_day": 14400,
            "tokens_per_minute": 6000,
            "tokens_per_day": 500000,
        },
        "models": {
            "analyst": "llama-3.1-8b-instant",
            "pm": "llama-3.1-8b-instant",
            "architect": "llama-3.3-70b-versatile",
            "po": "llama-3.1-8b-instant",
            "sm": "llama-3.1-8b-instant",
            "dev": "llama-3.3-70b-versatile",
            "qa": "llama-3.1-8b-instant",
        },
        "enabled": True,
        "priority": 1,  # Groq is fast and free - highest priority
    },
}

# Hybrid routing thresholds
HYBRID_ROUTING_CONFIG: dict[str, Any] = {
    # If remote_score > local_score * PERCENT_THRESHOLD, use remote
    "percent_threshold": 1.20,  # 20% better required to switch to remote
    # Minimum local score to skip remote validation
    "local_min_score": 70,
    # Enable/disable hybrid routing
    "enabled": True,
    # Fallback chain when primary fails: groq -> hf -> together -> local
    "fallback_chain": ["groq", "hf", "together", "local"],
    # Health check timeout (seconds)
    "health_timeout_sec": 5,
    # Health check interval (minutes)
    "health_check_interval_min": 5,
    # Maximum retries before marking provider offline
    "max_retries": 3,
    # Cache duration for quota checks (seconds)
    "quota_cache_sec": 300,
}

# Local runtime detection configuration
LOCAL_RUNTIMES: dict[str, dict[str, Any]] = {
    "ollama": {
        "name": "Ollama",
        "base_url": "http://localhost:11434",
        "health_endpoint": "/api/tags",
        "api_type": "ollama",
        "priority": 1,
    },
    "lm_studio": {
        "name": "LM Studio",
        "base_url": "http://localhost:1234",
        "health_endpoint": "/v1/models",
        "api_type": "openai",
        "priority": 2,
    },
    "koboldcpp": {
        "name": "KoboldCpp",
        "base_url": "http://localhost:5001",
        "health_endpoint": "/api/v1/model",
        "api_type": "kobold",
        "priority": 3,
    },
    "oobabooga": {
        "name": "Oobabooga Text Generation WebUI",
        "base_url": "http://localhost:5000",
        "health_endpoint": "/v1/models",
        "api_type": "openai",
        "priority": 4,
    },
    "llamacpp": {
        "name": "llama.cpp Server",
        "base_url": "http://localhost:8080",
        "health_endpoint": "/health",
        "api_type": "llamacpp",
        "priority": 5,
    },
}


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


class HybridRoutingConfig(BaseModel):
    """
    Hybrid routing configuration for local/remote LLM selection.
    """
    enabled: bool = Field(default=True)
    percent_threshold: float = Field(default=1.20)  # Remote must be 20% better
    local_min_score: int = Field(default=70)  # Skip remote if local score >= this
    fallback_chain: list[str] = Field(default_factory=lambda: ["groq", "hf", "together", "local"])
    health_timeout_sec: int = Field(default=5)
    health_check_interval_min: int = Field(default=5)
    max_retries: int = Field(default=3)
    quota_cache_sec: int = Field(default=300)


class ProviderConfig(BaseModel):
    """
    Remote provider API key configuration.
    Keys can be set via environment variables or stored securely.
    """
    hf_api_key: str = Field(default="")
    together_api_key: str = Field(default="")
    groq_api_key: str = Field(default="")


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
    hybrid_routing: HybridRoutingConfig = Field(default_factory=HybridRoutingConfig)
    providers: ProviderConfig = Field(default_factory=ProviderConfig)

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

        # Hybrid routing configuration
        hybrid_routing = HybridRoutingConfig(
            enabled=_env_bool("FREYA_HYBRID_ENABLED", True),
            percent_threshold=_env_float("FREYA_HYBRID_THRESHOLD", 1.20),
            local_min_score=_env_int("FREYA_HYBRID_LOCAL_MIN", 70),
            fallback_chain=_env_str("FREYA_HYBRID_FALLBACK", "groq,hf,together,local").split(","),
            health_timeout_sec=_env_int("FREYA_HEALTH_TIMEOUT", 5),
            health_check_interval_min=_env_int("FREYA_HEALTH_INTERVAL", 5),
            max_retries=_env_int("FREYA_HYBRID_RETRIES", 3),
            quota_cache_sec=_env_int("FREYA_QUOTA_CACHE", 300),
        )

        # Provider API keys (from environment)
        providers = ProviderConfig(
            hf_api_key=_env_str("HF_API_KEY", ""),
            together_api_key=_env_str("TOGETHER_API_KEY", ""),
            groq_api_key=_env_str("GROQ_API_KEY", ""),
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
            hybrid_routing=hybrid_routing,
            providers=providers,
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
