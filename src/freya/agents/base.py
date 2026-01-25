from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..ollama_client import OllamaClient
from ..router import LLMRouter
from ..fsx import Fs


@dataclass(frozen=True)
class AgentContext:
    goal: str
    artifacts_root: Path
    workspace_root: Path


class BaseAgent:
    def __init__(
        self,
        name: str,
        fs: Fs,
        ollama: OllamaClient,
        router: LLMRouter,
        model_fallback: str,
        model_options: dict[str, Any] | None = None,
    ) -> None:
        self.name = name
        self.fs = fs
        self.ollama = ollama
        self.router = router
        self.model_fallback = model_fallback
        self.model_options: dict[str, Any] = dict(model_options) if isinstance(model_options, dict) else {}

    def _read(self, p: Path) -> str:
        return self.fs.read_text(p)

    def _write(self, p: Path, content: str) -> Path:
        self.fs.write_text(p, content)
        return p

    def _gen(self, *, role: str, prompt: str, system: str) -> str:
        """
        Uses the model assigned to this agent + tuned options (if any).
        Bench writes best options per role into routing.json; we apply them here.
        """
        res = self.ollama.generate(
            model=self.model_fallback,
            prompt=prompt,
            system=system,
            temperature=0.0,
            top_p=1.0,
            options_extra=self.model_options,
        )
        return (res.response or "").strip()
