from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

from .config import FreyaConfig, PROVIDERS
from .fsx import Fs
from .ollama_client import OllamaClient
from .router import LLMRouter, ModelScore
from .ide import IDEController
from .quality import QualityGate
from .monitoring import Monitor
from .bmad_sync import BMADSync
from .model_manager import ModelManager, ModelRegistry
from .agents.base import AgentContext
from .agents import (
    AnalystAgent,
    PMAgent,
    ArchitectAgent,
    ProductOwnerAgent,
    ScrumMasterAgent,
    DeveloperAgent,
    QAAgent,
)

# Import hybrid routing components
try:
    from .hybrid_router import HybridRouter, ProviderType, RoutingDecision
    from .local_runtimes import LocalRuntimeDetector
    from .bench_hybrid import HybridBenchmark
    from .predict_consumption import ConsumptionPredictor, UsageRecord
    HYBRID_AVAILABLE = True
except ImportError:
    HYBRID_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class AgentResult:
    """Result from an agent execution."""
    agent: str
    role: str
    output_path: Path
    provider: str
    model: str
    duration_ms: int
    tokens_estimated: int
    success: bool
    error: Optional[str] = None


@dataclass
class PipelineStatus:
    """Status of BMAD pipeline execution."""
    project_name: str
    goal: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    current_agent: Optional[str] = None
    agents_completed: list[str] = None
    results: list[AgentResult] = None
    is_running: bool = False
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.agents_completed is None:
            self.agents_completed = []
        if self.results is None:
            self.results = []


