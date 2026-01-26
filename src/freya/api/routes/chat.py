# src/freya/api/routes/chat.py
"""
Chat API Routes

Endpoints for LLM chat interactions:
- Single message generation
- Streaming responses
- Chat history management
- Hat/persona selection
"""

from __future__ import annotations

import asyncio
import datetime as dt
import re
import threading
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

router = APIRouter()


# -----------------------------------------------------------------------------
# Request/Response Models
# -----------------------------------------------------------------------------
class ChatMessage(BaseModel):
    """A single chat message."""
    role: str = Field(..., description="Message role: user, assistant, system, tool")
    content: str = Field(..., description="Message content")
    timestamp: str | None = Field(default=None)


class ChatRequest(BaseModel):
    """Chat generation request."""
    message: str = Field(..., description="User message")
    model: str | None = Field(default=None, description="Model to use (auto-select if None)")
    system_prompt: str | None = Field(default=None, description="Custom system prompt")
    hat: str | None = Field(default=None, description="Hat/persona preset name")
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1024, ge=1, le=8192)
    stream: bool = Field(default=False, description="Enable streaming response")


class ChatResponse(BaseModel):
    """Chat generation response."""
    content: str
    model: str
    duration_ms: int
    tokens_estimated: int | None = None


class HatPreset(BaseModel):
    """A hat/persona preset."""
    name: str
    description: str
    system_prompt: str


# -----------------------------------------------------------------------------
# Security: Redact secrets from responses
# -----------------------------------------------------------------------------
_SECRET_PATTERNS = [
    re.compile(r"github_pat_[A-Za-z0-9_]+"),
    re.compile(r"\bghp_[A-Za-z0-9]+\b"),
    re.compile(r"\bsk-[A-Za-z0-9]+\b"),
    re.compile(r"Bearer\s+[A-Za-z0-9\-_.]+"),
]


def redact_secrets(text: str) -> str:
    """Remove potential secrets from text."""
    result = text
    for pattern in _SECRET_PATTERNS:
        result = pattern.sub("[REDACTED]", result)
    return result


# -----------------------------------------------------------------------------
# Default Prompts and Hats
# -----------------------------------------------------------------------------
DEFAULT_SYSTEM_PROMPT_FR = """Tu es Freya, une assistante IA experte en développement logiciel.
Tu réponds en français, de façon claire, structurée et actionnable.

Cadre:
- Réponses légales et éthiques uniquement
- Approche défensive par défaut pour la sécurité
- Cite tes sources quand tu utilises des informations externes
- Format Markdown pour la lisibilité
"""

DEFAULT_HATS: dict[str, dict[str, str]] = {
    "blue_hat": {
        "name": "Blue Hat (Défense)",
        "description": "Blue team défensif: durcissement, patch, audit, SOC, IR",
        "system_prompt": "Tu adoptes une posture Blue Team défensive. Focus sur le durcissement, les patches, l'audit de sécurité, SOC et réponse aux incidents. Tu refuses toute demande illégale."
    },
    "white_hat": {
        "name": "White Hat (Pentest légal)", 
        "description": "Pentest autorisé: méthodologie, périmètre, reporting",
        "system_prompt": "Tu es un pentester éthique. Tu discutes méthodologie, périmètre, reporting et remédiation. Pas de détails exploitables sans contexte d'autorisation."
    },
    "grey_hat": {
        "name": "Grey Hat (Research)",
        "description": "Veille CVE, analyse de risques, mitigations",
        "system_prompt": "Tu es un chercheur en sécurité. Tu analyses les CVE, risques et mitigations. Concepts high-level, pas de step-by-step d'exploitation."
    },
    "dev": {
        "name": "Developer",
        "description": "Développement logiciel, code review, architecture",
        "system_prompt": "Tu es un développeur senior expert. Tu aides à coder, reviewer, architecturer. Code propre, testé, documenté."
    },
    "architect": {
        "name": "Architect",
        "description": "Architecture logicielle, patterns, scalabilité",
        "system_prompt": "Tu es un architecte logiciel. Tu conseilles sur les patterns, la scalabilité, la maintenabilité et les choix technologiques."
    }
}


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------
@router.get("/hats")
async def list_hats() -> list[HatPreset]:
    """List available hat/persona presets."""
    return [
        HatPreset(
            name=key,
            description=data["description"],
            system_prompt=data["system_prompt"]
        )
        for key, data in DEFAULT_HATS.items()
    ]


@router.post("/generate", response_model=ChatResponse)
async def generate_chat(request: Request, body: ChatRequest) -> ChatResponse:
    """
    Generate a chat response.
    
    If stream=True, returns a streaming response instead.
    """
    state = request.app.state.freya
    
    if not state.ready or not state.ollama:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    # Select model
    model = body.model
    if not model:
        models = state.router.list_models()
        if not models:
            raise HTTPException(status_code=503, detail="No models available")
        # Prefer certain models
        for preferred in ["llama3.1:8b", "mistral:7b", "dolphin-llama3:8b"]:
            if preferred in models:
                model = preferred
                break
        if not model:
            model = models[0]
    
    # Build system prompt
    system = body.system_prompt or DEFAULT_SYSTEM_PROMPT_FR
    if body.hat and body.hat in DEFAULT_HATS:
        hat_prompt = DEFAULT_HATS[body.hat]["system_prompt"]
        system = f"{system}\n\n{hat_prompt}"
    
    # Add date context
    today = dt.date.today().isoformat()
    system = f"{system}\n\nDate: {today}"
    
    # Generate response
    try:
        result = state.ollama.generate(
            model=model,
            prompt=body.message,
            system=system,
            options_extra={
                "temperature": body.temperature,
                "num_predict": body.max_tokens,
                "top_p": 0.9,
                "repeat_penalty": 1.05,
            }
        )
        
        content = redact_secrets(result.response.strip())
        
        return ChatResponse(
            content=content,
            model=model,
            duration_ms=result.duration_ms,
            tokens_estimated=len(content.split()) * 2  # Rough estimate
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {e}")


@router.post("/search")
async def web_search(request: Request, query: str, limit: int = 5) -> list[dict[str, str]]:
    """
    Perform a web search (Wikipedia API).
    """
    from ...tools.websearch import WebSearch
    
    try:
        searcher = WebSearch(provider="wikipedia", brave_api_key="", user_agent="Freya/2.0")
        results = searcher.search(query, count=limit)
        return [
            {
                "title": r.title,
                "url": r.url,
                "snippet": r.snippet,
                "source": r.source
            }
            for r in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")
