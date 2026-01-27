# src/freya/api/routes/settings.py
"""
Settings API Routes

Endpoints for configuration management:
- Get/set configuration
- Manage prompts
- View paths and directories
- System preferences
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter()


# -----------------------------------------------------------------------------
# Request/Response Models
# -----------------------------------------------------------------------------
class PathsConfig(BaseModel):
    """System paths configuration."""
    managed_root: str
    cache_root: str
    artifacts_root: str
    output_root: str
    prompts_root: str
    workspace_root: str
    routing_path: str


class OllamaConfig(BaseModel):
    """Ollama configuration."""
    base_url: str
    timeout_sec: int


class ModelsConfig(BaseModel):
    """Default models per role."""
    analyst: str
    pm: str
    architect: str
    po: str
    sm: str
    dev: str
    qa: str


class PromptInfo(BaseModel):
    """Prompt file information."""
    name: str
    path: str
    size_bytes: int
    preview: str | None = None


class PromptContent(BaseModel):
    """Prompt content."""
    name: str
    content: str


class SavePromptRequest(BaseModel):
    """Request to save a prompt."""
    name: str = Field(..., description="Prompt name (e.g., 'analyst', 'chat_base_fr')")
    content: str = Field(..., description="Prompt content")


# -----------------------------------------------------------------------------
# Default Prompts
# -----------------------------------------------------------------------------
DEFAULT_CHAT_BASE_FR = """Tu es Freya, une assistante IA experte en développement logiciel.
Tu réponds en français, de façon claire, structurée et actionnable.

