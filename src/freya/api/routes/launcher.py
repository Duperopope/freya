# src/freya/api/routes/launcher.py
"""
Freya Launcher API Routes v2.5.5

Provides endpoints for:
- One-click update from Git repository
- Frontend rebuild
- Backend restart
- Full bootstrap (update + build + restart)
- System status and logs
"""

from __future__ import annotations

import asyncio
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Request
from pydantic import BaseModel

logger = logging.getLogger("freya.launcher")

router = APIRouter()

# -----------------------------------------------------------------------------
# Global state for launcher operations
# -----------------------------------------------------------------------------
class LauncherState:
    """Track launcher operation status."""
    def __init__(self):
        self.is_updating = False
        self.is_building = False
        self.is_restarting = False
        self.last_update: datetime | None = None
        self.last_build: datetime | None = None
        self.logs: list[dict[str, Any]] = []
        self.current_operation: str | None = None
        self.progress: int = 0
        self.error: str | None = None
    
    def add_log(self, level: str, message: str):
        self.logs.append({
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message
        })
        # Keep only last 100 logs
        if len(self.logs) > 100:
            self.logs = self.logs[-100:]
        logger.log(getattr(logging, level.upper(), logging.INFO), message)
    
    def reset(self):
        self.is_updating = False
        self.is_building = False
        self.is_restarting = False
        self.current_operation = None
        self.progress = 0
        self.error = None

launcher_state = LauncherState()


# -----------------------------------------------------------------------------
# Request/Response Models
# -----------------------------------------------------------------------------
class LauncherStatus(BaseModel):
    is_updating: bool
    is_building: bool
    is_restarting: bool
    current_operation: str | None
    progress: int
    error: str | None
    last_update: str | None
    last_build: str | None
    git_info: dict[str, Any] | None = None
    system_info: dict[str, Any] | None = None


class LauncherResult(BaseModel):
    success: bool
    message: str
    details: dict[str, Any] | None = None


class GitInfo(BaseModel):
    branch: str
    commit: str
    remote_url: str
    has_updates: bool
    ahead: int
    behind: int


# -----------------------------------------------------------------------------
# Utility Functions
# -----------------------------------------------------------------------------
def get_project_root() -> Path:
    """Get the Freya project root directory."""
    # Navigate from src/freya/api/routes/ to project root
    return Path(__file__).parent.parent.parent.parent.parent


def get_npm_command() -> str:
    """Get the correct npm command for the current platform."""
    if sys.platform == "win32":
        # On Windows, try npm.cmd first, then npm
        for cmd in ["npm.cmd", "npm"]:
            try:
                result = subprocess.run([cmd, "--version"], capture_output=True, timeout=10)
                if result.returncode == 0:
                    return cmd
            except:
                pass
        return "npm.cmd"  # Default fallback
    return "npm"


def run_command(cmd: list[str], cwd: Path | None = None, timeout: int = 300) -> tuple[bool, str, str]:
    """Run a shell command and return (success, stdout, stderr)."""
    try:
        # On Windows, use shell=True for better PATH resolution
        use_shell = sys.platform == "win32"
        
        result = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=use_shell,
            env={**os.environ, "PYTHONUNBUFFERED": "1"}
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", f"Command timed out after {timeout}s"
    except FileNotFoundError as e:
        return False, "", f"Command not found: {cmd[0]}. Please ensure it is installed and in PATH."
    except Exception as e:
        return False, "", str(e)


async def run_command_async(cmd: list[str], cwd: Path | None = None, timeout: int = 300) -> tuple[bool, str, str]:
    """Run a shell command asynchronously."""
    return await asyncio.get_event_loop().run_in_executor(
        None, lambda: run_command(cmd, cwd, timeout)
    )


