from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Optional


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())


def _jsonl_append(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _slug(s: str, max_len: int = 60) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9\-_\s]", "", s)
    s = re.sub(r"[\s]+", "-", s)
    s = s.strip("-_")
    return (s[:max_len] or "freya-project")


@dataclass
class ShellResult:
    cmd: str
    cwd: str
    returncode: int
    stdout: str
    stderr: str
    duration_ms: int


def run_cmd(cmd: str, cwd: Path, timeout_sec: int = 1800) -> ShellResult:
    """
    Windows-friendly runner: execute via Windows PowerShell host to avoid quoting edge cases.
    Ref: subprocess.run docs https://docs.python.org/3/library/subprocess.html#subprocess.run
    """
    t0 = time.time()
    ps = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
    completed = subprocess.run(
        [ps, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", cmd],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=timeout_sec,
    )
    dt_ms = int((time.time() - t0) * 1000)
    return ShellResult(
        cmd=cmd,
        cwd=str(cwd),
        returncode=completed.returncode,
        stdout=completed.stdout or "",
        stderr=completed.stderr or "",
        duration_ms=dt_ms,
    )


@dataclass
class AutopilotConfig:
    goal: str
    output_dir: str
    project_name: str
    max_fix_iters: int = 3
    open_vscode: bool = True


@dataclass
class AutopilotState:
    run_id: str
    step: str
    fix_iter: int
    last_test_returncode: Optional[int] = None


class FreyaAutopilot:
    """
    Autopilot V1: scaffold + tests + open VS Code.
    V2: BMAD + LLM patch loop + full app generation.
    """

    def __init__(self, cfg: AutopilotConfig) -> None:
        self.cfg = cfg
        self.root = Path(cfg.output_dir).resolve()
        self.meta = self.root / ".freya"
        self.events = self.meta / "events.jsonl"
        self.state_path = self.meta / "state.json"
        self.run_id = f"run_{int(time.time())}"
        self.state = AutopilotState(run_id=self.run_id, step="init", fix_iter=0)

    def _save_state(self) -> None:
        self.meta.mkdir(parents=True, exist_ok=True)
        with self.state_path.open("w", encoding="utf-8") as f:
            json.dump(asdict(self.state), f, ensure_ascii=False, indent=2)

    def _event(self, kind: str, **data: Any) -> None:
        _jsonl_append(
            self.events,
            {"ts": _now_iso(), "run_id": self.run_id, "kind": kind, **data},
        )

    def init_project_dir(self) -> None:
        self.state.step = "init_project_dir"
        self._event("step_start", step=self.state.step, output_dir=str(self.root))
        self.root.mkdir(parents=True, exist_ok=True)
        self.meta.mkdir(parents=True, exist_ok=True)

        spec = (
            f"# SPEC — {self.cfg.project_name}\n\n"
            "## Objectif (goal)\n"
            f"{self.cfg.goal}\n\n"
            "## Definition of Done (DoD)\n"
            "- L'application démarre localement.\n"
            "- Les tests automatisés passent (pytest).\n"
            "- Un endpoint /health répond 200.\n"
            "- README présent avec instructions.\n\n"
            "## Notes\n"
            "Généré par Freya Autopilot (V1).\n"
        )
        (self.root / "SPEC.md").write_text(spec, encoding="utf-8")
        self._event("file_write", path="SPEC.md", bytes=len(spec.encode("utf-8")))
        self._save_state()
        self._event("step_done", step=self.state.step)

    def create_venv_and_install(self) -> Path:
        self.state.step = "create_venv_and_install"
        self._event("step_start", step=self.state.step)

        py = Path(sys.executable).resolve()
        venv_dir = self.root / ".venv"
        venv_py = venv_dir / "Scripts" / "python.exe"

        if not venv_py.exists():
            r = run_cmd(f'& "{py}" -m venv ".venv"', cwd=self.root, timeout_sec=1200)
            self._event("cmd", **asdict(r))
            if r.returncode != 0:
                raise RuntimeError(f"venv creation failed:\n{r.stderr}\n{r.stdout}")

        r = run_cmd(f'& "{venv_py}" -m pip install -U pip', cwd=self.root, timeout_sec=1200)
        self._event("cmd", **asdict(r))
        if r.returncode != 0:
            raise RuntimeError(f"pip upgrade failed:\n{r.stderr}\n{r.stdout}")

        deps = ["fastapi", "uvicorn", "pytest", "httpx"]
        r = run_cmd(f'& "{venv_py}" -m pip install ' + " ".join(deps), cwd=self.root, timeout_sec=1800)
        self._event("cmd", **asdict(r))
        if r.returncode != 0:
            raise RuntimeError(f"deps install failed:\n{r.stderr}\n{r.stdout}")

        self._save_state()
        self._event("step_done", step=self.state.step)
        return venv_py

    def write_app_files(self) -> None:
        self.state.step = "write_app_files"
        self._event("step_start", step=self.state.step)

        app_dir = self.root / "app"
        app_dir.mkdir(parents=True, exist_ok=True)

        main_py = (
            "from fastapi import FastAPI\n\n"
            'app = FastAPI(title="FreyaApp", version="0.1.0")\n\n'
            '@app.get("/health")\n'
            "def health():\n"
            '    return {"status": "ok"}\n\n'
            '@app.get("/")\n'
            "def root():\n"
            '    return {"app": "FreyaApp", "message": "Hello from Freya Autopilot"}\n'
        )
        (app_dir / "__init__.py").write_text("", encoding="utf-8")
        (app_dir / "main.py").write_text(main_py, encoding="utf-8")
        self._event("file_write", path="app/main.py", bytes=len(main_py.encode("utf-8")))

        tests_dir = self.root / "tests"
        tests_dir.mkdir(parents=True, exist_ok=True)

        test_py = (
            "from fastapi.testclient import TestClient\n"
            "from app.main import app\n\n"
            "client = TestClient(app)\n\n"
            "def test_health_ok():\n"
            '    r = client.get("/health")\n'
            "    assert r.status_code == 200\n"
            '    assert r.json()["status"] == "ok"\n'
        )
        (tests_dir / "test_health.py").write_text(test_py, encoding="utf-8")
        self._event("file_write", path="tests/test_health.py", bytes=len(test_py.encode("utf-8")))

        readme = (
            f"# {self.cfg.project_name}\n\n"
            "## Goal\n"
            f"{self.cfg.goal}\n\n"
            "## Run\n"
            "```powershell\n"
            ".\\.venv\\Scripts\\python.exe -m uvicorn app.main:app --reload\n"
            "```\n\n"
            "## Test\n"
            "```powershell\n"
            ".\\.venv\\Scripts\\python.exe -m pytest -q\n"
            "```\n"
        )
        (self.root / "README.md").write_text(readme, encoding="utf-8")
        self._event("file_write", path="README.md", bytes=len(readme.encode("utf-8")))

        vscode_dir = self.root / ".vscode"
        vscode_dir.mkdir(parents=True, exist_ok=True)
        tasks = {
            "version": "2.0.0",
            "tasks": [
                {
                    "label": "Run API (uvicorn)",
                    "type": "shell",
                    "command": r".\.venv\Scripts\python.exe -m uvicorn app.main:app --reload",
                    "problemMatcher": [],
                },
                {
                    "label": "Run tests (pytest)",
                    "type": "shell",
                    "command": r".\.venv\Scripts\python.exe -m pytest -q",
                    "problemMatcher": [],
                },
            ],
        }
        tasks_json = json.dumps(tasks, ensure_ascii=False, indent=2)
        (vscode_dir / "tasks.json").write_text(tasks_json, encoding="utf-8")
        self._event("file_write", path=".vscode/tasks.json", bytes=len(tasks_json.encode("utf-8")))

        self._save_state()
        self._event("step_done", step=self.state.step)

    def run_tests(self, venv_py: Path) -> ShellResult:
        self.state.step = "run_tests"
        self._event("step_start", step=self.state.step)
        r = run_cmd(f'& "{venv_py}" -m pytest -q', cwd=self.root, timeout_sec=1800)
        self._event("cmd", **asdict(r))
        self.state.last_test_returncode = r.returncode
        self._save_state()
        self._event("step_done", step=self.state.step, returncode=r.returncode)
        return r

    def attempt_fix_from_test_output(self, test_result: ShellResult) -> bool:
        """
        V1: no LLM patching yet (stability first).
        V2: Dev/QA LLM will patch code based on failing tests.
        """
        self.state.step = "attempt_fix"
        self._event("step_start", step=self.state.step, fix_iter=self.state.fix_iter)
        self._event("fix_noop", reason="V1 scaffold should pass; inspect .freya/events.jsonl if not.")
        self._save_state()
        self._event("step_done", step=self.state.step, applied=False)
        return False

    def open_in_vscode(self) -> None:
        if not self.cfg.open_vscode:
            return
        self.state.step = "open_vscode"
        self._event("step_start", step=self.state.step)

        # VS Code CLI: https://code.visualstudio.com/docs/editor/command-line
        try:
            r = subprocess.run(
                ["code", "-r", str(self.root)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            self._event(
                "cmd_external",
                cmd="code -r <project>",
                returncode=r.returncode,
                stdout=r.stdout or "",
                stderr=r.stderr or "",
            )
        except Exception as e:
            self._event("cmd_external_error", cmd="code -r <project>", error=repr(e))

        self._save_state()
        self._event("step_done", step=self.state.step)

    def run(self) -> None:
        self._event("run_start", cfg=asdict(self.cfg))

        self.init_project_dir()
        venv_py = self.create_venv_and_install()
        self.write_app_files()

        for i in range(self.cfg.max_fix_iters + 1):
            self.state.fix_iter = i
            self._save_state()

            test_res = self.run_tests(venv_py)
            if test_res.returncode == 0:
                self._event("run_done", status="success")
                self.open_in_vscode()
                return

            self._event("tests_failed", iter=i)
            applied = self.attempt_fix_from_test_output(test_res)
            if not applied:
                break

        self._event("run_done", status="failed", hint="Inspect .freya/events.jsonl stderr/stdout of last cmd")
        self.open_in_vscode()
        raise RuntimeError("Autopilot failed: tests not passing. See .freya/events.jsonl")