Cadre:
- Réponses légales et éthiques uniquement
- Approche défensive par défaut pour la sécurité
- Cite tes sources quand tu utilises des informations externes
- Format Markdown pour la lisibilité
"""

DEFAULT_ROLE_PROMPTS = {
    "analyst": "Tu es l'Analyst BMAD. Tu produis project-brief.md selon BMAD. Précis, structuré.",
    "pm": "Tu es le PM BMAD. Tu produis PRD.md (FR/NFR/epics).",
    "architect": "Tu es l'Architect BMAD. Tu produis architecture.md (modules, risques, observabilité, sécurité).",
    "po": "Tu es le Product Owner BMAD. Tu shards en epic-*.md propres.",
    "sm": "Tu es le Scrum Master BMAD. Tu produis *.story.md détaillés (AC, steps, tests).",
    "dev": "Tu es le Developer BMAD. Tu codes, tests, respecte les contraintes.",
    "qa": "Tu es le QA BMAD. Tu valides, matrice de traçabilité, quality gates.",
}


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------
@router.get("/paths", response_model=PathsConfig)
async def get_paths(request: Request) -> PathsConfig:
    """Get all configured paths."""
    state = request.app.state.freya
    
    if not state.ready or not state.config:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    cfg = state.config
    return PathsConfig(
        managed_root=str(cfg.managed_root),
        cache_root=str(cfg.cache_root),
        artifacts_root=str(cfg.artifacts_root),
        output_root=str(cfg.output_root),
        prompts_root=str(cfg.prompts_root),
        workspace_root=str(cfg.safety.workspace_root),
        routing_path=str(cfg.routing_path),
    )


@router.get("/ollama", response_model=OllamaConfig)
async def get_ollama_config(request: Request) -> OllamaConfig:
    """Get Ollama configuration."""
    state = request.app.state.freya
    
    if not state.ready or not state.config:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    return OllamaConfig(
        base_url=state.config.ollama.base_url,
        timeout_sec=state.config.ollama.timeout_sec,
    )


@router.get("/models-default", response_model=ModelsConfig)
async def get_default_models(request: Request) -> ModelsConfig:
    """Get default models per role (from config, not routing)."""
    state = request.app.state.freya
    
    if not state.ready or not state.config:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    m = state.config.models
    return ModelsConfig(
        analyst=m.analyst,
        pm=m.pm,
        architect=m.architect,
        po=m.po,
        sm=m.sm,
        dev=m.dev,
        qa=m.qa,
    )


@router.get("/prompts", response_model=list[PromptInfo])
async def list_prompts(request: Request) -> list[PromptInfo]:
    """List all available prompts."""
    state = request.app.state.freya
    
    if not state.ready or not state.config:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    prompts_root = state.config.prompts_root
    _ensure_default_prompts(prompts_root)
    
    prompts = []
    
    # Root level prompts
    for path in prompts_root.glob("*.md"):
        try:
            content = path.read_text(encoding="utf-8")
            prompts.append(PromptInfo(
                name=path.stem,
                path=str(path.relative_to(prompts_root)),
                size_bytes=len(content.encode("utf-8")),
                preview=content[:200] + "..." if len(content) > 200 else content
            ))
        except Exception:
            continue
    
    # BMAD role prompts
    bmad_dir = prompts_root / "bmad_roles"
    if bmad_dir.exists():
        for path in bmad_dir.glob("*.md"):
            try:
                content = path.read_text(encoding="utf-8")
                prompts.append(PromptInfo(
                    name=f"bmad/{path.stem}",
                    path=str(path.relative_to(prompts_root)),
                    size_bytes=len(content.encode("utf-8")),
                    preview=content[:200] + "..." if len(content) > 200 else content
                ))
            except Exception:
                continue
    
    return sorted(prompts, key=lambda x: x.name)


@router.get("/prompts/{name:path}", response_model=PromptContent)
async def get_prompt(request: Request, name: str) -> PromptContent:
    """Get a specific prompt content."""
    state = request.app.state.freya
    
    if not state.ready or not state.config:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    prompts_root = state.config.prompts_root
    _ensure_default_prompts(prompts_root)
    
    # Handle bmad/ prefix
    if name.startswith("bmad/"):
        path = prompts_root / "bmad_roles" / f"{name[5:]}.md"
    else:
        path = prompts_root / f"{name}.md"
    
    # Security check
    try:
        path = path.resolve()
        if prompts_root.resolve() not in path.parents and path != prompts_root.resolve():
            raise HTTPException(status_code=403, detail="Access denied")
    except Exception:
        raise HTTPException(status_code=403, detail="Invalid path")
    
    if not path.exists():
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    try:
        content = path.read_text(encoding="utf-8")
        return PromptContent(name=name, content=content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read prompt: {e}")


@router.post("/prompts")
async def save_prompt(request: Request, body: SavePromptRequest) -> dict[str, Any]:
    """Save a prompt."""
    state = request.app.state.freya
    
    if not state.ready or not state.config:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    prompts_root = state.config.prompts_root
    
    # Handle bmad/ prefix
    if body.name.startswith("bmad/"):
        path = prompts_root / "bmad_roles" / f"{body.name[5:]}.md"
    else:
        path = prompts_root / f"{body.name}.md"
    
    # Security check
    try:
        path = path.resolve()
        if prompts_root.resolve() not in path.parents and path.parent != prompts_root.resolve():
            raise HTTPException(status_code=403, detail="Access denied")
    except Exception:
        raise HTTPException(status_code=403, detail="Invalid path")
    
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body.content, encoding="utf-8")
        return {
            "saved": True,
            "name": body.name,
            "path": str(path),
            "size_bytes": len(body.content.encode("utf-8"))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save prompt: {e}")


@router.get("/env")
async def get_env_vars() -> dict[str, str | None]:
    """Get Freya-related environment variables (values redacted for security)."""
    freya_vars = {}
    for key, value in os.environ.items():
        if key.startswith("FREYA_"):
            # Redact sensitive values
            if any(s in key.upper() for s in ["KEY", "TOKEN", "SECRET", "PASSWORD"]):
                freya_vars[key] = "[REDACTED]"
            else:
                freya_vars[key] = value
    return freya_vars


@router.get("/version")
async def get_version() -> dict[str, str]:
    """Get Freya version information."""
    return {
        "version": "2.3.1",
        "api_version": "2.3",
        "python_version": f"{__import__('sys').version_info.major}.{__import__('sys').version_info.minor}",
    }


# -----------------------------------------------------------------------------
# Hybrid Routing Endpoints (v2.1)
# -----------------------------------------------------------------------------
@router.get("/hybrid-routing")
async def get_hybrid_routing_config(request: Request) -> dict[str, Any]:
    """Get hybrid routing configuration."""
    state = request.app.state.freya
    
    if not state.ready or not state.config:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    cfg = state.config.hybrid_routing
    return {
        "enabled": cfg.enabled,
        "percent_threshold": cfg.percent_threshold,
        "local_min_score": cfg.local_min_score,
        "fallback_chain": cfg.fallback_chain,
        "health_timeout_sec": cfg.health_timeout_sec,
        "health_check_interval_min": cfg.health_check_interval_min,
        "max_retries": cfg.max_retries,
        "quota_cache_sec": cfg.quota_cache_sec,
    }


class HybridRoutingUpdateRequest(BaseModel):
    """Request to update hybrid routing configuration."""
    enabled: bool | None = None
    percent_threshold: float | None = None
    local_min_score: int | None = None
    fallback_chain: list[str] | None = None
    max_retries: int | None = None


@router.post("/hybrid-routing")
async def update_hybrid_routing_config(request: Request, body: HybridRoutingUpdateRequest) -> dict[str, Any]:
    """Update hybrid routing configuration."""
    state = request.app.state.freya
    
    if not state.ready or not state.config:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    cfg = state.config.hybrid_routing
    
    # Update only provided fields
    if body.enabled is not None:
        cfg.enabled = body.enabled
    if body.percent_threshold is not None:
        cfg.percent_threshold = body.percent_threshold
    if body.local_min_score is not None:
        cfg.local_min_score = body.local_min_score
    if body.fallback_chain is not None:
        cfg.fallback_chain = body.fallback_chain
    if body.max_retries is not None:
        cfg.max_retries = body.max_retries
    
    return {
        "success": True,
        "message": "Hybrid routing configuration updated",
        "config": {
            "enabled": cfg.enabled,
            "percent_threshold": cfg.percent_threshold,
            "local_min_score": cfg.local_min_score,
            "fallback_chain": cfg.fallback_chain,
            "max_retries": cfg.max_retries,
        }
    }


@router.get("/providers")
async def get_providers(request: Request) -> dict[str, Any]:
    """Get remote provider configurations."""
    from ...config import PROVIDERS
    
    state = request.app.state.freya
    
    if not state.ready:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    # Return providers with API keys redacted
    providers = {}
    for pid, cfg in PROVIDERS.items():
        providers[pid] = {
            "name": cfg["name"],
            "base_url": cfg["base_url"],
            "enabled": cfg["enabled"],
            "priority": cfg["priority"],
            "models": cfg["models"],
            "rate_limits": cfg.get("rate_limits", {}),
            "free_tier": cfg.get("free_tier", {}),
            "has_api_key": bool(os.environ.get(cfg["api_key_env"], "")),
        }
    
    return providers


@router.get("/provider-health")
async def get_provider_health(request: Request) -> dict[str, Any]:
    """Get health status of all providers."""
    state = request.app.state.freya
    
    if not state.ready or not state.orchestrator:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    return state.orchestrator.get_provider_health()


@router.get("/local-runtimes")
async def get_local_runtimes(request: Request) -> dict[str, Any]:
    """Get status of local LLM runtimes."""
    state = request.app.state.freya
    
    if not state.ready or not state.orchestrator:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    if not state.orchestrator.runtime_detector:
        return {"error": "Runtime detection not available"}
    
    return state.orchestrator.runtime_detector.get_runtime_status()


@router.post("/local-runtimes/detect")
async def detect_local_runtimes(request: Request) -> dict[str, Any]:
    """Trigger detection of local LLM runtimes."""
    state = request.app.state.freya
    
    if not state.ready or not state.orchestrator:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    if not state.orchestrator.runtime_detector:
        return {"error": "Runtime detection not available"}
    
    state.orchestrator.runtime_detector.detect_all_runtimes()
    return state.orchestrator.runtime_detector.get_runtime_status()


@router.get("/usage-stats")
async def get_usage_stats(request: Request) -> dict[str, Any]:
    """Get usage statistics for hybrid routing."""
    state = request.app.state.freya
    
    if not state.ready or not state.orchestrator:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    return state.orchestrator.get_usage_stats()


class PredictConsumptionRequest(BaseModel):
    """Request for consumption prediction."""
    role: str = Field(..., description="BMAD role (analyst, pm, architect, etc.)")
    prompt_tokens: int = Field(default=500, description="Estimated input tokens")
    provider: str = Field(default="local", description="Target provider")


@router.post("/predict-consumption")
async def predict_consumption(request: Request, body: PredictConsumptionRequest) -> dict[str, Any]:
    """Predict token consumption and cost for a task."""
    state = request.app.state.freya
    
    if not state.ready or not state.orchestrator:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    return state.orchestrator.predict_consumption(
        role=body.role,
        prompt_tokens=body.prompt_tokens,
        provider=body.provider,
    )


class UpdateProviderKeyRequest(BaseModel):
    """Request to update a provider API key."""
    provider: str = Field(..., description="Provider ID (hf, together, groq)")
    api_key: str = Field(..., description="API key")


@router.post("/provider-key")
async def update_provider_key(request: Request, body: UpdateProviderKeyRequest) -> dict[str, Any]:
    """Update a provider API key (stored in environment)."""
    from ...config import PROVIDERS
    
    if body.provider not in PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {body.provider}")
    
    env_var = PROVIDERS[body.provider]["api_key_env"]
    
    # Set environment variable for current session
    os.environ[env_var] = body.api_key
    
    return {
        "success": True,
        "provider": body.provider,
        "message": f"API key set for {PROVIDERS[body.provider]['name']}. Note: This only persists for the current session.",
    }


@router.post("/sync-bmad")
async def sync_bmad(request: Request) -> dict[str, Any]:
    """Sync BMAD method from GitHub."""
    state = request.app.state.freya
    
    if not state.ready or not state.orchestrator:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        result = state.orchestrator.sync_bmad()
        return {"success": True, "message": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"BMAD sync failed: {e}")


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def _ensure_default_prompts(prompts_root: Path) -> None:
    """Ensure default prompts exist."""
    prompts_root.mkdir(parents=True, exist_ok=True)
    bmad_dir = prompts_root / "bmad_roles"
    bmad_dir.mkdir(parents=True, exist_ok=True)
    
    # Chat base prompt
    chat_path = prompts_root / "chat_base_fr.md"
    if not chat_path.exists():
        chat_path.write_text(DEFAULT_CHAT_BASE_FR, encoding="utf-8")
    
    # Role prompts
    for role, content in DEFAULT_ROLE_PROMPTS.items():
        role_path = bmad_dir / f"{role}.md"
        if not role_path.exists():
            role_path.write_text(content + "\n", encoding="utf-8")