def get_git_info(project_root: Path) -> dict[str, Any]:
    """Get current Git repository information."""
    try:
        # Get current branch
        success, branch, _ = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=project_root)
        branch = branch.strip() if success else "unknown"
        
        # Get current commit
        success, commit, _ = run_command(["git", "rev-parse", "--short", "HEAD"], cwd=project_root)
        commit = commit.strip() if success else "unknown"
        
        # Get remote URL
        success, remote, _ = run_command(["git", "remote", "get-url", "origin"], cwd=project_root)
        remote = remote.strip() if success else "unknown"
        
        # Fetch to check for updates (silent)
        run_command(["git", "fetch", "--quiet"], cwd=project_root)
        
        # Check ahead/behind
        success, status, _ = run_command(
            ["git", "rev-list", "--left-right", "--count", f"HEAD...origin/{branch}"],
            cwd=project_root
        )
        ahead, behind = 0, 0
        if success and status.strip():
            parts = status.strip().split()
            if len(parts) == 2:
                ahead, behind = int(parts[0]), int(parts[1])
        
        # Get last commit message
        success, last_msg, _ = run_command(
            ["git", "log", "-1", "--pretty=%s"],
            cwd=project_root
        )
        last_message = last_msg.strip() if success else ""
        
        # Get last commit date
        success, last_date, _ = run_command(
            ["git", "log", "-1", "--pretty=%ci"],
            cwd=project_root
        )
        last_commit_date = last_date.strip() if success else ""
        
        return {
            "branch": branch,
            "commit": commit,
            "remote_url": remote,
            "has_updates": behind > 0,
            "ahead": ahead,
            "behind": behind,
            "last_message": last_message,
            "last_commit_date": last_commit_date
        }
    except Exception as e:
        logger.error(f"Error getting git info: {e}")
        return {
            "branch": "unknown",
            "commit": "unknown",
            "remote_url": "unknown",
            "has_updates": False,
            "ahead": 0,
            "behind": 0,
            "error": str(e)
        }


def get_system_info() -> dict[str, Any]:
    """Get system information for the launcher."""
    project_root = get_project_root()
    web_dir = project_root / "web"
    web_dist = web_dir / "dist"
    
    # Check Node.js
    success, node_version, _ = run_command(["node", "--version"])
    node_ok = success
    node_ver = node_version.strip() if success else "Not found"
    
    # Check npm (handle Windows npm.cmd)
    npm_cmd = get_npm_command()
    success, npm_version, _ = run_command([npm_cmd, "--version"])
    npm_ok = success
    npm_ver = npm_version.strip() if success else "Not found"
    
    # Check Python
    python_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    # Check if web UI is built
    web_built = web_dist.exists() and (web_dist / "index.html").exists()
    
    # Check if node_modules exists
    node_modules_ok = (web_dir / "node_modules").exists()
    
    return {
        "project_root": str(project_root),
        "python_version": python_ver,
        "node_version": node_ver,
        "node_ok": node_ok,
        "npm_version": npm_ver,
        "npm_ok": npm_ok,
        "web_built": web_built,
        "node_modules_installed": node_modules_ok,
        "platform": sys.platform
    }


# -----------------------------------------------------------------------------
# Background Tasks
# -----------------------------------------------------------------------------
async def do_git_update(project_root: Path):
    """Perform Git pull update."""
    global launcher_state
    launcher_state.is_updating = True
    launcher_state.current_operation = "Updating from Git..."
    launcher_state.progress = 10
    
    try:
        launcher_state.add_log("info", "Starting Git update...")
        
        # Stash any local changes
        launcher_state.add_log("info", "Stashing local changes...")
        launcher_state.progress = 20
        run_command(["git", "stash"], cwd=project_root)
        
        # Pull latest changes
        launcher_state.add_log("info", "Pulling latest changes...")
        launcher_state.progress = 40
        success, stdout, stderr = await run_command_async(
            ["git", "pull", "--rebase", "origin", "main"],
            cwd=project_root,
            timeout=120
        )
        
        if not success:
            # Try without rebase
            launcher_state.add_log("warning", "Rebase failed, trying merge...")
            success, stdout, stderr = await run_command_async(
                ["git", "pull", "origin", "main"],
                cwd=project_root,
                timeout=120
            )
        
        launcher_state.progress = 80
        
        if success:
            launcher_state.add_log("info", f"Git update successful: {stdout.strip()}")
            launcher_state.last_update = datetime.now()
            launcher_state.progress = 100
        else:
            launcher_state.add_log("error", f"Git update failed: {stderr}")
            launcher_state.error = f"Git pull failed: {stderr[:200]}"
        
        # Pop stash
        run_command(["git", "stash", "pop"], cwd=project_root)
        
    except Exception as e:
        launcher_state.add_log("error", f"Update error: {e}")
        launcher_state.error = str(e)
    finally:
        launcher_state.is_updating = False
        launcher_state.current_operation = None


