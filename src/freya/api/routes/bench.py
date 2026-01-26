# src/freya/api/routes/bench.py
"""
Benchmark API Routes

Endpoints for LLM benchmarking:
- Start/stop benchmarks
- Get progress and results
- View benchmark history
- Apply routing from results
"""

from __future__ import annotations

import asyncio
import json
import threading
import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel, Field

from ..websocket import ChannelType, WSMessage

router = APIRouter()


# -----------------------------------------------------------------------------
# Request/Response Models
# -----------------------------------------------------------------------------
class BenchStartRequest(BaseModel):
    """Request to start a benchmark."""
    program: str = Field(default="bench-fast", description="bench-fast, bench-standard, bench-advanced")
    resume: bool = Field(default=True, description="Resume from last checkpoint if available")


class BenchStatus(BaseModel):
    """Current benchmark status."""
    running: bool
    program: str
    phase: str
    role: str
    model: str
    model_index: int
    total_models: int
    step_index: int
    total_steps: int
    last_event: str
    progress_percent: float


class BenchResult(BaseModel):
    """Single benchmark result row."""
    role: str
    phase: str
    model: str
    score: int
    latency_ms: int
    status: str


class BillboardEntry(BaseModel):
    """Best model for a role."""
    role: str
    model: str
    score: int
    latency_ms: int
    options: dict[str, Any] = {}


class BenchState(BaseModel):
    """Persistent benchmark state."""
    program: str
    done_count: int
    updated_at: str | None


# -----------------------------------------------------------------------------
# Global Benchmark State (thread-safe)
# -----------------------------------------------------------------------------
class BenchRuntime:
    """Thread-safe benchmark runtime state."""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._running = False
        self._stop_requested = False
        self._program = "bench-fast"
        self._phase = ""
        self._role = ""
        self._model = ""
        self._model_i = 0
        self._total_models = 1
        self._step_i = 0
        self._steps_total = 1
        self._last_event = ""
        self._thread: threading.Thread | None = None
    
    @property
    def status(self) -> dict[str, Any]:
        with self._lock:
            total = max(1, self._total_models * self._steps_total)
            current = self._model_i * self._steps_total + self._step_i
            progress = (current / total) * 100 if total > 0 else 0
            
            return {
                "running": self._running,
                "program": self._program,
                "phase": self._phase,
                "role": self._role,
                "model": self._model,
                "model_index": self._model_i,
                "total_models": self._total_models,
                "step_index": self._step_i,
                "total_steps": self._steps_total,
                "last_event": self._last_event,
                "progress_percent": round(progress, 1),
            }
    
    def start(self, program: str) -> bool:
        with self._lock:
            if self._running:
                return False
            self._running = True
            self._stop_requested = False
            self._program = program
            self._phase = "starting"
            self._role = ""
            self._model = ""
            self._model_i = 0
            self._step_i = 0
            self._last_event = "start"
            return True
    
    def stop(self) -> None:
        with self._lock:
            self._stop_requested = True
    
    def finish(self) -> None:
        with self._lock:
            self._running = False
            self._stop_requested = False
    
    def should_stop(self) -> bool:
        with self._lock:
            return self._stop_requested
    
    def update(self, **kwargs) -> None:
        with self._lock:
            for key, value in kwargs.items():
                if hasattr(self, f"_{key}"):
                    setattr(self, f"_{key}", value)


# Global runtime instance
_bench_runtime = BenchRuntime()


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------
@router.get("/status", response_model=BenchStatus)
async def get_bench_status() -> BenchStatus:
    """Get current benchmark status."""
    return BenchStatus(**_bench_runtime.status)


@router.post("/start")
async def start_benchmark(
    request: Request,
    body: BenchStartRequest,
    background_tasks: BackgroundTasks
) -> dict[str, Any]:
    """
    Start a benchmark run.
    
    Progress is streamed via WebSocket (channel: bench).
    """
    state = request.app.state.freya
    
    if not state.ready:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    if not _bench_runtime.start(body.program):
        raise HTTPException(status_code=409, detail="Benchmark already running")
    
    # Determine trials and mode based on program
    config_map = {
        "bench-fast": {"trials": 1, "mode": "quick"},
        "bench-standard": {"trials": 5, "mode": "tune"},
        "bench-advanced": {"trials": 5, "mode": "tune"},
    }
    config = config_map.get(body.program, config_map["bench-fast"])
    
    def run_bench():
        """Background benchmark runner."""
        try:
            cache_dir = state.config.cache_root / "bench_runs" / body.program
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            ws_manager = state.ws_manager
            
            def progress_callback(event: str, payload: dict[str, Any]) -> None:
                """Handle benchmark progress events."""
                _bench_runtime.update(last_event=event)
                
                if event == "phase_start":
                    _bench_runtime.update(phase=payload.get("phase", ""))
                
                elif event == "role_start":
                    _bench_runtime.update(
                        role=payload.get("role", ""),
                        total_models=payload.get("total_models", 1)
                    )
                
                elif event == "model_start":
                    _bench_runtime.update(
                        model=payload.get("model", ""),
                        model_i=payload.get("model_i", 0),
                        total_models=payload.get("total_models", 1),
                        steps_total=payload.get("steps_total", 1),
                        step_i=0
                    )
                
                elif event == "step_done":
                    with _bench_runtime._lock:
                        _bench_runtime._step_i += 1
                
                elif event == "model_done":
                    # Broadcast result via WebSocket
                    if ws_manager:
                        ws_manager.broadcast_sync(WSMessage(
                            channel=ChannelType.BENCH,
                            event="model_done",
                            data=payload
                        ))
                
                # Broadcast progress update
                if ws_manager:
                    ws_manager.broadcast_sync(WSMessage(
                        channel=ChannelType.BENCH,
                        event="progress",
                        data=_bench_runtime.status
                    ))
            
            # Run the benchmark
            state.router.bench(
                roles=None,
                models=None,
                max_models=0,
                trials=config["trials"],
                mode=config["mode"],
                cache_dir=cache_dir,
                resume=body.resume,
                program=body.program,
                progress=progress_callback,
                should_stop=_bench_runtime.should_stop,
            )
            
            # Persist results
            _persist_bench_json(state)
            
            # Broadcast completion
            if ws_manager:
                ws_manager.broadcast_sync(WSMessage(
                    channel=ChannelType.BENCH,
                    event="complete",
                    data={"program": body.program, "status": "success"}
                ))
        
        except Exception as e:
            if state.ws_manager:
                state.ws_manager.broadcast_sync(WSMessage(
                    channel=ChannelType.BENCH,
                    event="error",
                    data={"error": str(e)}
                ))
        
        finally:
            _bench_runtime.finish()
    
    # Start in background thread
    thread = threading.Thread(target=run_bench, daemon=True)
    thread.start()
    
    return {
        "started": True,
        "program": body.program,
        "resume": body.resume,
        "message": "Benchmark started. Watch WebSocket channel 'bench' for progress."
    }


