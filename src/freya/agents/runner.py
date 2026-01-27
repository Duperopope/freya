"""
TestRunner Agent - Runs and validates the generated application.

This agent:
1. Detects the project type (Python, Node.js, etc.)
2. Installs dependencies
3. Runs the application
4. Executes tests
5. Reports results
"""
from __future__ import annotations

import logging
import subprocess
import time
from pathlib import Path
from typing import Optional
from .base import BaseAgent, AgentContext

logger = logging.getLogger("freya.agents.runner")


class TestRunnerAgent(BaseAgent):
    """Agent that runs and validates the generated application."""
    
    def __init__(self, *args, timeout_sec: int = 120, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.timeout_sec = timeout_sec
    
    def _run_command(self, cmd: str, cwd: Path, timeout: int = 60) -> tuple[int, str, str]:
        """Run a shell command and return exit code, stdout, stderr."""
        logger.info(f"[Runner] Executing: {cmd}")
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", f"Command timed out after {timeout}s"
        except Exception as e:
            return -1, "", str(e)
    
    def _detect_project_type(self, code_dir: Path) -> str:
        """Detect the type of project based on files present."""
        if (code_dir / "requirements.txt").exists() or (code_dir / "setup.py").exists() or (code_dir / "pyproject.toml").exists():
            return "python"
        if (code_dir / "package.json").exists():
            return "nodejs"
        if (code_dir / "Cargo.toml").exists():
            return "rust"
        if (code_dir / "go.mod").exists():
            return "go"
        # Check for Python files
        if list(code_dir.glob("*.py")):
            return "python"
        # Check for JS/TS files
        if list(code_dir.glob("*.js")) or list(code_dir.glob("*.ts")):
            return "nodejs"
        return "unknown"
    
    def _find_main_file(self, code_dir: Path, project_type: str) -> Optional[Path]:
        """Find the main entry point file."""
        if project_type == "python":
            for name in ["main.py", "app.py", "run.py", "__main__.py", "server.py"]:
                if (code_dir / name).exists():
                    return code_dir / name
            # Look for any Python file with if __name__ == "__main__"
            for py_file in code_dir.glob("*.py"):
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                if 'if __name__' in content:
                    return py_file
        elif project_type == "nodejs":
            pkg_json = code_dir / "package.json"
            if pkg_json.exists():
                import json
                try:
                    pkg = json.loads(pkg_json.read_text())
                    main = pkg.get("main", "index.js")
                    if (code_dir / main).exists():
                        return code_dir / main
                except Exception:
                    pass
            for name in ["index.js", "app.js", "main.js", "server.js"]:
                if (code_dir / name).exists():
                    return code_dir / name
        return None
    
    def _install_dependencies(self, code_dir: Path, project_type: str) -> tuple[bool, str]:
        """Install project dependencies."""
        if project_type == "python":
            req_file = code_dir / "requirements.txt"
            if req_file.exists():
                code, out, err = self._run_command(
                    "pip install -r requirements.txt --quiet", 
                    code_dir, 
                    timeout=120
                )
                return code == 0, f"{out}\n{err}".strip()
            return True, "No requirements.txt found"
        
        elif project_type == "nodejs":
            if (code_dir / "package.json").exists():
                code, out, err = self._run_command(
                    "npm install --silent",
                    code_dir,
                    timeout=120
                )
                return code == 0, f"{out}\n{err}".strip()
            return True, "No package.json found"
        
        return True, "No dependencies to install"
    
    def _run_tests(self, code_dir: Path, project_type: str) -> tuple[bool, str]:
        """Run project tests."""
        results = []
        
        if project_type == "python":
            # Try pytest first
            tests_dir = code_dir / "tests"
            if tests_dir.exists() or list(code_dir.glob("test_*.py")) or list(code_dir.glob("*_test.py")):
                code, out, err = self._run_command(
                    "python -m pytest -v --tb=short",
                    code_dir,
                    timeout=60
                )
                results.append(f"pytest (exit {code}):\n{out}\n{err}")
                if code == 0:
                    return True, "\n".join(results)
            
            # Try running main file with --help or similar
            main_file = self._find_main_file(code_dir, project_type)
            if main_file:
                code, out, err = self._run_command(
                    f"python {main_file.name} --help 2>/dev/null || python {main_file.name} -h 2>/dev/null || echo 'No help available'",
                    code_dir,
                    timeout=30
                )
                results.append(f"Main file check:\n{out}")
        
        elif project_type == "nodejs":
            pkg_json = code_dir / "package.json"
            if pkg_json.exists():
                import json
                try:
                    pkg = json.loads(pkg_json.read_text())
                    if "test" in pkg.get("scripts", {}):
                        code, out, err = self._run_command(
                            "npm test",
                            code_dir,
                            timeout=60
                        )
                        results.append(f"npm test (exit {code}):\n{out}\n{err}")
                        return code == 0, "\n".join(results)
                except Exception:
                    pass
        
        if not results:
            return True, "No tests found"
        
        return False, "\n".join(results)
    
    def _syntax_check(self, code_dir: Path, project_type: str) -> tuple[bool, str]:
        """Run syntax/lint checks."""
        if project_type == "python":
            # Check all Python files for syntax errors
            errors = []
            for py_file in code_dir.rglob("*.py"):
                code, out, err = self._run_command(
                    f"python -m py_compile {py_file.name}",
                    py_file.parent,
                    timeout=10
                )
                if code != 0:
                    errors.append(f"{py_file.name}: {err}")
            
            if errors:
                return False, "Syntax errors:\n" + "\n".join(errors)
            
            # Try ruff if available
            code, out, err = self._run_command(
                "python -m ruff check . --select=E,F --ignore=E501",
                code_dir,
                timeout=30
            )
            if code != 0 and "No module named ruff" not in err:
                return False, f"Ruff errors:\n{out}\n{err}"
            
            return True, "Syntax OK"
        
        elif project_type == "nodejs":
            # Check for obvious issues
            for js_file in code_dir.glob("*.js"):
                code, out, err = self._run_command(
                    f"node --check {js_file.name}",
                    code_dir,
                    timeout=10
                )
                if code != 0:
                    return False, f"Syntax error in {js_file.name}: {err}"
            return True, "Syntax OK"
        
        return True, "No syntax check available"
    
    def run(self, ctx: AgentContext) -> Path:
        """Run the TestRunner agent."""
        code_dir = ctx.artifacts_root / "code"
        out = ctx.artifacts_root / "runner-report.md"
        
        lines = ["# Test Runner Report", "", f"Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}", ""]
        
        # Check if code directory exists
        if not code_dir.exists():
            lines.append("## ❌ Error")
            lines.append("No code directory found. Dev agent may have failed.")
            return self._write(out, "\n".join(lines) + "\n")
        
        code_files = list(code_dir.rglob("*"))
        code_files = [f for f in code_files if f.is_file() and not f.name.startswith("_debug")]
        
        lines.append(f"## 📁 Code Directory: `{code_dir}`")
        lines.append(f"- Files found: {len(code_files)}")
        for f in code_files[:10]:
            try:
                rel = f.relative_to(code_dir)
                lines.append(f"  - `{rel}`")
            except ValueError:
                lines.append(f"  - `{f.name}`")
        if len(code_files) > 10:
            lines.append(f"  - ... and {len(code_files) - 10} more")
        lines.append("")
        
        # Detect project type
        project_type = self._detect_project_type(code_dir)
        lines.append(f"## 🔍 Project Type: `{project_type}`")
        lines.append("")
        
        # Find main file
        main_file = self._find_main_file(code_dir, project_type)
        if main_file:
            lines.append(f"## 📄 Main Entry Point: `{main_file.name}`")
        else:
            lines.append("## ⚠️ No main entry point detected")
        lines.append("")
        
        # Syntax check
        lines.append("## 🔧 Syntax Check")
        syntax_ok, syntax_msg = self._syntax_check(code_dir, project_type)
        lines.append(f"- Status: {'✅ PASS' if syntax_ok else '❌ FAIL'}")
        lines.append(f"```\n{syntax_msg}\n```")
        lines.append("")
        
        # Install dependencies
        lines.append("## 📦 Dependencies")
        deps_ok, deps_msg = self._install_dependencies(code_dir, project_type)
        lines.append(f"- Status: {'✅ PASS' if deps_ok else '❌ FAIL'}")
        if deps_msg:
            lines.append(f"```\n{deps_msg[:500]}\n```")
        lines.append("")
        
        # Run tests
        lines.append("## 🧪 Tests")
        tests_ok, tests_msg = self._run_tests(code_dir, project_type)
        lines.append(f"- Status: {'✅ PASS' if tests_ok else '❌ FAIL'}")
        lines.append(f"```\n{tests_msg[:1000]}\n```")
        lines.append("")
        
        # Overall verdict
        all_ok = syntax_ok and deps_ok and tests_ok
        lines.append("## 🏁 Verdict")
        lines.append(f"- Syntax: {'✅' if syntax_ok else '❌'}")
        lines.append(f"- Dependencies: {'✅' if deps_ok else '❌'}")
        lines.append(f"- Tests: {'✅' if tests_ok else '❌'}")
        lines.append("")
        lines.append(f"**Overall: {'✅ ALL CHECKS PASSED' if all_ok else '❌ SOME CHECKS FAILED'}**")
        
        if not all_ok:
            lines.append("")
            lines.append("### Recommended Actions:")
            if not syntax_ok:
                lines.append("- Fix syntax errors in the code")
            if not deps_ok:
                lines.append("- Check requirements.txt or package.json")
            if not tests_ok:
                lines.append("- Review and fix failing tests")
        
        return self._write(out, "\n".join(lines) + "\n")
