from __future__ import annotations

import socket
import subprocess
import time
from pathlib import Path
from dataclasses import dataclass


@dataclass(frozen=True)
class LlamaServerConfig:
    exe: Path
    host: str
    port: int
    ctx_size: int
    threads: int
    ngl: int


class LlamaCppServer:
    def __init__(self, cfg: LlamaServerConfig) -> None:
        self.cfg = cfg
        self.proc: subprocess.Popen[str] | None = None

    def _port_open(self) -> bool:
        try:
            with socket.create_connection((self.cfg.host, self.cfg.port), timeout=0.5):
                return True
        except Exception:
            return False

    def start(self, gguf_path: Path) -> None:
        if not self.cfg.exe.exists():
            raise FileNotFoundError(f"llama-server.exe not found: {self.cfg.exe}")
        if not gguf_path.exists():
            raise FileNotFoundError(f"GGUF not found: {gguf_path}")

        # If port already used, we don't kill anything automatically (safe).
        if self._port_open():
            raise RuntimeError(f"Port {self.cfg.port} already in use. Stop the existing server first.")

        args = [
            str(self.cfg.exe),
            "-m", str(gguf_path),
            "--host", self.cfg.host,
            "--port", str(self.cfg.port),
            "--ctx-size", str(self.cfg.ctx_size),
            "--threads", str(self.cfg.threads),
            "-ngl", str(self.cfg.ngl),
        ]
        self.proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        # wait until port opens (or timeout)
        t0 = time.time()
        while time.time() - t0 < 30:
            if self._port_open():
                return
            time.sleep(0.25)

        # if failed, dump some logs
        out = ""
        if self.proc and self.proc.stdout:
            try:
                out = self.proc.stdout.read()[:2000]
            except Exception:
                pass
        raise RuntimeError(f"llama-server did not start in time. Output:\n{out}")

    def stop(self) -> None:
        if not self.proc:
            return
        try:
            self.proc.terminate()
            self.proc.wait(timeout=10)
        except Exception:
            try:
                self.proc.kill()
            except Exception:
                pass
        finally:
            self.proc = None
