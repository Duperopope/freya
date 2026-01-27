# src/freya/api/main.py
"""
Freya Web API - Main FastAPI Application

Provides the REST API and WebSocket endpoints for the Freya web interface.
Designed to work alongside the existing CLI and core modules.
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from ..config import FreyaConfig
from ..ollama_client import OllamaClient
from ..router import LLMRouter
from ..orchestrator import Orchestrator

from .websocket import WebSocketManager, websocket_endpoint
from .routes import chat, bench, bmad, models, files, watch, settings

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
logger = logging.getLogger("freya.api")

# -----------------------------------------------------------------------------
# Application State (shared across requests)
# -----------------------------------------------------------------------------
class AppState:
    """
    Centralized application state.
    Initialized at startup, accessible via request.app.state.freya
    """
    def __init__(self) -> None:
        self.config: FreyaConfig | None = None
        self.ollama: OllamaClient | None = None
        self.router: LLMRouter | None = None
        self.orchestrator: Orchestrator | None = None
        self.ws_manager: WebSocketManager | None = None
        self.ready: bool = False


# -----------------------------------------------------------------------------
# Lifespan (startup/shutdown)
# -----------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Initializes all Freya components at startup.
    """
    state = AppState()
    app.state.freya = state
    
    logger.info("Freya API starting up...")
    
    try:
        # Load configuration
        state.config = FreyaConfig.load()
        logger.info(f"Config loaded: managed_root={state.config.managed_root}")
        
        # Initialize Ollama client
        state.ollama = OllamaClient(
            base_url=state.config.ollama.base_url,
            timeout_sec=state.config.ollama.timeout_sec
        )
        logger.info(f"Ollama client: {state.config.ollama.base_url}")
        
        # Initialize LLM Router
        state.router = LLMRouter(state.ollama)
        logger.info("LLM Router initialized")
        
        # Initialize Orchestrator
        state.orchestrator = Orchestrator(state.config, logger)
        logger.info("Orchestrator initialized")
        
        # Initialize WebSocket manager
        state.ws_manager = WebSocketManager()
        logger.info("WebSocket manager initialized")
        
        state.ready = True
        logger.info("Freya API ready!")
        
    except Exception as e:
        logger.error(f"Startup error: {e}")
        state.ready = False
    
    yield
    
    # Shutdown
    logger.info("Freya API shutting down...")
    if state.ws_manager:
        await state.ws_manager.shutdown()


# -----------------------------------------------------------------------------
# App Factory
# -----------------------------------------------------------------------------
def create_app(
    *,
    static_dir: Path | None = None,
    debug: bool = False
) -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Args:
        static_dir: Optional path to serve static files (built web UI)
        debug: Enable debug mode
    
    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="Freya API",
        description="BMAD-aligned multi-agent orchestrator for local LLMs with enhanced UX",
        version="2.3.5",
        docs_url="/api/docs" if debug else None,
        redoc_url="/api/redoc" if debug else None,
        lifespan=lifespan,
    )
    
    # CORS middleware (permissive for development)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(exc), "type": type(exc).__name__}
        )
    
    # Health check
    @app.get("/api/health")
    async def health_check(request: Request) -> dict[str, Any]:
        state: AppState = request.app.state.freya
        
        ollama_ok = False
        models_count = 0
        if state.ollama:
            try:
                tags = state.ollama.tags()
                ollama_ok = True
                models_count = len(tags)
            except Exception:
                pass
        
        return {
            "status": "ok" if state.ready else "degraded",
            "ready": state.ready,
            "ollama": {
                "connected": ollama_ok,
                "models_count": models_count,
                "base_url": state.config.ollama.base_url if state.config else None
            },
            "config": {
                "managed_root": str(state.config.managed_root) if state.config else None,
                "output_root": str(state.config.output_root) if state.config else None,
            }
        }
    
    # System info
    @app.get("/api/system")
    async def system_info(request: Request) -> dict[str, Any]:
        state: AppState = request.app.state.freya
        
        if not state.orchestrator:
            return {"error": "Not initialized"}
        
        snapshot = state.orchestrator.monitor.snapshot()
        return {
            "cpu_percent": snapshot.cpu_percent,
            "ram_percent": snapshot.ram_percent,
            "disk_free_gb": round(snapshot.disk_free_gb, 2),
            "disk_total_gb": round(snapshot.disk_total_gb, 2),
        }
    
    # Include route modules
    app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
    app.include_router(bench.router, prefix="/api/bench", tags=["Benchmark"])
    app.include_router(bmad.router, prefix="/api/bmad", tags=["BMAD"])
    app.include_router(models.router, prefix="/api/models", tags=["Models"])
    app.include_router(files.router, prefix="/api/files", tags=["Files"])
    app.include_router(watch.router, prefix="/api/watch", tags=["Watch"])
    app.include_router(settings.router, prefix="/api/settings", tags=["Settings"])
    
    # WebSocket endpoint (MUST be before static files mount)
    @app.websocket("/ws")
    async def ws_endpoint(websocket: WebSocket):
        """WebSocket endpoint for real-time updates."""
        state: AppState = app.state.freya
        if state.ws_manager:
            await websocket_endpoint(websocket, state.ws_manager)
        else:
            await websocket.close(code=1011, reason="WebSocket manager not initialized")
    
    # Serve static files (built web UI) if provided - MUST be last
    if static_dir and static_dir.exists():
        # Serve static assets
        app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="assets")
        
        # Fallback route for SPA - serve index.html for all non-API routes
        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            """Serve the SPA index.html for client-side routing."""
            from fastapi.responses import FileResponse
            index_path = static_dir / "index.html"
            if index_path.exists():
                return FileResponse(index_path, media_type="text/html")
            return JSONResponse(status_code=404, content={"error": "Not found"})
    
    return app


# -----------------------------------------------------------------------------
# Auto-detect static files directory
# -----------------------------------------------------------------------------
def get_static_dir() -> Path | None:
    """Find the built web UI directory."""
    # Try relative to this file (installed package)
    candidates = [
        Path(__file__).parent.parent.parent.parent / "web" / "dist",  # Development
        Path(__file__).parent / "static",  # Installed package
    ]
    for candidate in candidates:
        if candidate.exists() and (candidate / "index.html").exists():
            return candidate
    return None


# -----------------------------------------------------------------------------
# Development server entry point
# -----------------------------------------------------------------------------
def run_dev_server(host: str = "127.0.0.1", port: int = 8765):
    """Run the development server with auto-reload."""
    import uvicorn
    uvicorn.run(
        "freya.api.main:create_debug_app",
        factory=True,
        host=host,
        port=port,
        reload=True,
        log_level="info",
    )


# Create app with auto-detected static files for debug mode
def create_debug_app() -> FastAPI:
    """Create app with static files and debug enabled."""
    static_dir = get_static_dir()
    return create_app(static_dir=static_dir, debug=True)


# Create app with auto-detected static files for production
def create_production_app() -> FastAPI:
    """Create app with static files for production deployment."""
    static_dir = get_static_dir()
    return create_app(static_dir=static_dir, debug=False)


if __name__ == "__main__":
    run_dev_server()
