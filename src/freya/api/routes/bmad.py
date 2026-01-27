# src/freya/api/routes/bmad.py
"""
BMAD Workflow API Routes

Endpoints for BMAD (Business Model - Architecture - Development) orchestration:
- Run full BMAD cycle
- Run individual agents
- Get artifacts
- Autopilot mode
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel, Field

from ..websocket import ChannelType, WSMessage

router = APIRouter()
logger = logging.getLogger("freya.api.bmad")


# -----------------------------------------------------------------------------
# Request/Response Models
# -----------------------------------------------------------------------------
class BMADRunRequest(BaseModel):
    """Request to run BMAD workflow."""
    goal: str = Field(..., description="Project goal in natural language")
    project_name: str = Field(default="FreyaProject", description="Project name")
    output_dir: str | None = Field(default=None, description="Custom output directory")


class AgentRunRequest(BaseModel):
    """Request to run a single agent."""
    goal: str = Field(..., description="Project goal")
    agent: str = Field(..., description="Agent name: analyst, pm, architect, po, sm, dev, qa")


class BMADStatus(BaseModel):
    """BMAD workflow status."""
    running: bool
    current_agent: str | None
    agents_completed: list[str]
    artifacts_generated: list[str]
    error: str | None = None


class ArtifactInfo(BaseModel):
    """Information about a generated artifact."""
    name: str
    path: str
    size_bytes: int
    modified_at: str


class AutopilotRequest(BaseModel):
    """Request for autopilot mode."""
    goal: str = Field(..., description="Project goal")
    project_name: str = Field(default="FreyaApp")
    max_fix_iters: int = Field(default=3, ge=1, le=10)
    open_vscode: bool = Field(default=False)  # Disabled for web


# -----------------------------------------------------------------------------
# Global BMAD State
# -----------------------------------------------------------------------------
class BMADRuntime:
    """Thread-safe BMAD runtime state with persistence and detailed logging."""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._running = False
        self._current_agent: str | None = None
        self._completed: list[str] = []
        self._artifacts: list[str] = []
        self._error: str | None = None
        self._logs: list[dict[str, Any]] = []  # Detailed execution logs
        self._project_name: str = ""
        self._goal: str = ""
        self._started_at: str | None = None
    
    @property
    def status(self) -> dict[str, Any]:
        with self._lock:
            return {
                "running": self._running,
                "current_agent": self._current_agent,
                "agents_completed": list(self._completed),
                "artifacts_generated": list(self._artifacts),
                "error": self._error,
                "logs": list(self._logs[-50:]),  # Last 50 logs
                "project_name": self._project_name,
                "goal": self._goal,
                "started_at": self._started_at,
            }
    
    def start(self, project_name: str = "", goal: str = "") -> bool:
        with self._lock:
            if self._running:
                return False
            self._running = True
            self._current_agent = None
            self._completed = []
            self._artifacts = []
            self._error = None
            self._logs = []
            self._project_name = project_name
            self._goal = goal
            self._started_at = time.strftime("%Y-%m-%d %H:%M:%S")
            return True
    
    def set_agent(self, agent: str) -> None:
        with self._lock:
            self._current_agent = agent
    
    def add_log(self, level: str, message: str, agent: str | None = None, details: dict | None = None) -> None:
        """Add a detailed log entry."""
        with self._lock:
            self._logs.append({
                "timestamp": time.strftime("%H:%M:%S"),
                "level": level,
                "agent": agent or self._current_agent,
                "message": message,
                "details": details or {}
            })
    
    def complete_agent(self, agent: str, artifact: str | None = None) -> None:
        with self._lock:
            self._completed.append(agent)
            if artifact:
                self._artifacts.append(artifact)
    
    def set_error(self, error: str) -> None:
        with self._lock:
            self._error = error
    
    def finish(self) -> None:
        with self._lock:
            self._running = False
            self._current_agent = None
    
    def get_state_for_persistence(self) -> dict[str, Any]:
        """Get state dict for saving to file."""
        with self._lock:
            return {
                "project_name": self._project_name,
                "goal": self._goal,
                "completed_agents": list(self._completed),
                "artifacts": list(self._artifacts),
                "error": self._error,
                "started_at": self._started_at,
                "saved_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
    
    def load_state(self, state: dict[str, Any]) -> None:
        """Load state from persistence."""
        with self._lock:
            self._project_name = state.get("project_name", "")
            self._goal = state.get("goal", "")
            self._completed = state.get("completed_agents", [])
            self._artifacts = state.get("artifacts", [])
            self._error = state.get("error")


_bmad_runtime = BMADRuntime()


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------
@router.get("/status")
async def get_bmad_status() -> dict[str, Any]:
    """Get current BMAD workflow status with logs."""
    return _bmad_runtime.status


@router.get("/logs")
async def get_bmad_logs() -> dict[str, Any]:
    """Get detailed execution logs."""
    status = _bmad_runtime.status
    return {
        "logs": status.get("logs", []),
        "project_name": status.get("project_name"),
        "running": status.get("running"),
        "current_agent": status.get("current_agent"),
    }


@router.post("/resume")
async def resume_bmad_project(
    request: Request,
    project_name: str,
    background_tasks: BackgroundTasks
) -> dict[str, Any]:
    """Resume a BMAD project from where it stopped."""
    state = request.app.state.freya
    
    if not state.ready:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    # Find project state file
    output_dir = state.config.output_root / project_name
    state_file = output_dir / ".bmad_state.json"
    
    if not state_file.exists():
        raise HTTPException(status_code=404, detail=f"No saved state found for project '{project_name}'")
    
    try:
        saved_state = json.loads(state_file.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load state: {e}")
    
    completed_agents = saved_state.get("completed_agents", [])
    goal = saved_state.get("goal", "")
    
    return {
        "project_name": project_name,
        "goal": goal,
        "completed_agents": completed_agents,
        "can_resume": True,
        "next_agent": _get_next_agent(completed_agents),
        "message": f"Project '{project_name}' can be resumed. Use /run with same goal to continue."
    }


def _get_next_agent(completed: list[str]) -> str | None:
    """Get the next agent to run based on completed list."""
    all_agents = ["analyst", "pm", "architect", "po", "sm", "dev", "qa"]
    for agent in all_agents:
        if agent not in completed:
            return agent
    return None


@router.post("/run")
async def run_bmad_workflow(
    request: Request,
    body: BMADRunRequest,
    background_tasks: BackgroundTasks
) -> dict[str, Any]:
    """
    Run full BMAD workflow with detailed logging and code generation.
    
    Executes all agents in sequence:
    Analyst -> PM -> Architect -> PO -> SM -> Dev -> QA
    
    Dev agent creates actual code files. QA runs tests.
    Progress is streamed via WebSocket (channel: bmad).
    """
    state = request.app.state.freya
    
    if not state.ready:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    if not _bmad_runtime.start(project_name=body.project_name, goal=body.goal):
        raise HTTPException(status_code=409, detail="BMAD workflow already running")
    
    # Determine output directory
    if body.output_dir:
        output_dir = Path(body.output_dir)
    else:
        output_dir = state.config.output_root / body.project_name
    
    def run_workflow():
        """Background BMAD runner with detailed logging."""
        ws_manager = state.ws_manager
        
        def broadcast(event: str, data: dict[str, Any]) -> None:
            if ws_manager:
                ws_manager.broadcast_sync(WSMessage(
                    channel=ChannelType.BMAD,
                    event=event,
                    data={**data, "logs": _bmad_runtime.status.get("logs", [])}
                ))
        
        def log_and_broadcast(level: str, message: str, agent: str | None = None, details: dict | None = None):
            """Log message and broadcast to frontend."""
            _bmad_runtime.add_log(level, message, agent, details)
            broadcast("log", {
                "level": level,
                "message": message,
                "agent": agent or _bmad_runtime.status.get("current_agent"),
                "details": details or {}
            })
            logger.info(f"[BMAD/{agent or 'system'}] {message}")
        
        try:
            log_and_broadcast("info", f"🚀 Pipeline BMAD démarré pour '{body.project_name}'")
            log_and_broadcast("info", f"📋 Objectif: {body.goal[:200]}...")
            broadcast("started", {"goal": body.goal, "project_name": body.project_name})
            
            # Initialize directories
            output_dir.mkdir(parents=True, exist_ok=True)
            code_dir = output_dir / "code"
            code_dir.mkdir(parents=True, exist_ok=True)
            
            log_and_broadcast("info", f"📁 Dossier de sortie: {output_dir}")
            
            # Save pipeline state for resume capability
            state_file = output_dir / ".bmad_state.json"
            
            # Check if we should resume from a previous run
            already_completed: list[str] = []
            if state_file.exists():
                try:
                    saved_state = json.loads(state_file.read_text(encoding="utf-8"))
                    already_completed = saved_state.get("completed_agents", [])
                    if already_completed:
                        log_and_broadcast("info", f"🔄 Reprise du projet - {len(already_completed)} agents déjà complétés")
                        log_and_broadcast("info", f"✓ Agents complétés: {', '.join(already_completed)}")
                except Exception as e:
                    logger.warning(f"Failed to load previous state: {e}")
                    already_completed = []
            
            # Agent execution sequence with descriptions
            agents = [
                ("analyst", "📊 Analyste", "Crée le brief projet"),
                ("pm", "📋 Product Manager", "Rédige le PRD (Product Requirements Document)"),
                ("architect", "🏗️ Architecte", "Conçoit l'architecture technique"),
                ("po", "🎯 Product Owner", "Découpe en epics"),
                ("sm", "📝 Scrum Master", "Crée les user stories"),
                ("dev", "💻 Développeur", "Génère le code"),
                ("qa", "🔍 QA Engineer", "Teste et valide"),
                ("runner", "🚀 Test Runner", "Lance et valide l'application"),
            ]
            
            max_fix_cycles = 3  # Maximum Dev→QA→Runner cycles
            current_cycle = 0
            
            for idx, (agent_name, agent_label, agent_desc) in enumerate(agents):
                # Skip already completed agents (resume mode)
                if agent_name in already_completed:
                    log_and_broadcast("info", f"⏭️ {agent_label} déjà complété, on passe au suivant", agent_name)
                    _bmad_runtime.complete_agent(agent_name)
                    continue
                _bmad_runtime.set_agent(agent_name)
                log_and_broadcast("info", f"▶️ {agent_label} - {agent_desc}", agent_name)
                broadcast("agent_start", {"agent": agent_name, "progress": (idx / len(agents)) * 100})
                
                start_time = time.time()
                
                try:
                    # Run agent
                    artifact_path = _run_single_agent(state, agent_name, body.goal, output_dir)
                    
                    elapsed = time.time() - start_time
                    
                    # Log artifact details
                    if artifact_path.exists():
                        content = artifact_path.read_text(encoding="utf-8")
                        preview = content[:500] + "..." if len(content) > 500 else content
                        log_and_broadcast(
                            "success", 
                            f"✅ {agent_label} terminé en {elapsed:.1f}s",
                            agent_name,
                            {"artifact": str(artifact_path.name), "preview": preview, "size": len(content)}
                        )
                        
                        # Check if Runner agent detected failures - trigger fix cycle
                        if agent_name == "runner" and current_cycle < max_fix_cycles:
                            if "❌" in content or "FAIL" in content:
                                current_cycle += 1
                                log_and_broadcast(
                                    "info",
                                    f"🔄 Cycle de correction {current_cycle}/{max_fix_cycles} - Des erreurs ont été détectées",
                                    "system"
                                )
                                
                                # Re-run Dev with fix instructions
                                fix_goal = f"""
