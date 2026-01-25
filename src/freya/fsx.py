from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
import shutil


@dataclass(frozen=True)
class FileWriteResult:
    path: Path
    bytes_written: int
    sha256: str


class Fs:
    def __init__(self, workspace_root: Path, managed_root: Path, protected_names: set[str]) -> None:
        self.workspace_root = workspace_root.resolve()
        self.managed_root = managed_root.resolve()
        self.protected_names = protected_names

        self.managed_root.mkdir(parents=True, exist_ok=True)

    def _is_protected(self, path: Path) -> bool:
        parts = set(path.parts)
        return any(p in parts for p in self.protected_names)

    def resolve_in_workspace(self, path: Path) -> Path:
        p = (self.workspace_root / path).resolve() if not path.is_absolute() else path.resolve()
        if self.workspace_root not in p.parents and p != self.workspace_root:
            raise PermissionError(f"Path outside workspace blocked: {p}")
        return p

    def resolve_in_managed(self, rel: Path) -> Path:
        rel = Path(rel)
        if rel.is_absolute():
            raise ValueError("Managed paths must be relative")
        p = (self.managed_root / rel).resolve()
        if self.managed_root not in p.parents and p != self.managed_root:
            raise PermissionError(f"Path escape blocked: {p}")
        return p

    def read_text(self, path: Path, encoding: str = "utf-8") -> str:
        p = path.resolve()
        return p.read_text(encoding=encoding)

    def write_text(self, path: Path, content: str, encoding: str = "utf-8") -> FileWriteResult:
        p = path.resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        data = content.encode(encoding)
        p.write_bytes(data)
        h = hashlib.sha256(data).hexdigest()
        return FileWriteResult(path=p, bytes_written=len(data), sha256=h)

    def copytree(self, src: Path, dst: Path, overwrite: bool = True) -> None:
        if overwrite and dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)

    def safe_delete_managed(self, rel: Path) -> None:
        """Delete only inside managed_root, never touch workspace arbitrary paths."""
        p = self.resolve_in_managed(rel)
        if self._is_protected(p):
            raise PermissionError(f"Protected path blocked: {p}")
        if p.is_dir():
            shutil.rmtree(p)
        elif p.exists():
            p.unlink()

    def ensure_dirs(self) -> None:
        for sub in ["artifacts", "logs", "cache", "reports", "tmp", "bmad"]:
            self.resolve_in_managed(Path(sub)).mkdir(parents=True, exist_ok=True)
