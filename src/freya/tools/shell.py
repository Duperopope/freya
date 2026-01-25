from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ShellResult:
    cmd: str
    ok: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int


DEFAULT_ALLOW_PREFIX = (
    "freya ",
    "ollama ",
    "git ",
    "code ",
    "python ",
    "pytest",
    "ruff",
    "dir",
    "Get-ChildItem",
)


DANGEROUS_TOKENS = (
    "rm ",
    "del ",
    "Remove-Item",
    "Format-Volume",
    "Clear-Disk",
    "diskpart",
    "shutdown",
    "reboot",
)


def run_powershell(
    *,
    cmd: str,
    audit_log: Path,
    timeout_sec: int = 30,
    allow_prefix: tuple[str, ...] = DEFAULT_ALLOW_PREFIX,
    require_approval_for_non_allowlisted: bool = True,
    approved: bool = False,
) -> ShellResult:
    start = time.perf_counter()
    cmd_stripped = cmd.strip()

    # Safety gate
    if any(tok.lower() in cmd_stripped.lower() for tok in DANGEROUS_TOKENS):
        raise ValueError("Commande refusée (token dangereux détecté).")

    allowlisted = cmd_stripped.startswith(allow_prefix)
    if require_approval_for_non_allowlisted and (not allowlisted) and (not approved):
        raise PermissionError("Commande non allowlistée: approval requise.")

    p = subprocess.run(
        ["powershell", "-NoProfile", "-Command", cmd_stripped],
        capture_output=True,
        text=True,
        timeout=timeout_sec,
    )
    dur_ms = int((time.perf_counter() - start) * 1000)

    res = ShellResult(
        cmd=cmd_stripped,
        ok=(p.returncode == 0),
        exit_code=int(p.returncode),
        stdout=p.stdout or "",
        stderr=p.stderr or "",
        duration_ms=dur_ms,
    )

    audit_log.parent.mkdir(parents=True, exist_ok=True)
    audit_log.write_text("", encoding="utf-8") if not audit_log.exists() else None
    with audit_log.open("a", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {
                    "ts": time.time(),
                    "cmd": res.cmd,
                    "ok": res.ok,
                    "exit_code": res.exit_code,
                    "duration_ms": res.duration_ms,
                }
            )
            + "\n"
        )

    return res
