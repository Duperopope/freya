from __future__ import annotations

import subprocess
from pathlib import Path


class PowerShell:
    def __init__(self, cwd: Path) -> None:
        self.cwd = cwd.resolve()

    def run(self, command: str, timeout_sec: int = 600) -> subprocess.CompletedProcess[str]:
        # -NoProfile for predictability; -NonInteractive for automation
        argv = ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command]
        return subprocess.run(
            argv,
            cwd=str(self.cwd),
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            shell=False,
        )
