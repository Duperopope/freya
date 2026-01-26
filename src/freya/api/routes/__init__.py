# src/freya/api/routes/__init__.py
"""
Freya API Routes

All API endpoints organized by domain:
- chat: LLM chat interactions
- bench: Benchmark operations
- bmad: BMAD workflow orchestration
- models: Ollama model management
- files: File browser and editor
- watch: Cyber security monitoring
- settings: Configuration management
"""

from . import chat, bench, bmad, models, files, watch, settings

__all__ = [
    "chat",
    "bench", 
    "bmad",
    "models",
    "files",
    "watch",
    "settings",
]