FIX THE FOLLOWING ISSUES from the test runner report:

{content[:2000]}

Original goal: {body.goal}

Fix the code to make all tests pass.
"""
                                log_and_broadcast("info", "🔧 Relance du Développeur pour corriger les erreurs", "dev")
                                _run_single_agent(state, "dev", fix_goal, output_dir)
                                
                                log_and_broadcast("info", "🔍 Relance du QA pour vérifier les corrections", "qa")
                                _run_single_agent(state, "qa", body.goal, output_dir)
                                
                                log_and_broadcast("info", "🚀 Relance du Runner pour valider", "runner")
                                artifact_path = _run_single_agent(state, "runner", body.goal, output_dir)
                                
                                # Check again
                                content = artifact_path.read_text(encoding="utf-8")
                                if "✅ ALL CHECKS PASSED" in content:
                                    log_and_broadcast("success", f"🎉 Toutes les vérifications passent après {current_cycle} cycle(s) de correction!", "system")
                    else:
                        log_and_broadcast("success", f"✅ {agent_label} terminé en {elapsed:.1f}s", agent_name)
                    
                    _bmad_runtime.complete_agent(agent_name, str(artifact_path))
                    broadcast("agent_done", {
                        "agent": agent_name,
                        "artifact": str(artifact_path),
                        "elapsed_seconds": elapsed
                    })
                    
                    # Save state for resume
                    state_file.write_text(json.dumps(_bmad_runtime.get_state_for_persistence(), indent=2))
                    
                except Exception as e:
                    elapsed = time.time() - start_time
                    error_msg = f"{agent_name}: {str(e)}"
                    logger.error(f"Agent {agent_name} failed: {e}", exc_info=True)
                    
                    log_and_broadcast(
                        "error", 
                        f"❌ {agent_label} a échoué après {elapsed:.1f}s: {str(e)[:200]}",
                        agent_name,
                        {"error": str(e), "traceback": str(e.__traceback__) if e.__traceback__ else None}
                    )
                    
                    _bmad_runtime.set_error(error_msg)
                    broadcast("agent_error", {"agent": agent_name, "error": str(e)})
                    
                    # Save state even on error
                    state_file.write_text(json.dumps(_bmad_runtime.get_state_for_persistence(), indent=2))
                    # Continue with next agent (continuous mode)
            
            # Final summary
            completed = _bmad_runtime.status["agents_completed"]
            artifacts = _bmad_runtime.status["artifacts_generated"]
            
            log_and_broadcast("info", f"🏁 Pipeline terminé: {len(completed)}/{len(agents)} agents complétés")
            log_and_broadcast("info", f"📦 Artifacts générés: {len(artifacts)}")
            if current_cycle > 0:
                log_and_broadcast("info", f"🔄 Cycles de correction effectués: {current_cycle}")
            
            # List generated files
            all_files = list(output_dir.rglob("*"))
            file_list = [str(f.relative_to(output_dir)) for f in all_files if f.is_file()]
            log_and_broadcast("info", f"📂 Fichiers créés: {len(file_list)}", details={"files": file_list[:20]})
            
            broadcast("complete", {
                "status": "success" if len(completed) == len(agents) else "partial",
                "artifacts": artifacts,
                "files_created": file_list
            })
        
        except Exception as e:
            logger.error(f"BMAD workflow failed: {e}", exc_info=True)
            log_and_broadcast("error", f"💥 Pipeline échoué: {str(e)}")
            _bmad_runtime.set_error(str(e))
            broadcast("error", {"error": str(e)})
        
        finally:
            _bmad_runtime.finish()
    
    thread = threading.Thread(target=run_workflow, daemon=True)
    thread.start()
    
    return {
        "started": True,
        "goal": body.goal,
        "project_name": body.project_name,
        "output_dir": str(output_dir),
        "message": "BMAD workflow started. Watch WebSocket channel 'bmad' for progress."
    }


@router.post("/agent")
async def run_single_agent_endpoint(
    request: Request,
    body: AgentRunRequest
) -> dict[str, Any]:
    """
    Run a single BMAD agent.
    
    Valid agents: analyst, pm, architect, po, sm, dev, qa
    """
    state = request.app.state.freya
    
    if not state.ready:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    valid_agents = ["analyst", "pm", "architect", "po", "sm", "dev", "qa"]
    if body.agent not in valid_agents:
        raise HTTPException(status_code=400, detail=f"Invalid agent. Must be one of: {valid_agents}")
    
    try:
        output_dir = state.config.output_root / "single_agent_runs"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        artifact_path = _run_single_agent(state, body.agent, body.goal, output_dir)
        
        return {
            "success": True,
            "agent": body.agent,
            "artifact": str(artifact_path),
            "content_preview": artifact_path.read_text(encoding="utf-8")[:2000] if artifact_path.exists() else None
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent failed: {e}")


@router.get("/artifacts", response_model=list[ArtifactInfo])
async def list_artifacts(request: Request, project: str | None = None) -> list[ArtifactInfo]:
    """List generated artifacts."""
    state = request.app.state.freya
    
    if project:
        search_dir = state.config.output_root / project
    else:
        search_dir = state.config.output_root
    
    if not search_dir.exists():
        return []
    
    artifacts = []
    for path in search_dir.rglob("*.md"):
        try:
            stat = path.stat()
            artifacts.append(ArtifactInfo(
                name=path.name,
                path=str(path.relative_to(state.config.output_root)),
                size_bytes=stat.st_size,
                modified_at=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime))
            ))
        except Exception:
            continue
    
    return sorted(artifacts, key=lambda x: x.modified_at, reverse=True)


@router.get("/artifact")
async def get_artifact(request: Request, path: str) -> dict[str, Any]:
    """Get artifact content."""
    state = request.app.state.freya
    
    full_path = state.config.output_root / path
    
    # Security check
    try:
        full_path = full_path.resolve()
        output_root = state.config.output_root.resolve()
        if output_root not in full_path.parents and full_path != output_root:
            raise HTTPException(status_code=403, detail="Access denied")
    except Exception:
        raise HTTPException(status_code=403, detail="Invalid path")
    
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    try:
        content = full_path.read_text(encoding="utf-8")
        return {
            "name": full_path.name,
            "path": path,
            "content": content,
            "size_bytes": len(content.encode("utf-8"))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read artifact: {e}")


@router.post("/autopilot")
async def run_autopilot(
    request: Request,
    body: AutopilotRequest,
    background_tasks: BackgroundTasks
) -> dict[str, Any]:
    """
    Run autopilot mode (scaffold + tests + validation).
    
    This creates a complete project with:
    - SPEC.md
    - FastAPI app
    - Tests
    - README
    """
    state = request.app.state.freya
    
    if not state.ready:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    from ...autopilot import AutopilotConfig, FreyaAutopilot
    
    output_dir = state.config.output_root / body.project_name
    
    def run_autopilot_bg():
        ws_manager = state.ws_manager
        
        try:
            if ws_manager:
                ws_manager.broadcast_sync(WSMessage(
                    channel=ChannelType.BMAD,
                    event="autopilot_started",
                    data={"goal": body.goal, "project_name": body.project_name}
                ))
            
            config = AutopilotConfig(
                goal=body.goal,
                output_dir=str(output_dir),
                project_name=body.project_name,
                max_fix_iters=body.max_fix_iters,
                open_vscode=False  # Don't open VS Code from web
            )
            
            pilot = FreyaAutopilot(config)
            pilot.run()
            
            if ws_manager:
                ws_manager.broadcast_sync(WSMessage(
                    channel=ChannelType.BMAD,
                    event="autopilot_complete",
                    data={"status": "success", "output_dir": str(output_dir)}
                ))
        
        except Exception as e:
            logger.error(f"Autopilot failed: {e}")
            if ws_manager:
                ws_manager.broadcast_sync(WSMessage(
                    channel=ChannelType.BMAD,
                    event="autopilot_error",
                    data={"error": str(e)}
                ))
    
    background_tasks.add_task(run_autopilot_bg)
    
    return {
        "started": True,
        "goal": body.goal,
        "project_name": body.project_name,
        "output_dir": str(output_dir)
    }


# -----------------------------------------------------------------------------
# Autonomy Mode v2.4 - Self-Healing Pipeline
# -----------------------------------------------------------------------------
class AutonomyModeRequest(BaseModel):
    """Request for full autonomy mode after Analyst validation."""
    goal: str = Field(..., description="Project goal (validated by Analyst)")
    project_name: str = Field(default="FreyaApp")
    analyst_brief: str = Field(..., description="Validated Analyst brief")
    max_retries: int = Field(default=3, ge=1, le=10, description="Max retries per agent on failure")
    max_qa_cycles: int = Field(default=5, ge=1, le=20, description="Max QA->Dev fix cycles")
    enable_safeguards: bool = Field(default=True, description="Enable security safeguards")
    notification_email: str | None = Field(default=None, description="Email for completion notification")


class AutonomyStatus(BaseModel):
    """Autonomy mode status."""
    running: bool
    phase: str  # 'pm' | 'architect' | 'po' | 'sm' | 'dev' | 'qa' | 'fixing' | 'complete' | 'failed'
    current_agent: str | None
    agents_completed: list[str]
    qa_cycles: int
    artifacts_generated: list[str]
    errors: list[dict]
    started_at: str | None
    estimated_completion: str | None


class AutonomyRuntime:
    """Autonomy mode runtime with self-healing."""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._running = False
        self._phase = "idle"
        self._current_agent: str | None = None
        self._completed: list[str] = []
        self._qa_cycles = 0
        self._artifacts: list[str] = []
        self._errors: list[dict] = []
        self._started_at: str | None = None
        self._stop_requested = False
    
    @property
    def status(self) -> dict[str, Any]:
        with self._lock:
            return {
                "running": self._running,
                "phase": self._phase,
                "current_agent": self._current_agent,
                "agents_completed": list(self._completed),
                "qa_cycles": self._qa_cycles,
                "artifacts_generated": list(self._artifacts),
                "errors": list(self._errors),
                "started_at": self._started_at,
                "estimated_completion": None  # TODO: calculate based on history
            }
    
    def start(self) -> bool:
        with self._lock:
            if self._running:
                return False
            self._running = True
            self._phase = "starting"
            self._current_agent = None
            self._completed = []
            self._qa_cycles = 0
            self._artifacts = []
            self._errors = []
            self._started_at = time.strftime("%Y-%m-%d %H:%M:%S")
            self._stop_requested = False
            return True
    
    def set_phase(self, phase: str, agent: str | None = None) -> None:
        with self._lock:
            self._phase = phase
            self._current_agent = agent
    
    def complete_agent(self, agent: str, artifact: str | None = None) -> None:
        with self._lock:
            if agent not in self._completed:
                self._completed.append(agent)
            if artifact and artifact not in self._artifacts:
                self._artifacts.append(artifact)
    
    def add_error(self, agent: str, error: str, retry_count: int) -> None:
        with self._lock:
            self._errors.append({
                "agent": agent,
                "error": error,
                "retry": retry_count,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            })
    
    def increment_qa_cycle(self) -> None:
        with self._lock:
            self._qa_cycles += 1
    
    def request_stop(self) -> None:
        with self._lock:
            self._stop_requested = True
    
    def should_stop(self) -> bool:
        with self._lock:
            return self._stop_requested
    
    def finish(self, success: bool = True) -> None:
        with self._lock:
            self._running = False
            self._phase = "complete" if success else "failed"
            self._current_agent = None


_autonomy_runtime = AutonomyRuntime()


@router.get("/autonomy/status", response_model=AutonomyStatus)
async def get_autonomy_status() -> AutonomyStatus:
    """Get autonomy mode status."""
    return AutonomyStatus(**_autonomy_runtime.status)


@router.post("/autonomy/stop")
async def stop_autonomy() -> dict[str, Any]:
    """Request graceful stop of autonomy mode."""
    _autonomy_runtime.request_stop()
    return {"message": "Stop requested. Pipeline will finish current agent then stop."}


@router.post("/autonomy/start")
async def start_autonomy_mode(
    request: Request,
    body: AutonomyModeRequest,
    background_tasks: BackgroundTasks
) -> dict[str, Any]:
    """
    Start full autonomy mode after Analyst validation.
    
    This runs the complete BMAD pipeline (PM -> Architect -> PO -> SM -> Dev -> QA)
    with self-healing loops:
    - If an agent fails, retry up to max_retries times
    - If QA finds issues, send back to Dev for fixes (up to max_qa_cycles)
    - Progress is streamed via WebSocket
    - Optional email notification on completion
    """
    state = request.app.state.freya
    
    if not state.ready:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    if not _autonomy_runtime.start():
        raise HTTPException(status_code=409, detail="Autonomy mode already running")
    
    output_dir = state.config.output_root / body.project_name
    
    def run_autonomy_pipeline():
        """Background autonomy runner with self-healing."""
        ws_manager = state.ws_manager
        
        def broadcast(event: str, data: dict[str, Any]) -> None:
            if ws_manager:
                ws_manager.broadcast_sync(WSMessage(
                    channel=ChannelType.BMAD,
                    event=event,
                    data=data
                ))
        
        try:
            broadcast("autonomy_started", {
                "goal": body.goal,
                "project_name": body.project_name,
                "max_retries": body.max_retries,
                "max_qa_cycles": body.max_qa_cycles
            })
            
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save Analyst brief
            brief_path = output_dir / "project-brief.md"
            brief_path.write_text(body.analyst_brief, encoding="utf-8")
            _autonomy_runtime.complete_agent("analyst", str(brief_path))
            
            # Agent sequence (excluding analyst which is already done)
            agents = ["pm", "architect", "po", "sm", "dev", "qa"]
            
            for agent_name in agents:
                if _autonomy_runtime.should_stop():
                    broadcast("autonomy_stopped", {"reason": "User requested stop"})
                    _autonomy_runtime.finish(success=False)
                    return
                
                _autonomy_runtime.set_phase(agent_name, agent_name)
                broadcast("agent_start", {"agent": agent_name, "phase": agent_name})
                
                # Retry loop for agent
                success = False
                for retry in range(body.max_retries):
                    try:
                        artifact_path = _run_single_agent(state, agent_name, body.goal, output_dir)
                        _autonomy_runtime.complete_agent(agent_name, str(artifact_path))
                        broadcast("agent_done", {
                            "agent": agent_name,
                            "artifact": str(artifact_path),
                            "retry": retry
                        })
                        success = True
                        break
                    except Exception as e:
                        logger.warning(f"Agent {agent_name} failed (retry {retry + 1}/{body.max_retries}): {e}")
                        _autonomy_runtime.add_error(agent_name, str(e), retry + 1)
                        broadcast("agent_retry", {
                            "agent": agent_name,
                            "error": str(e),
                            "retry": retry + 1,
                            "max_retries": body.max_retries
                        })
                        time.sleep(2)  # Brief pause before retry
                
                if not success:
                    broadcast("agent_failed", {
                        "agent": agent_name,
                        "message": f"Agent {agent_name} failed after {body.max_retries} retries"
                    })
                    # Continue to next agent instead of stopping entirely
            
            # Self-healing QA loop
            qa_passed = False
            while not qa_passed and _autonomy_runtime.status["qa_cycles"] < body.max_qa_cycles:
                if _autonomy_runtime.should_stop():
                    break
                
                _autonomy_runtime.set_phase("fixing", "qa")
                broadcast("qa_cycle_start", {"cycle": _autonomy_runtime.status["qa_cycles"] + 1})
                
                # Check QA results
                qa_artifact = output_dir / "QA.md"
                if qa_artifact.exists():
                    qa_content = qa_artifact.read_text(encoding="utf-8")
                    
                    # Check if QA passed (look for OK verdict)
                    if "## Verdict" in qa_content and "OK" in qa_content.upper():
                        qa_passed = True
                        broadcast("qa_passed", {"cycle": _autonomy_runtime.status["qa_cycles"]})
                    else:
                        # QA found issues - retry Dev agent
                        _autonomy_runtime.increment_qa_cycle()
                        broadcast("qa_issues_found", {
                            "cycle": _autonomy_runtime.status["qa_cycles"],
                            "message": "QA found issues, retrying Developer"
                        })
                        
                        # Re-run Dev with QA feedback
                        _autonomy_runtime.set_phase("fixing", "dev")
                        try:
                            # Include QA feedback in context
                            fix_goal = f"{body.goal}\n\n## QA Feedback:\n{qa_content}"
                            artifact_path = _run_single_agent(state, "dev", fix_goal, output_dir)
                            _autonomy_runtime.complete_agent("dev", str(artifact_path))
                            
                            # Re-run QA
                            _autonomy_runtime.set_phase("fixing", "qa")
                            qa_path = _run_single_agent(state, "qa", fix_goal, output_dir)
                            _autonomy_runtime.complete_agent("qa", str(qa_path))
                        except Exception as e:
                            logger.error(f"Fix cycle failed: {e}")
                            _autonomy_runtime.add_error("fix_cycle", str(e), _autonomy_runtime.status["qa_cycles"])
                else:
                    # No QA artifact means QA didn't run properly
                    break
            
            # Complete
            _autonomy_runtime.finish(success=qa_passed or _autonomy_runtime.status["qa_cycles"] >= body.max_qa_cycles)
            broadcast("autonomy_complete", {
                "status": "success" if qa_passed else "completed_with_issues",
                "qa_cycles": _autonomy_runtime.status["qa_cycles"],
                "artifacts": _autonomy_runtime.status["artifacts_generated"],
                "errors": _autonomy_runtime.status["errors"]
            })
            
            # TODO: Send email notification if configured
            if body.notification_email:
                logger.info(f"Would send notification to {body.notification_email}")
        
        except Exception as e:
            logger.error(f"Autonomy pipeline failed: {e}")
            _autonomy_runtime.finish(success=False)
            broadcast("autonomy_error", {"error": str(e)})
    
    thread = threading.Thread(target=run_autonomy_pipeline, daemon=True)
    thread.start()
    
    return {
        "started": True,
        "goal": body.goal,
        "project_name": body.project_name,
        "output_dir": str(output_dir),
        "message": "Autonomy mode started. Watch WebSocket channel 'bmad' for progress."
    }


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def _run_single_agent(state, agent_name: str, goal: str, output_dir: Path) -> Path:
    """Run a single BMAD agent."""
    from ...agents.base import AgentContext
    from ...agents import (
        AnalystAgent, PMAgent, ArchitectAgent,
        ProductOwnerAgent, ScrumMasterAgent, DeveloperAgent, QAAgent, TestRunnerAgent
    )
    
    ctx = AgentContext(
        goal=goal,
        artifacts_root=output_dir,
        workspace_root=state.config.safety.workspace_root
    )
    
    orch = state.orchestrator
    
    agent_classes = {
        "analyst": (AnalystAgent, "analyst"),
        "pm": (PMAgent, "pm"),
        "architect": (ArchitectAgent, "architect"),
        "po": (ProductOwnerAgent, "po"),
        "sm": (ScrumMasterAgent, "sm"),
        "dev": (DeveloperAgent, "dev"),
        "qa": (QAAgent, "qa"),
        "runner": (TestRunnerAgent, "qa"),  # Use QA role for model selection
    }
    
    if agent_name not in agent_classes:
        raise ValueError(f"Unknown agent: {agent_name}")
    
    cls, role = agent_classes[agent_name]
    
    # Create agent with appropriate parameters
    base_args = [
        agent_name.upper(),
        orch.fs,
        orch.ollama,
        orch.router,
        orch.model_for_role(role),
    ]
    kwargs = {"model_options": orch.options_for_role(role)}
    
    # Dev and QA need quality gate
    if agent_name in ("dev", "qa"):
        kwargs["quality"] = orch.quality
    
    # Runner has different constructor
    if agent_name == "runner":
        # TestRunnerAgent doesn't need all the ollama/router stuff
        agent = cls(
            agent_name.upper(),
            orch.fs,
            orch.ollama,
            orch.router,
            orch.model_for_role(role),
            timeout_sec=120,
        )
    else:
        agent = cls(*base_args, **kwargs)
    
    return agent.run(ctx)
