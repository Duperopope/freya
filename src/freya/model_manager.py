from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .ollama_client import OllamaClient
from .monitoring import Monitor


@dataclass(frozen=True)
class InstalledModel:
    name: str
    size_bytes: int | None
    modified_at: str | None

    @property
    def size_gb(self) -> float | None:
        if self.size_bytes is None:
            return None
        return self.size_bytes / (1024**3)


class ModelRegistry:
    """
    Tracks what Freya pulled so pruning is safe.
    Stored in: .freya/cache/model_registry.json
    """
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"pulled_by_freya": {}, "updated_at": None}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {"pulled_by_freya": {}, "updated_at": None}

    def save(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def mark_pulled(self, model: str, reason: str) -> None:
        data = self.load()
        pb = data.setdefault("pulled_by_freya", {})
        pb[model] = {"reason": reason}
        data["updated_at"] = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
        self.save(data)

    def is_freya_pulled(self, model: str) -> bool:
        data = self.load()
        return model in (data.get("pulled_by_freya") or {})


class ModelManager:
    def __init__(self, ollama: OllamaClient, monitor: Monitor, registry: ModelRegistry) -> None:
        self.ollama = ollama
        self.monitor = monitor
        self.registry = registry

    def installed(self) -> list[InstalledModel]:
        models = self.ollama.tags()
        out: list[InstalledModel] = []
        for m in models:
            out.append(
                InstalledModel(
                    name=m.get("name") or "",
                    size_bytes=m.get("size"),
                    modified_at=m.get("modified_at"),
                )
            )
        out = [x for x in out if x.name]
        out.sort(key=lambda x: x.name)
        return out

    def disk_free_gb(self, workspace_root: Path) -> float:
        st = self.monitor.snapshot()
        return float(st.disk_free_gb)

    def prune_models(self, models_to_remove: list[str], *, dry_run: bool = True, only_freya_pulled: bool = True) -> list[str]:
        removed: list[str] = []
        for m in models_to_remove:
            if only_freya_pulled and not self.registry.is_freya_pulled(m):
                continue
            if dry_run:
                removed.append(m)
                continue
            self.ollama.delete(m)
            removed.append(m)
        return removed