async def do_npm_install(project_root: Path):
    """Install npm dependencies."""
    global launcher_state
    web_dir = project_root / "web"
    npm_cmd = get_npm_command()
    
    launcher_state.current_operation = "Installing npm dependencies..."
    launcher_state.progress = 10
    launcher_state.add_log("info", f"Running {npm_cmd} install...")
    
    success, stdout, stderr = await run_command_async(
        [npm_cmd, "install"],
        cwd=web_dir,
        timeout=300
    )
    
    if success:
        launcher_state.add_log("info", "npm install completed")
        launcher_state.progress = 50
    else:
        launcher_state.add_log("error", f"npm install failed: {stderr}")
        launcher_state.error = f"npm install failed: {stderr[:200]}"
        raise Exception("npm install failed")


async def do_build_frontend(project_root: Path):
    """Build the frontend."""
    global launcher_state
    launcher_state.is_building = True
    launcher_state.current_operation = "Building frontend..."
    launcher_state.progress = 60
    
    web_dir = project_root / "web"
    
    try:
        launcher_state.add_log("info", "Starting frontend build...")
        
        # Check if node_modules exists
        if not (web_dir / "node_modules").exists():
            await do_npm_install(project_root)
        
        launcher_state.progress = 70
        npm_cmd = get_npm_command()
        launcher_state.add_log("info", f"Running {npm_cmd} run build...")
        
        success, stdout, stderr = await run_command_async(
            [npm_cmd, "run", "build"],
            cwd=web_dir,
            timeout=300
        )
        
        launcher_state.progress = 95
        
        if success:
            launcher_state.add_log("info", "Frontend build completed successfully")
            launcher_state.last_build = datetime.now()
            launcher_state.progress = 100
        else:
            launcher_state.add_log("error", f"Build failed: {stderr}")
            launcher_state.error = f"Build failed: {stderr[:200]}"
            
    except Exception as e:
        launcher_state.add_log("error", f"Build error: {e}")
        launcher_state.error = str(e)
    finally:
        launcher_state.is_building = False
        launcher_state.current_operation = None


async def do_full_bootstrap(project_root: Path, skip_npm: bool = False):
    """Perform full bootstrap: update + install deps + build."""
    global launcher_state
    
    try:
        # Step 1: Git update
        await do_git_update(project_root)
        if launcher_state.error:
            return
        
        # Step 2: Python deps
        launcher_state.current_operation = "Installing Python dependencies..."
        launcher_state.progress = 20
        launcher_state.add_log("info", "Installing Python dependencies...")
        
        success, _, stderr = await run_command_async(
            [sys.executable, "-m", "pip", "install", "-e", ".", "--quiet"],
            cwd=project_root,
            timeout=180
        )
        
        if not success:
            launcher_state.add_log("warning", f"pip install warning: {stderr[:100]}")
        else:
            launcher_state.add_log("info", "Python dependencies installed")
        
        launcher_state.progress = 40
        
        # Check if we should skip npm (frontend already built)
        web_dir = project_root / "web"
        web_dist = web_dir / "dist"
        frontend_exists = web_dist.exists() and (web_dist / "index.html").exists()
        
        if skip_npm and frontend_exists:
            launcher_state.add_log("info", "Skipping npm (frontend already built)")
            launcher_state.progress = 100
            launcher_state.last_update = datetime.now()
            return
        
        # Step 3: npm install
        npm_cmd = get_npm_command()
        launcher_state.current_operation = "Installing npm dependencies..."
        launcher_state.add_log("info", f"Installing npm dependencies ({npm_cmd})...")
        
        success, _, stderr = await run_command_async(
            [npm_cmd, "install"],
            cwd=web_dir,
            timeout=300
        )
        
        if success:
            launcher_state.add_log("info", "npm dependencies installed")
        else:
            # Check if frontend is already built - if so, just warn but don't fail
            if frontend_exists:
                launcher_state.add_log("warning", f"npm install failed but frontend exists: {stderr[:100]}")
                launcher_state.progress = 100
                launcher_state.last_update = datetime.now()
                return
            else:
                launcher_state.add_log("error", f"npm install failed: {stderr[:100]}")
                launcher_state.error = "npm install failed - frontend not built"
                return
        
        launcher_state.progress = 60
        
        # Step 4: Build frontend
        await do_build_frontend(project_root)
        
    except Exception as e:
        launcher_state.add_log("error", f"Bootstrap error: {e}")
        launcher_state.error = str(e)