class Orchestrator:
    """
    BMAD Orchestrator v2.1
    
    Manages the BMAD agent pipeline with hybrid local/remote routing.
    
    Features:
    - 7 specialized agents (Analyst, PM, Architect, PO, SM, Dev, QA)
    - Hybrid routing: local-first with remote validation/fallback
    - Multi-provider support (Ollama, HF, Together, Groq)
    - Health monitoring and automatic failover
    - Consumption prediction and cost tracking
    """
    
    def __init__(self, cfg: FreyaConfig, log=None) -> None:
        self.cfg = cfg
        self.logger = log or logger

        self.fs = Fs(cfg.safety.workspace_root, cfg.managed_root, cfg.safety.protected_names)
        self.fs.ensure_dirs()

        self.ollama = OllamaClient(cfg.ollama.base_url, timeout_sec=cfg.ollama.timeout_sec)
        self.router = LLMRouter(self.ollama)

        self.ide = IDEController(cfg.safety.workspace_root)
        self.quality = QualityGate(self.ide)

        self.monitor = Monitor(cfg.safety.workspace_root)
        self.bmad = BMADSync(cfg.bmad_root)

        self.registry = ModelRegistry(cfg.cache_root / "model_registry.json")
        self.models = ModelManager(self.ollama, self.monitor, self.registry)

        self.routing_path = cfg.cache_root / "routing.json"
        
        # Pipeline status tracking
        self.pipeline_status: Optional[PipelineStatus] = None
        self._stop_requested = False
        
        # Initialize hybrid routing components
        self.hybrid_router: Optional['HybridRouter'] = None
        self.runtime_detector: Optional['LocalRuntimeDetector'] = None
        self.hybrid_bench: Optional['HybridBenchmark'] = None
        self.predictor: Optional['ConsumptionPredictor'] = None
        
        if HYBRID_AVAILABLE and cfg.hybrid_routing.enabled:
            self._init_hybrid_routing()

        # Load prior bench scores if present (typed)
        bench_path = cfg.cache_root / "bench.json"
        if bench_path.exists():
            try:
                data = json.loads(bench_path.read_text(encoding="utf-8"))
                scores: dict[str, list[ModelScore]] = {}
                for role, arr in (data or {}).items():
                    role_scores: list[ModelScore] = []
                    for s in (arr or []):
                        if not isinstance(s, dict):
                            continue
                        model = str(s.get("model", "")).strip()
                        if not model:
                            continue
                        latency_ms = int(s.get("latency_ms", 999999))
                        format_score = int(s.get("format_score", -999999))
                        raw_opts = s.get("options")
                        options: dict[str, Any] = dict(raw_opts) if isinstance(raw_opts, dict) else {}
                        role_scores.append(
                            ModelScore(
                                model=model,
                                latency_ms=latency_ms,
                                format_score=format_score,
                                role=str(role),
                                options=options,
                            )
                        )
                    role_scores.sort(key=lambda x: (-x.format_score, x.latency_ms))
                    scores[str(role)] = role_scores
                self.router.scores = scores
            except Exception:
                pass
    
    def _init_hybrid_routing(self) -> None:
        """Initialize hybrid routing components."""
        try:
            # Runtime detector
            self.runtime_detector = LocalRuntimeDetector()
            self.runtime_detector.detect_all_runtimes()
            
            # Hybrid router
            self.hybrid_router = HybridRouter(
                self.cfg,
                self.ollama,
                bench_scores=self.router.scores,
            )
            
            # Hybrid benchmark
            self.hybrid_bench = HybridBenchmark(self.cfg, self.ollama)
            
            # Consumption predictor
            self.predictor = ConsumptionPredictor(self.cfg.cache_root / "consumption")
            
            self.logger.info("Hybrid routing initialized successfully")
            
            # Log available runtimes
            available = self.runtime_detector.get_available_runtimes()
            if available:
                self.logger.info(f"Available local runtimes: {[r.name for r in available]}")
            
            # Log provider status
            health = self.hybrid_router.get_health_status()
            for provider, status in health.items():
                self.logger.info(f"Provider {provider}: {status.get('status', 'unknown')}")
                
        except Exception as e:
            self.logger.warning(f"Failed to initialize hybrid routing: {e}")
            self.hybrid_router = None

    def init_workspace(self) -> None:
        self.cfg.managed_root.mkdir(parents=True, exist_ok=True)
        (self.cfg.managed_root / "tmp").mkdir(parents=True, exist_ok=True)

    def sync_bmad(self) -> str:
        return self.bmad.sync()

    def load_routing(self) -> dict[str, Any]:
        if not self.routing_path.exists():
            return {}
        try:
            data = json.loads(self.routing_path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def save_routing(self, routing: dict[str, Any]) -> None:
        self.routing_path.parent.mkdir(parents=True, exist_ok=True)
        self.routing_path.write_text(json.dumps(routing, indent=2, ensure_ascii=False), encoding="utf-8")

    def model_for_role(self, role: str) -> str:
        routing = self.load_routing()
        v = routing.get(role)
        if isinstance(v, str) and v.strip():
            return v.strip()
        if isinstance(v, dict) and isinstance(v.get("model"), str) and v["model"].strip():
            return v["model"].strip()
        return getattr(self.cfg.models, role)

    def options_for_role(self, role: str) -> dict[str, Any]:
        routing = self.load_routing()
        v = routing.get(role)
        if isinstance(v, dict) and isinstance(v.get("options"), dict):
            return dict(v["options"])
        return {}

    def request_stop(self) -> None:
        """Request the pipeline to stop after the current agent completes."""
        self._stop_requested = True
        self.logger.info("Stop requested for BMAD pipeline")
    
    def get_pipeline_status(self) -> Optional[PipelineStatus]:
        """Get current pipeline status."""
        return self.pipeline_status
    
    def _select_routing(self, role: str) -> tuple[str, str, dict[str, Any]]:
        """
        Select model and provider for a role using hybrid routing.
        
        Returns: (provider, model, options)
        """
        # Use hybrid router if available
        if self.hybrid_router and self.cfg.hybrid_routing.enabled:
            # Get local score from bench if available
            local_score = None
            if role in self.router.scores and self.router.scores[role]:
                local_score = self.router.scores[role][0].format_score
            
            decision = self.hybrid_router.select_provider(role, local_score)
            
            self.logger.info(
                f"Routing {role}: {decision.provider} -> {decision.model} "
                f"(reason: {decision.reason})"
            )
            
            return decision.provider, decision.model, {}
        
        # Fallback to standard routing
        model = self.model_for_role(role)
        options = self.options_for_role(role)
        return "local", model, options
    
    def run_bmad_cycle(
        self,
        goal: str,
        project_name: str = "FreyaProject",
        continuous: bool = True,
        progress_cb: Callable[[str, dict], None] | None = None,
    ) -> list[Path]:
        """
        Run the complete BMAD agent pipeline.
        
        Args:
            goal: Project goal/description
            project_name: Name for the project
            continuous: If True, continue through all agents even on errors
            progress_cb: Callback for progress updates
        
        Returns:
            List of artifact paths created
        """
        import time
        
        self._stop_requested = False
        artifacts = self.cfg.artifacts_root / project_name
        artifacts.mkdir(parents=True, exist_ok=True)

        ctx = AgentContext(
            goal=goal,
            artifacts_root=artifacts,
            workspace_root=self.cfg.safety.workspace_root,
        )
        
        # Initialize pipeline status
        self.pipeline_status = PipelineStatus(
            project_name=project_name,
            goal=goal,
            started_at=datetime.now(),
            is_running=True,
        )
        
        # Define agent pipeline with roles
        pipeline = [
            ("analyst", "project-brief.md", AnalystAgent),
            ("pm", "PRD.md", PMAgent),
            ("architect", "architecture.md", ArchitectAgent),
            ("po", "epics/", ProductOwnerAgent),
            ("sm", "stories/", ScrumMasterAgent),
            ("dev", "code/", DeveloperAgent),
            ("qa", "QA.md", QAAgent),
        ]

        out: list[Path] = []
        
        for role, output_name, agent_class in pipeline:
            # Check for stop request
            if self._stop_requested:
                self.logger.info(f"Pipeline stopped at {role}")
                self.pipeline_status.error = "Stopped by user request"
                break
            
            # Update status
            self.pipeline_status.current_agent = role
            
            if progress_cb:
                progress_cb("agent_start", {
                    "agent": role,
                    "output": output_name,
                    "completed": len(self.pipeline_status.agents_completed),
                    "total": len(pipeline),
                })
            
            # Select routing
            provider, model, options = self._select_routing(role)
            
            self.logger.info(f"BMAD: {role.upper()} -> {output_name} (provider: {provider}, model: {model})")
            
            t0 = time.time()
            result = AgentResult(
                agent=role,
                role=role,
                output_path=artifacts / output_name,
                provider=provider,
                model=model,
                duration_ms=0,
                tokens_estimated=0,
                success=False,
            )
            
            try:
                # Create agent with selected model
                if agent_class in (DeveloperAgent, QAAgent):
                    agent = agent_class(
                        role.upper(), self.fs, self.ollama, self.router,
                        model,
                        model_options=options,
                        quality=self.quality,
                    )
                else:
                    agent = agent_class(
                        role.upper(), self.fs, self.ollama, self.router,
                        model,
                        model_options=options,
                    )
                
                # Run agent
                output_path = agent.run(ctx)
                
                result.output_path = output_path
                result.duration_ms = int((time.time() - t0) * 1000)
                result.success = True
                
                out.append(output_path)
                self.pipeline_status.agents_completed.append(role)
                
                # Track usage if predictor available
                if self.predictor:
                    record = UsageRecord(
                        timestamp=datetime.now(),
                        role=role,
                        prompt_tokens=500,  # Estimate
                        completion_tokens=1500,  # Estimate
                        total_tokens=2000,
                        provider=provider,
                        model=model,
                        latency_ms=result.duration_ms,
                    )
                    self.predictor.add_record(record)
                
                if progress_cb:
                    progress_cb("agent_done", {
                        "agent": role,
                        "output": str(output_path),
                        "duration_ms": result.duration_ms,
                        "success": True,
                    })
                    
            except Exception as e:
                result.error = str(e)
                result.duration_ms = int((time.time() - t0) * 1000)
                
                self.logger.error(f"Agent {role} failed: {e}")
                
                if progress_cb:
                    progress_cb("agent_error", {
                        "agent": role,
                        "error": str(e),
                        "duration_ms": result.duration_ms,
                    })
                
                if not continuous:
                    self.pipeline_status.error = f"Agent {role} failed: {e}"
                    break
            
            self.pipeline_status.results.append(result)
        
        # Mark pipeline complete
        self.pipeline_status.is_running = False
        self.pipeline_status.completed_at = datetime.now()
        self.pipeline_status.current_agent = None
        
        if progress_cb:
            progress_cb("pipeline_complete", {
                "total_agents": len(pipeline),
                "completed": len(self.pipeline_status.agents_completed),
                "artifacts": [str(p) for p in out],
                "error": self.pipeline_status.error,
            })

        return out
    
    def run_hybrid_bench(
        self,
        providers: list[str] | None = None,
        progress_cb: Callable[[str, dict], None] | None = None,
    ) -> dict[str, Any]:
        """
        Run hybrid benchmark across local and remote providers.
        
        Args:
            providers: List of providers to bench (default: ["local"])
            progress_cb: Progress callback
        
        Returns:
            Benchmark results and rankings
        """
        if not self.hybrid_bench:
            return {"error": "Hybrid benchmarking not available"}
        
        providers = providers or ["local"]
        results = []
        
        for provider in providers:
            self.logger.info(f"Running micro-bench for {provider}")
            
            provider_results = self.hybrid_bench.run_micro_bench(
                provider=provider,
                progress_cb=progress_cb,
            )
            results.extend(provider_results)
        
        # Calculate rankings
        rankings = self.hybrid_bench.calculate_rankings()
        
        # Mark bench complete for scheduling
        for provider in providers:
            self.hybrid_bench.mark_bench_complete(provider)
        
        return {
            "results": [
                {
                    "case": r.case_name,
                    "role": r.role,
                    "model": r.model,
                    "provider": r.provider,
                    "score": r.score,
                    "passed": r.passed,
                    "latency_ms": r.latency_ms,
                }
                for r in results
            ],
            "rankings": {
                role: [
                    {
                        "model": m.model,
                        "provider": m.provider,
                        "score": m.score,
                        "public_score": m.public_score,
                        "local_score": m.local_score,
                    }
                    for m in models
                ]
                for role, models in rankings.items()
            },
        }
    
    def get_provider_health(self) -> dict[str, Any]:
        """Get health status of all providers."""
        if not self.hybrid_router:
            return {"local": {"status": "unknown"}}
        
        return self.hybrid_router.get_health_status()
    
    def get_usage_stats(self) -> dict[str, Any]:
        """Get usage statistics."""
        stats = {}
        
        if self.hybrid_router:
            stats["routing"] = self.hybrid_router.get_usage_stats()
        
        if self.predictor:
            stats["consumption"] = self.predictor.get_stats()
        
        if self.runtime_detector:
            stats["runtimes"] = self.runtime_detector.get_runtime_status()
        
        return stats
    
    def predict_consumption(
        self,
        role: str,
        prompt_tokens: int = 500,
        provider: str = "local",
    ) -> dict[str, Any]:
        """Predict token consumption and cost for a task."""
        if not self.predictor:
            return {"error": "Consumption predictor not available"}
        
        prediction = self.predictor.predict(role, prompt_tokens, provider)
        
        return {
            "estimated_tokens": prediction.estimated_tokens,
            "estimated_cost_usd": prediction.estimated_cost_usd,
            "estimated_latency_ms": prediction.estimated_latency_ms,
            "confidence": prediction.confidence,
            "provider_recommendation": prediction.provider_recommendation,
            "breakdown": prediction.breakdown,
        }
    
    def get_system_snapshot(self) -> dict[str, Any]:
        """Get a complete system snapshot for monitoring."""
        import psutil
        
        snapshot = {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "percent": psutil.virtual_memory().percent,
            },
            "disk": {
                "total": psutil.disk_usage("/").total,
                "free": psutil.disk_usage("/").free,
                "percent": psutil.disk_usage("/").percent,
            },
        }
        
        # Add provider health
        snapshot["providers"] = self.get_provider_health()
        
        # Add pipeline status
        if self.pipeline_status:
            snapshot["pipeline"] = {
                "project": self.pipeline_status.project_name,
                "is_running": self.pipeline_status.is_running,
                "current_agent": self.pipeline_status.current_agent,
                "completed": len(self.pipeline_status.agents_completed),
            }
        
        return snapshot
