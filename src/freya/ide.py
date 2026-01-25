from __future__ import annotations

import shutil
from pathlib import Path
from .powershell import PowerShell


class IDEController:
    """
    Pragmatic VS Code control on Windows:
    - open file at line via 'code -g'
    - rely on filesystem edits + running commands in PowerShell
    """

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root.resolve()
        self.ps = PowerShell(self.workspace_root)

    def has_code_cli(self) -> bool:
        return shutil.which("code") is not None

    def open_file(self, rel_path: Path, line: int = 1, col: int = 1) -> str:
        if not self.has_code_cli():
            return "VS Code CLI (code) not found in PATH."
        p = (self.workspace_root / rel_path).resolve()
        cp = self.ps.run(f'code -g "{p}:{line}:{col}"', timeout_sec=30)
        if cp.returncode == 0:
            return f"Opened in VS Code: {rel_path}:{line}:{col}"
        return f"Failed to open VS Code file: {cp.stderr.strip()}"

    def run_task_like(self, command: str, timeout_sec: int = 900) -> tuple[int, str, str]:
        cp = self.ps.run(command, timeout_sec=timeout_sec)
        return cp.returncode, cp.stdout, cp.stderr
