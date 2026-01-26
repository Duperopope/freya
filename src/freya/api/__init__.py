# src/freya/api/__init__.py
"""
Freya Web API - FastAPI backend for the modern web interface.

This module provides:
- RESTful API endpoints for all Freya functionality
- WebSocket support for real-time updates (bench progress, logs)
- Integration with existing Freya core modules

Architecture:
    api/
    ├── main.py          # FastAPI app, CORS, lifespan
    ├── websocket.py     # WebSocket manager for real-time
    └── routes/
        ├── chat.py      # Chat with LLM agents
        ├── bench.py     # Benchmark operations
        ├── bmad.py      # BMAD workflow orchestration
        ├── models.py    # Ollama model management
        ├── files.py     # File browser & editor
        ├── watch.py     # Cyber security watch
        └── settings.py  # Configuration management
"""

from .main import create_app

__all__ = ["create_app"]