@router.post("/stop")
async def stop_benchmark() -> dict[str, str]:
    """Request benchmark stop (soft stop, waits for current step)."""
    _bench_runtime.stop()
    return {"message": "Stop requested"}


@router.get("/billboard", response_model=list[BillboardEntry])
async def get_billboard(request: Request) -> list[BillboardEntry]:
    """Get the best model for each role from bench results."""
    state = request.app.state.freya
    
    if not state.router.scores:
        return []
    
    entries = []
    for role, scores in state.router.scores.items():
        if scores:
            best = scores[0]
            entries.append(BillboardEntry(
                role=role,
                model=best.model,
                score=best.format_score,
                latency_ms=best.latency_ms,
                options=dict(best.options) if best.options else {}
            ))
    
    return entries


@router.get("/history")
async def get_bench_history(request: Request, program: str = "bench-fast", limit: int = 100) -> list[BenchResult]:
    """Get benchmark history from JSONL log."""
    state = request.app.state.freya
    
    jsonl_path = state.config.cache_root / "bench_runs" / program / "bench_table.jsonl"
    
    if not jsonl_path.exists():
        return []
    
    results = []
    try:
        lines = jsonl_path.read_text(encoding="utf-8").splitlines()
        for line in lines[-limit:]:
            try:
                obj = json.loads(line)
                if obj.get("type") == "model_done":
                    results.append(BenchResult(
                        role=str(obj.get("role", "")),
                        phase=str(obj.get("phase", "")),
                        model=str(obj.get("model", "")),
                        score=int(obj.get("score", 0)),
                        latency_ms=int(obj.get("latency_ms", 0)),
                        status=str(obj.get("status", ""))
                    ))
            except (json.JSONDecodeError, ValueError):
                continue
    except Exception:
        pass
    
    return results


@router.get("/state", response_model=BenchState)
async def get_bench_state(request: Request, program: str = "bench-fast") -> BenchState:
    """Get persistent benchmark state."""
    state = request.app.state.freya
    
    state_path = state.config.cache_root / "bench_runs" / program / "bench_state.json"
    
    if not state_path.exists():
        return BenchState(program=program, done_count=0, updated_at=None)
    
    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
        done = data.get("done", {})
        meta = data.get("meta", {})
        updated = meta.get("updated_at")
        
        return BenchState(
            program=program,
            done_count=len(done) if isinstance(done, dict) else 0,
            updated_at=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(updated)) if updated else None
        )
    except Exception:
        return BenchState(program=program, done_count=0, updated_at=None)


@router.post("/apply-routing")
async def apply_routing(request: Request) -> dict[str, Any]:
    """Apply best models from benchmark to routing.json."""
    state = request.app.state.freya
    
    if not state.router.scores:
        raise HTTPException(status_code=400, detail="No benchmark scores available")
    
    routing: dict[str, Any] = {}
    for role, scores in state.router.scores.items():
        if scores:
            best = scores[0]
            routing[role] = {
                "model": best.model,
                "options": dict(best.options) if best.options else {}
            }
    
    routing_path = state.config.routing_path
    routing_path.parent.mkdir(parents=True, exist_ok=True)
    routing_path.write_text(json.dumps(routing, indent=2, ensure_ascii=False), encoding="utf-8")
    
    return {
        "success": True,
        "path": str(routing_path),
        "roles_configured": list(routing.keys())
    }


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def _persist_bench_json(state) -> None:
    """Persist benchmark scores to bench.json."""
    if not state.router.scores:
        return
    
    out: dict[str, list[dict[str, Any]]] = {}
    for role, scores in state.router.scores.items():
        rows = []
        for s in scores:
            rows.append({
                "model": s.model,
                "latency_ms": s.latency_ms,
                "format_score": s.format_score,
                "role": s.role,
                "options": dict(s.options) if s.options else {}
            })
        out[role] = rows
    
    bench_path = state.config.cache_root / "bench.json"
    bench_path.parent.mkdir(parents=True, exist_ok=True)
    bench_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
