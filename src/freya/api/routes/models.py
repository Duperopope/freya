# src/freya/api/routes/models.py
"""
Models API Routes

Endpoints for Ollama model management:
- List installed models
- Get model details
- Pull new models
- Delete models
- Model registry
"""

from __future__ import annotations

import asyncio
import threading
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel, Field

from ..websocket import ChannelType, WSMessage

router = APIRouter()


# -----------------------------------------------------------------------------
# Request/Response Models
# -----------------------------------------------------------------------------
class ModelInfo(BaseModel):
    """Information about an installed model."""
    name: str
    size_bytes: int | None = None
    size_gb: float | None = None
    modified_at: str | None = None
    is_freya_pulled: bool = False


class ModelDetails(BaseModel):
    """Detailed model information."""
    name: str
    modelfile: str | None = None
    parameters: dict[str, Any] = {}
    template: str | None = None
    license: str | None = None


class PullRequest(BaseModel):
    """Request to pull a model."""
    model: str = Field(..., description="Model name to pull (e.g., llama3.1:8b)")


class DeleteRequest(BaseModel):
    """Request to delete a model."""
    model: str = Field(..., description="Model name to delete")
    only_freya_pulled: bool = Field(default=True, description="Only delete if pulled by Freya")


class RoutingConfig(BaseModel):
    """Routing configuration for a role."""
    role: str
    model: str
    options: dict[str, Any] = {}


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------
@router.get("/", response_model=list[ModelInfo])
async def list_models(request: Request) -> list[ModelInfo]:
    """List all installed Ollama models."""
    state = request.app.state.freya
    
    if not state.ready or not state.orchestrator:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    models = state.orchestrator.models.installed()
    registry = state.orchestrator.registry
    
    return [
        ModelInfo(
            name=m.name,
            size_bytes=m.size_bytes,
            size_gb=round(m.size_gb, 2) if m.size_gb else None,
            modified_at=m.modified_at,
            is_freya_pulled=registry.is_freya_pulled(m.name)
        )
        for m in models
    ]


@router.get("/details")
async def get_model_details(request: Request, name: str) -> ModelDetails:
    """Get detailed information about a model."""
    state = request.app.state.freya
    
    if not state.ready or not state.ollama:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        info = state.ollama.show(name)
        return ModelDetails(
            name=name,
            modelfile=info.get("modelfile"),
            parameters=info.get("parameters", {}),
            template=info.get("template"),
            license=info.get("license")
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Model not found: {e}")


@router.post("/pull")
async def pull_model(
    request: Request,
    body: PullRequest,
    background_tasks: BackgroundTasks
) -> dict[str, Any]:
    """
    Pull a model from Ollama registry.
    
    Progress is streamed via WebSocket (channel: system).
    """
    state = request.app.state.freya
    
    if not state.ready or not state.ollama:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    def pull_in_background():
        ws_manager = state.ws_manager
        
        try:
            if ws_manager:
                ws_manager.broadcast_sync(WSMessage(
                    channel=ChannelType.SYSTEM,
                    event="pull_started",
                    data={"model": body.model}
                ))
            
            # Stream pull progress
            for chunk in state.ollama.pull_stream(body.model):
                status = chunk.get("status", "")
                completed = chunk.get("completed", 0)
                total = chunk.get("total", 0)
                
                if ws_manager:
                    ws_manager.broadcast_sync(WSMessage(
                        channel=ChannelType.SYSTEM,
                        event="pull_progress",
                        data={
                            "model": body.model,
                            "status": status,
                            "completed": completed,
                            "total": total,
                            "percent": round((completed / total) * 100, 1) if total > 0 else 0
                        }
                    ))
            
            # Mark as pulled by Freya
            state.orchestrator.registry.mark_pulled(body.model, "api_pull")
            
            if ws_manager:
                ws_manager.broadcast_sync(WSMessage(
                    channel=ChannelType.SYSTEM,
                    event="pull_complete",
                    data={"model": body.model}
                ))
        
        except Exception as e:
            if ws_manager:
                ws_manager.broadcast_sync(WSMessage(
                    channel=ChannelType.SYSTEM,
                    event="pull_error",
                    data={"model": body.model, "error": str(e)}
                ))
    
    thread = threading.Thread(target=pull_in_background, daemon=True)
    thread.start()
    
    return {
        "started": True,
        "model": body.model,
        "message": "Pull started. Watch WebSocket channel 'system' for progress."
    }


@router.delete("/")
async def delete_model(request: Request, body: DeleteRequest) -> dict[str, Any]:
    """
    Delete an installed model.
    
    By default, only deletes models that were pulled by Freya for safety.
    """
    state = request.app.state.freya
    
    if not state.ready or not state.orchestrator:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    registry = state.orchestrator.registry
    
    # Safety check
    if body.only_freya_pulled and not registry.is_freya_pulled(body.model):
        raise HTTPException(
            status_code=403,
            detail=f"Model '{body.model}' was not pulled by Freya. Set only_freya_pulled=false to force delete."
        )
    
    try:
        state.ollama.delete(body.model)
        return {"deleted": True, "model": body.model}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {e}")


@router.get("/routing", response_model=list[RoutingConfig])
async def get_routing(request: Request) -> list[RoutingConfig]:
    """Get current model routing configuration."""
    state = request.app.state.freya
    
    if not state.ready or not state.orchestrator:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    routing = state.orchestrator.load_routing()
    
    configs = []
    for role in ["analyst", "pm", "architect", "po", "sm", "dev", "qa"]:
        v = routing.get(role, {})
        if isinstance(v, str):
            model = v
            options = {}
        elif isinstance(v, dict):
            model = v.get("model", "")
            options = v.get("options", {})
        else:
            model = ""
            options = {}
        
        if not model:
            model = getattr(state.config.models, role, "llama3.1:8b")
        
        configs.append(RoutingConfig(
            role=role,
            model=model,
            options=options
        ))
    
    return configs


@router.post("/routing")
async def set_routing(request: Request, configs: list[RoutingConfig]) -> dict[str, Any]:
    """Set model routing configuration."""
    state = request.app.state.freya
    
    if not state.ready or not state.orchestrator:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    routing = {}
    for config in configs:
        routing[config.role] = {
            "model": config.model,
            "options": config.options
        }
    
    state.orchestrator.save_routing(routing)
    
    return {
        "saved": True,
        "path": str(state.orchestrator.routing_path),
        "roles": list(routing.keys())
    }


@router.get("/recommended")
async def get_recommended_models() -> list[dict[str, str]]:
    """Get list of recommended models for different use cases."""
    return [
        {
            "name": "llama3.1:8b",
            "description": "Excellent all-around model, good balance of speed and quality",
            "use_case": "General purpose, analysis, writing"
        },
        {
            "name": "llama3.1:70b",
            "description": "Highest quality, requires significant resources",
            "use_case": "Complex reasoning, architecture decisions"
        },
        {
            "name": "mistral:7b",
            "description": "Fast and efficient, good for simple tasks",
            "use_case": "Quick responses, summaries"
        },
        {
            "name": "codellama:13b",
            "description": "Specialized for code generation",
            "use_case": "Development, code review"
        },
        {
            "name": "deepseek-coder-v2:latest",
            "description": "State-of-the-art code model",
            "use_case": "Development, complex code generation"
        },
        {
            "name": "dolphin-llama3:8b",
            "description": "Uncensored, good for security research",
            "use_case": "Security analysis, pentesting documentation"
        },
        {
            "name": "qwen2.5:7b",
            "description": "Good multilingual support",
            "use_case": "French/English tasks, documentation"
        }
    ]
