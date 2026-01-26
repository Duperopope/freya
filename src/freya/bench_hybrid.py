# src/freya/bench_hybrid.py
"""
Hybrid Benchmarking System for Freya 2.1
========================================

Intelligent benchmarking for local and remote LLM providers.

Features:
- Public benchmark integration (Kaggle, llm-stats)
- Micro-benchmark (sanity checks)
- Role-based scoring for BMAD agents
- Provider comparison and ranking
- Automatic scheduling (monthly)

References:
- Kaggle AI Models Benchmark 2026: https://www.kaggle.com/datasets/asadullahcreative/ai-models-benchmark-dataset-2026-latest
- llm-stats: Various LLM leaderboards
- Clarifai Top Models: https://www.clarifai.com/blog/top-10-open-source-reasoning-models-in-2026
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

import requests

from .config import PROVIDERS, FreyaConfig
from .ollama_client import OllamaClient

logger = logging.getLogger(__name__)


# =============================================================================
# PUBLIC BENCHMARK DATA
# =============================================================================

# Role-to-benchmark mapping: which public benchmarks are relevant for each BMAD role
ROLE_BENCHMARK_MAPPING: dict[str, list[str]] = {
    "analyst": ["reasoning", "comprehension", "analysis"],
    "pm": ["reasoning", "instruction_following", "summarization"],
    "architect": ["reasoning", "code", "planning"],
    "po": ["reasoning", "comprehension", "prioritization"],
    "sm": ["reasoning", "planning", "summarization"],
    "dev": ["code", "reasoning", "instruction_following"],
    "qa": ["code", "reasoning", "analysis"],
}

# Known public benchmark scores (updated from Kaggle/llm-stats 2026)
# Format: model_name -> {benchmark_name: score}
PUBLIC_BENCHMARK_SCORES: dict[str, dict[str, float]] = {
    # Llama models
    "llama3.1:8b": {
        "mmlu": 69.4,
        "humaneval": 62.2,
        "gsm8k": 80.1,
        "hellaswag": 81.5,
        "reasoning": 72.0,
        "code": 62.2,
        "comprehension": 75.0,
    },
    "llama3.2:latest": {
        "mmlu": 63.4,
        "humaneval": 43.2,
        "gsm8k": 65.3,
        "hellaswag": 78.2,
        "reasoning": 68.0,
        "code": 43.2,
        "comprehension": 70.5,
    },
    "llama-3.3-70b-versatile": {
        "mmlu": 86.0,
        "humaneval": 82.6,
        "gsm8k": 93.0,
        "hellaswag": 88.5,
        "reasoning": 85.0,
        "code": 82.6,
        "comprehension": 87.0,
    },
    # Qwen models
    "qwen2.5:7b": {
        "mmlu": 74.2,
        "humaneval": 75.2,
        "gsm8k": 82.6,
        "hellaswag": 80.1,
        "reasoning": 76.0,
        "code": 75.2,
        "comprehension": 77.0,
    },
    "Qwen/Qwen2.5-72B-Instruct": {
        "mmlu": 85.3,
        "humaneval": 86.5,
        "gsm8k": 91.2,
        "hellaswag": 87.0,
        "reasoning": 86.0,
        "code": 86.5,
        "comprehension": 85.5,
    },
    # DeepSeek models
    "deepseek-coder-v2:latest": {
        "mmlu": 79.4,
        "humaneval": 90.2,
        "gsm8k": 85.1,
        "hellaswag": 82.0,
        "reasoning": 78.0,
        "code": 90.2,
        "comprehension": 80.0,
    },
    "deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct": {
        "mmlu": 73.2,
        "humaneval": 82.3,
        "gsm8k": 78.5,
        "hellaswag": 78.5,
        "reasoning": 74.0,
        "code": 82.3,
        "comprehension": 75.0,
    },
    # Mistral models
    "mistral:7b": {
        "mmlu": 60.1,
        "humaneval": 40.2,
        "gsm8k": 52.2,
        "hellaswag": 81.3,
        "reasoning": 62.0,
        "code": 40.2,
        "comprehension": 68.0,
    },
    # Groq models
    "llama-3.1-8b-instant": {
        "mmlu": 69.4,
        "humaneval": 62.2,
        "gsm8k": 80.1,
        "hellaswag": 81.5,
        "reasoning": 72.0,
        "code": 62.2,
        "comprehension": 75.0,
    },
}


@dataclass
class BenchmarkCase:
    """A single benchmark test case."""
    name: str
    role: str
    prompt: str
    expected_patterns: list[str] = field(default_factory=list)
    expected_format: str = ""
    max_score: int = 100
    timeout_sec: int = 60


@dataclass
class BenchmarkResult:
    """Result of running a benchmark."""
    case_name: str
    role: str
    model: str
    provider: str
    score: int
    latency_ms: int
    response_length: int
    passed: bool
    notes: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ModelRanking:
    """Model ranking for a specific role."""
    role: str
    model: str
    provider: str
    score: float
    public_score: float
    local_score: float
    latency_avg_ms: int
    reliability: float  # 0-1, based on success rate
    last_bench: Optional[datetime] = None


class HybridBenchmark:
    """
    Hybrid benchmarking system for local and remote providers.
    """
    
    def __init__(self, cfg: FreyaConfig, local_client: OllamaClient):
        self.cfg = cfg
        self.local_client = local_client
        
        # Storage paths
        self.bench_cache = cfg.cache_root / "hybrid_bench"
        self.bench_cache.mkdir(parents=True, exist_ok=True)
        
        self.results_path = self.bench_cache / "results.json"
        self.rankings_path = self.bench_cache / "rankings.json"
        self.schedule_path = self.bench_cache / "schedule.json"
        
        # Load existing data
        self.results: list[BenchmarkResult] = self._load_results()
        self.rankings: dict[str, list[ModelRanking]] = self._load_rankings()
    
    def _load_results(self) -> list[BenchmarkResult]:
        """Load benchmark results from disk."""
        if not self.results_path.exists():
            return []
        
        try:
            data = json.loads(self.results_path.read_text(encoding="utf-8"))
            return [
                BenchmarkResult(
                    case_name=r["case_name"],
                    role=r["role"],
                    model=r["model"],
                    provider=r["provider"],
                    score=r["score"],
                    latency_ms=r["latency_ms"],
                    response_length=r["response_length"],
                    passed=r["passed"],
                    notes=r.get("notes", ""),
                    timestamp=datetime.fromisoformat(r["timestamp"]) if r.get("timestamp") else datetime.now(),
                )
                for r in data
            ]
        except Exception as e:
            logger.warning(f"Failed to load bench results: {e}")
            return []
    
    def _save_results(self) -> None:
        """Save benchmark results to disk."""
        try:
            data = [
                {
                    "case_name": r.case_name,
                    "role": r.role,
                    "model": r.model,
                    "provider": r.provider,
                    "score": r.score,
                    "latency_ms": r.latency_ms,
                    "response_length": r.response_length,
                    "passed": r.passed,
                    "notes": r.notes,
                    "timestamp": r.timestamp.isoformat(),
                }
                for r in self.results
            ]
            self.results_path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as e:
            logger.error(f"Failed to save bench results: {e}")
    
    def _load_rankings(self) -> dict[str, list[ModelRanking]]:
        """Load model rankings from disk."""
        if not self.rankings_path.exists():
            return {}
        
        try:
            data = json.loads(self.rankings_path.read_text(encoding="utf-8"))
            rankings = {}
            for role, models in data.items():
                rankings[role] = [
                    ModelRanking(
                        role=m["role"],
                        model=m["model"],
                        provider=m["provider"],
                        score=m["score"],
                        public_score=m["public_score"],
                        local_score=m["local_score"],
                        latency_avg_ms=m["latency_avg_ms"],
                        reliability=m["reliability"],
                        last_bench=datetime.fromisoformat(m["last_bench"]) if m.get("last_bench") else None,
                    )
                    for m in models
                ]
            return rankings
        except Exception as e:
            logger.warning(f"Failed to load rankings: {e}")
            return {}
    
    def _save_rankings(self) -> None:
        """Save model rankings to disk."""
        try:
            data = {}
            for role, models in self.rankings.items():
                data[role] = [
                    {
                        "role": m.role,
                        "model": m.model,
                        "provider": m.provider,
                        "score": m.score,
                        "public_score": m.public_score,
                        "local_score": m.local_score,
                        "latency_avg_ms": m.latency_avg_ms,
                        "reliability": m.reliability,
                        "last_bench": m.last_bench.isoformat() if m.last_bench else None,
                    }
                    for m in models
                ]
            self.rankings_path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as e:
            logger.error(f"Failed to save rankings: {e}")
    
    def get_micro_bench_cases(self) -> list[BenchmarkCase]:
        """Get micro-benchmark (sanity check) cases."""
        cases = []
        
        # Analyst micro-bench
        cases.append(BenchmarkCase(
            name="analyst_brief",
            role="analyst",
            prompt="Briefly describe the key requirements for a simple todo app in 3 bullet points.",
            expected_patterns=["todo", "task", "requirement", "user", "feature"],
            expected_format="bullet points",
            max_score=100,
            timeout_sec=30,
        ))
        
        # PM micro-bench
        cases.append(BenchmarkCase(
            name="pm_prd",
            role="pm",
            prompt="Write a one-paragraph product description for a note-taking app.",
            expected_patterns=["note", "user", "feature", "app"],
            expected_format="paragraph",
            max_score=100,
            timeout_sec=30,
        ))
        
        # Architect micro-bench
        cases.append(BenchmarkCase(
            name="architect_design",
            role="architect",
            prompt="List 3 main components needed for a REST API backend.",
            expected_patterns=["api", "database", "controller", "service", "endpoint"],
            expected_format="list",
            max_score=100,
            timeout_sec=30,
        ))
        
        # Dev micro-bench
        cases.append(BenchmarkCase(
            name="dev_code",
            role="dev",
            prompt="Write a Python function that adds two numbers and returns the result.",
            expected_patterns=["def", "return", "+", "sum", "add"],
            expected_format="code",
            max_score=100,
            timeout_sec=30,
        ))
        
        # QA micro-bench
        cases.append(BenchmarkCase(
            name="qa_test",
            role="qa",
            prompt="Write a simple test case description for testing user login functionality.",
            expected_patterns=["test", "login", "user", "password", "verify", "expect"],
            expected_format="test case",
            max_score=100,
            timeout_sec=30,
        ))
        
        return cases
    
    def evaluate_response(self, response: str, case: BenchmarkCase) -> tuple[int, str]:
        """
        Evaluate a response against a benchmark case.
        Returns (score, notes).
        """
        score = 0
        notes = []
        
        if not response or not response.strip():
            return 0, "Empty response"
        
        response_lower = response.lower()
        
        # Pattern matching (40 points)
        patterns_found = 0
        for pattern in case.expected_patterns:
            if pattern.lower() in response_lower:
                patterns_found += 1
        
        if case.expected_patterns:
            pattern_score = int((patterns_found / len(case.expected_patterns)) * 40)
            score += pattern_score
            notes.append(f"Patterns: {patterns_found}/{len(case.expected_patterns)}")
        
        # Length check (20 points)
        min_len = 50
        good_len = 200
        if len(response) >= good_len:
            score += 20
        elif len(response) >= min_len:
            score += int((len(response) - min_len) / (good_len - min_len) * 20)
        notes.append(f"Length: {len(response)}")
        
        # Format check (20 points)
        format_score = 0
        if case.expected_format == "bullet points":
            if "-" in response or "*" in response or "•" in response:
                format_score = 20
        elif case.expected_format == "code":
            if "def " in response or "function" in response or "class " in response:
                format_score = 20
        elif case.expected_format == "list":
            if any(c in response for c in ["1.", "2.", "-", "*"]):
                format_score = 20
        else:
            format_score = 10  # Default partial score
        
        score += format_score
        notes.append(f"Format: {format_score}/20")
        
        # Coherence check (20 points)
        # Simple heuristic: check for sentence structure
        sentences = response.split(".")
        if len(sentences) >= 2:
            score += 10
        if len(response.split()) >= 20:
            score += 10
        
        return min(score, case.max_score), "; ".join(notes)
    
    def run_micro_bench(
        self,
        provider: str = "local",
        models: list[str] | None = None,
        progress_cb: Callable[[str, dict], None] | None = None,
    ) -> list[BenchmarkResult]:
        """
        Run micro-benchmark (sanity check) suite.
        """
        cases = self.get_micro_bench_cases()
        results = []
        
        if provider == "local":
            # Get available local models
            try:
                tags = self.local_client.tags()
                available_models = [m.get("name", "") for m in tags if isinstance(m, dict)]
            except Exception:
                available_models = []
            
            if models:
                available_models = [m for m in available_models if m in models]
        else:
            # Use remote provider models
            provider_cfg = PROVIDERS.get(provider, {})
            available_models = list(provider_cfg.get("models", {}).values())
        
        if not available_models:
            logger.warning(f"No models available for {provider}")
            return results
        
        for case in cases:
            for model in available_models:
                if progress_cb:
                    progress_cb("running", {"case": case.name, "model": model, "provider": provider})
                
                try:
                    t0 = time.time()
                    
                    if provider == "local":
                        result = self.local_client.generate(
                            model=model,
                            prompt=case.prompt,
                            system=f"You are a {case.role} agent. Respond concisely.",
                            timeout_sec=case.timeout_sec,
                        )
                        response = result.response
                        latency_ms = int((time.time() - t0) * 1000)
                    else:
                        # Would use remote client here
                        response = ""
                        latency_ms = 0
                    
                    score, notes = self.evaluate_response(response, case)
                    
                    bench_result = BenchmarkResult(
                        case_name=case.name,
                        role=case.role,
                        model=model,
                        provider=provider,
                        score=score,
                        latency_ms=latency_ms,
                        response_length=len(response),
                        passed=score >= 50,
                        notes=notes,
                    )
                    
                    results.append(bench_result)
                    self.results.append(bench_result)
                    
                except Exception as e:
                    logger.warning(f"Bench failed for {model} on {case.name}: {e}")
                    results.append(BenchmarkResult(
                        case_name=case.name,
                        role=case.role,
                        model=model,
                        provider=provider,
                        score=0,
                        latency_ms=0,
                        response_length=0,
                        passed=False,
                        notes=f"Error: {e}",
                    ))
        
        self._save_results()
        return results
    
    def get_public_score(self, model: str, role: str) -> float:
        """Get public benchmark score for a model and role."""
        # Normalize model name
        model_key = model.lower().replace(":", "-")
        
        # Try exact match first
        scores = PUBLIC_BENCHMARK_SCORES.get(model, {})
        if not scores:
            # Try partial match
            for key, value in PUBLIC_BENCHMARK_SCORES.items():
                if key.lower() in model_key or model_key in key.lower():
                    scores = value
                    break
        
        if not scores:
            return 0.0
        
        # Get relevant benchmarks for role
        relevant_benchmarks = ROLE_BENCHMARK_MAPPING.get(role, ["reasoning"])
        
        # Calculate weighted average
        total_score = 0.0
        count = 0
        for bench in relevant_benchmarks:
            if bench in scores:
                total_score += scores[bench]
                count += 1
        
        return total_score / count if count > 0 else 0.0
    
    def calculate_rankings(self) -> dict[str, list[ModelRanking]]:
        """
        Calculate model rankings for each role based on:
        - Public benchmark scores (40%)
        - Local micro-bench scores (40%)
        - Latency (10%)
        - Reliability (10%)
        """
        rankings = {}
        roles = ["analyst", "pm", "architect", "po", "sm", "dev", "qa"]
        
        for role in roles:
            role_results = [r for r in self.results if r.role == role]
            
            # Group by model and provider
            model_stats: dict[tuple[str, str], dict] = {}
            
            for r in role_results:
                key = (r.model, r.provider)
                if key not in model_stats:
                    model_stats[key] = {
                        "scores": [],
                        "latencies": [],
                        "passed": 0,
                        "total": 0,
                    }
                
                model_stats[key]["scores"].append(r.score)
                model_stats[key]["latencies"].append(r.latency_ms)
                model_stats[key]["total"] += 1
                if r.passed:
                    model_stats[key]["passed"] += 1
            
            role_rankings = []
            for (model, provider), stats in model_stats.items():
                if not stats["scores"]:
                    continue
                
                local_score = sum(stats["scores"]) / len(stats["scores"])
                public_score = self.get_public_score(model, role)
                latency_avg = sum(stats["latencies"]) / len(stats["latencies"]) if stats["latencies"] else 0
                reliability = stats["passed"] / stats["total"] if stats["total"] > 0 else 0
                
                # Calculate composite score
                # 40% public, 40% local, 10% latency (inverse), 10% reliability
                latency_score = max(0, 100 - (latency_avg / 100))  # Lower is better
                
                composite = (
                    public_score * 0.4 +
                    local_score * 0.4 +
                    latency_score * 0.1 +
                    reliability * 100 * 0.1
                )
                
                role_rankings.append(ModelRanking(
                    role=role,
                    model=model,
                    provider=provider,
                    score=composite,
                    public_score=public_score,
                    local_score=local_score,
                    latency_avg_ms=int(latency_avg),
                    reliability=reliability,
                    last_bench=datetime.now(),
                ))
            
            # Sort by composite score
            role_rankings.sort(key=lambda x: -x.score)
            rankings[role] = role_rankings
        
        self.rankings = rankings
        self._save_rankings()
        return rankings
    
    def get_best_model(self, role: str, provider: str = "any") -> Optional[ModelRanking]:
        """Get best model for a role, optionally filtered by provider."""
        role_rankings = self.rankings.get(role, [])
        
        if provider != "any":
            role_rankings = [r for r in role_rankings if r.provider == provider]
        
        return role_rankings[0] if role_rankings else None
    
    def should_run_bench(self, provider: str = "local") -> bool:
        """Check if benchmark should be run (monthly schedule)."""
        if not self.schedule_path.exists():
            return True
        
        try:
            data = json.loads(self.schedule_path.read_text(encoding="utf-8"))
            last_run = data.get(provider)
            if not last_run:
                return True
            
            last_date = datetime.fromisoformat(last_run)
            days_since = (datetime.now() - last_date).days
            
            return days_since >= 30  # Monthly
            
        except Exception:
            return True
    
    def mark_bench_complete(self, provider: str = "local") -> None:
        """Mark benchmark as complete for scheduling."""
        try:
            data = {}
            if self.schedule_path.exists():
                data = json.loads(self.schedule_path.read_text(encoding="utf-8"))
            
            data[provider] = datetime.now().isoformat()
            
            self.schedule_path.write_text(
                json.dumps(data, indent=2),
                encoding="utf-8",
            )
        except Exception as e:
            logger.warning(f"Failed to save bench schedule: {e}")
    
    def get_comparison(self, role: str) -> dict[str, Any]:
        """Get comparison of local vs remote providers for a role."""
        rankings = self.rankings.get(role, [])
        
        local_models = [r for r in rankings if r.provider == "local"]
        remote_models = [r for r in rankings if r.provider != "local"]
        
        best_local = local_models[0] if local_models else None
        best_remote = remote_models[0] if remote_models else None
        
        comparison = {
            "role": role,
            "best_local": {
                "model": best_local.model if best_local else None,
                "score": best_local.score if best_local else 0,
                "latency_ms": best_local.latency_avg_ms if best_local else 0,
            },
            "best_remote": {
                "model": best_remote.model if best_remote else None,
                "provider": best_remote.provider if best_remote else None,
                "score": best_remote.score if best_remote else 0,
                "latency_ms": best_remote.latency_avg_ms if best_remote else 0,
            },
            "recommendation": "local",
            "score_diff": 0,
        }
        
        if best_local and best_remote:
            score_diff = best_remote.score - best_local.score
            comparison["score_diff"] = score_diff
            
            # Use remote only if significantly better (>20%)
            threshold = best_local.score * (self.cfg.hybrid_routing.percent_threshold - 1)
            if score_diff > threshold:
                comparison["recommendation"] = best_remote.provider
        
        return comparison