# -----------------------------------------------------------------------------
# API Endpoints
# -----------------------------------------------------------------------------
@router.get("/status", response_model=LauncherStatus)
async def get_launcher_status():
    """Get current launcher status and system information."""
    project_root = get_project_root()
    
    return LauncherStatus(
        is_updating=launcher_state.is_updating,
        is_building=launcher_state.is_building,
        is_restarting=launcher_state.is_restarting,
        current_operation=launcher_state.current_operation,
        progress=launcher_state.progress,
        error=launcher_state.error,
        last_update=launcher_state.last_update.isoformat() if launcher_state.last_update else None,
        last_build=launcher_state.last_build.isoformat() if launcher_state.last_build else None,
        git_info=get_git_info(project_root),
        system_info=get_system_info()
    )


@router.get("/logs")
async def get_launcher_logs(limit: int = 50):
    """Get recent launcher logs."""
    return {
        "logs": launcher_state.logs[-limit:],
        "total": len(launcher_state.logs)
    }


@router.post("/check-updates", response_model=LauncherResult)
async def check_for_updates():
    """Check if updates are available from Git."""
    project_root = get_project_root()
    
    # Fetch latest
    launcher_state.add_log("info", "Checking for updates...")
    success, _, _ = await run_command_async(
        ["git", "fetch", "--quiet"],
        cwd=project_root,
        timeout=60
    )
    
    if not success:
        return LauncherResult(
            success=False,
            message="Failed to fetch from remote",
            details=None
        )
    
    git_info = get_git_info(project_root)
    
    if git_info.get("has_updates"):
        return LauncherResult(
            success=True,
            message=f"{git_info['behind']} update(s) available",
            details=git_info
        )
    else:
        return LauncherResult(
            success=True,
            message="Already up to date",
            details=git_info
        )


@router.post("/update", response_model=LauncherResult)
async def trigger_update(background_tasks: BackgroundTasks):
    """Trigger a Git update (pull latest changes)."""
    if launcher_state.is_updating or launcher_state.is_building:
        return LauncherResult(
            success=False,
            message="Another operation is in progress",
            details={"current_operation": launcher_state.current_operation}
        )
    
    launcher_state.reset()
    project_root = get_project_root()
    
    background_tasks.add_task(do_git_update, project_root)
    
    return LauncherResult(
        success=True,
        message="Update started",
        details={"status": "in_progress"}
    )


@router.post("/build", response_model=LauncherResult)
async def trigger_build(background_tasks: BackgroundTasks):
    """Trigger a frontend rebuild."""
    if launcher_state.is_updating or launcher_state.is_building:
        return LauncherResult(
            success=False,
            message="Another operation is in progress",
            details={"current_operation": launcher_state.current_operation}
        )
    
    launcher_state.reset()
    project_root = get_project_root()
    
    background_tasks.add_task(do_build_frontend, project_root)
    
    return LauncherResult(
        success=True,
        message="Build started",
        details={"status": "in_progress"}
    )


@router.post("/update-only", response_model=LauncherResult)
async def trigger_update_only(background_tasks: BackgroundTasks):
    """Trigger update without npm rebuild (Git pull + pip only)."""
    if launcher_state.is_updating or launcher_state.is_building:
        return LauncherResult(
            success=False,
            message="Another operation is in progress",
            details={"current_operation": launcher_state.current_operation}
        )
    
    launcher_state.reset()
    project_root = get_project_root()
    
    # Use bootstrap with skip_npm=True
    background_tasks.add_task(do_full_bootstrap, project_root, True)
    
    return LauncherResult(
        success=True,
        message="Update started (skip npm)",
        details={"status": "in_progress", "skip_npm": True}
    )


@router.post("/bootstrap", response_model=LauncherResult)
async def trigger_bootstrap(background_tasks: BackgroundTasks):
    """Trigger full bootstrap: update + install dependencies + build."""
    if launcher_state.is_updating or launcher_state.is_building:
        return LauncherResult(
            success=False,
            message="Another operation is in progress",
            details={"current_operation": launcher_state.current_operation}
        )
    
    launcher_state.reset()
    project_root = get_project_root()
    
    background_tasks.add_task(do_full_bootstrap, project_root)
    
    return LauncherResult(
        success=True,
        message="Bootstrap started (update + build)",
        details={"status": "in_progress"}
    )


@router.post("/clear-error", response_model=LauncherResult)
async def clear_error():
    """Clear any error state."""
    launcher_state.error = None
    return LauncherResult(
        success=True,
        message="Error cleared",
        details=None
    )


@router.post("/clear-logs", response_model=LauncherResult)
async def clear_logs():
    """Clear launcher logs."""
    launcher_state.logs = []
    return LauncherResult(
        success=True,
        message="Logs cleared",
        details=None
    )
