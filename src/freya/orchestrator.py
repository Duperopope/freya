from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import FreyaConfig
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


class Orchestrator:
    def __init__(self, cfg: FreyaConfig, logger) -> None:
        self.cfg = cfg
        self.logger = logger

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

    def run_bmad_cycle(self, goal: str) -> list[Path]:
        artifacts = self.cfg.artifacts_root
        artifacts.mkdir(parents=True, exist_ok=True)

        ctx = AgentContext(goal=goal, artifacts_root=artifacts, workspace_root=self.cfg.safety.workspace_root)

        analyst = AnalystAgent(
            "Analyst", self.fs, self.ollama, self.router,
            self.model_for_role("analyst"),
            model_options=self.options_for_role("analyst"),
        )
        pm = PMAgent(
            "PM", self.fs, self.ollama, self.router,
            self.model_for_role("pm"),
            model_options=self.options_for_role("pm"),
        )
        architect = ArchitectAgent(
            "Architect", self.fs, self.ollama, self.router,
            self.model_for_role("architect"),
            model_options=self.options_for_role("architect"),
        )
        po = ProductOwnerAgent(
            "PO", self.fs, self.ollama, self.router,
            self.model_for_role("po"),
            model_options=self.options_for_role("po"),
        )
        sm = ScrumMasterAgent(
            "SM", self.fs, self.ollama, self.router,
            self.model_for_role("sm"),
            model_options=self.options_for_role("sm"),
        )
        dev = DeveloperAgent(
            "DEV", self.fs, self.ollama, self.router,
            self.model_for_role("dev"),
            model_options=self.options_for_role("dev"),
            quality=self.quality,
        )
        qa = QAAgent(
            "QA", self.fs, self.ollama, self.router,
            self.model_for_role("qa"),
            model_options=self.options_for_role("qa"),
            quality=self.quality,
        )

        out: list[Path] = []
        self.logger.info("BMAD: Analyst -> project-brief.md")
        out.append(analyst.run(ctx))

        self.logger.info("BMAD: PM -> PRD.md")
        out.append(pm.run(ctx))

        self.logger.info("BMAD: Architect -> architecture.md")
        out.append(architect.run(ctx))

        self.logger.info("BMAD: PO -> epics")
        out.append(po.run(ctx))

        self.logger.info("BMAD: SM -> stories")
        out.append(sm.run(ctx))

        self.logger.info("BMAD: DEV -> code")
        out.append(dev.run(ctx))

        self.logger.info("BMAD: QA -> QA.md")
        out.append(qa.run(ctx))

        return out
