# src/freya/hybrid_router.py
"""
Hybrid Router for Freya 2.1
===========================

Implements intelligent routing between local (Ollama/Llama.cpp) and remote
(HuggingFace, Together AI, Groq) LLM providers.

Features:
- Local-first execution with optional remote validation
- Multi-provider failover with health monitoring
- Quota tracking and rotation
- Benchmark-based quality scoring
- Downtime detection and automatic fallback

References:
- Ollama: https://ollama.ai/docs
- HuggingFace: https://huggingface.co/docs/inference-providers/en/pricing
- Together AI: https://docs.together.ai/docs/rate-limits
- Groq: https://console.groq.com/docs/rate-limits
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

import requests

from .config import (
    HYBRID_ROUTING_CONFIG,
    LOCAL_RUNTIMES,
    PROVIDERS,
    FreyaConfig,
    HybridRoutingConfig,
)
from .ollama_client import OllamaClient, OllamaGenerateResult

logger = logging.getLogger(__name__)


class ProviderType(str, Enum):
    """Provider type enumeration."""
    LOCAL = "local"
    HF = "hf"
    TOGETHER = "together"
    GROQ = "groq"


class ProviderStatus(str, Enum):
    """Provider health status."""
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    RATE_LIMITED = "rate_limited"
    UNKNOWN = "unknown"


@dataclass
class ProviderHealth:
    """Provider health tracking."""
    provider: str
    status: ProviderStatus = ProviderStatus.UNKNOWN
    last_check: datetime = field(default_factory=datetime.now)
    last_success: Optional[datetime] = None
    last_error: Optional[str] = None
    consecutive_failures: int = 0
    latency_ms: int = 0
    
    def is_healthy(self) -> bool:
        return self.status in (ProviderStatus.ONLINE, ProviderStatus.DEGRADED)
    
    def mark_success(self, latency_ms: int = 0) -> None:
        self.status = ProviderStatus.ONLINE
        self.last_check = datetime.now()
        self.last_success = datetime.now()
        self.consecutive_failures = 0
        self.latency_ms = latency_ms
        self.last_error = None
    
    def mark_failure(self, error: str, max_retries: int = 3) -> None:
        self.last_check = datetime.now()
        self.consecutive_failures += 1
        self.last_error = error
        if self.consecutive_failures >= max_retries:
            self.status = ProviderStatus.OFFLINE
        else:
            self.status = ProviderStatus.DEGRADED
    
    def mark_rate_limited(self) -> None:
        self.status = ProviderStatus.RATE_LIMITED
        self.last_check = datetime.now()


@dataclass
class QuotaInfo:
    """Provider quota tracking."""
    provider: str
    requests_remaining: int = -1  # -1 = unlimited/unknown
    tokens_remaining: int = -1
    reset_time: Optional[datetime] = None
    last_update: datetime = field(default_factory=datetime.now)
    
    def has_quota(self, min_requests: int = 10) -> bool:
        if self.requests_remaining == -1:
            return True  # Unknown = assume available
        return self.requests_remaining >= min_requests
    
    def is_stale(self, cache_seconds: int = 300) -> bool:
        return (datetime.now() - self.last_update).total_seconds() > cache_seconds


@dataclass
class RoutingDecision:
    """Result of routing decision."""
    provider: str
    provider_type: ProviderType
    model: str
    reason: str
    local_score: Optional[float] = None
    remote_score: Optional[float] = None
    fallback_used: bool = False


@dataclass
class HybridGenerateResult:
    """Result from hybrid generation."""
    provider: str
    provider_type: ProviderType
    model: str
    response: str
    duration_ms: int
    tokens_estimated: int = 0
    local_validated: bool = False
    remote_validated: bool = False


class RemoteProviderClient:
    """Client for remote LLM providers (HF, Together, Groq)."""
    
    def __init__(self, provider_id: str, config: dict[str, Any], api_key: str):
        self.provider_id = provider_id
        self.config = config
        self.api_key = api_key
        self.base_url = config["base_url"]
        self.name = config["name"]
        
    def _headers(self) -> dict[str, str]:
        """Get headers for API requests."""
        if self.provider_id == "hf":
            return {"Authorization": f"Bearer {self.api_key}"}
        elif self.provider_id == "together":
            return {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
        elif self.provider_id == "groq":
            return {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
        return {}
    
    def health_check(self, timeout: int = 5) -> tuple[bool, int]:
        """Check if provider is reachable. Returns (is_healthy, latency_ms)."""
        try:
            t0 = time.time()
            
            if self.provider_id == "hf":
                # HuggingFace: check inference endpoint
                r = requests.get(
                    "https://api-inference.huggingface.co/status",
                    headers=self._headers(),
                    timeout=timeout,
                )
            elif self.provider_id == "together":
                # Together AI: check models endpoint
                r = requests.get(
                    f"{self.base_url}/models",
                    headers=self._headers(),
                    timeout=timeout,
                )
            elif self.provider_id == "groq":
                # Groq: check models endpoint
                r = requests.get(
                    f"{self.base_url}/models",
                    headers=self._headers(),
                    timeout=timeout,
                )
            else:
                return False, 0
            
            latency_ms = int((time.time() - t0) * 1000)
            return r.status_code in (200, 401), latency_ms  # 401 = valid endpoint, just auth issue
            
        except Exception as e:
            logger.warning(f"Health check failed for {self.name}: {e}")
            return False, 0
    
    def check_quota(self) -> QuotaInfo:
        """Check remaining quota from provider."""
        quota = QuotaInfo(provider=self.provider_id)
        
        try:
            # Most providers include quota in response headers
            # This is a simplified check - real implementation would
            # track usage locally and/or call provider-specific endpoints
            
            if self.provider_id == "groq":
                # Groq includes rate limit info in headers
                # We can't check without making a request
                rate_limits = self.config.get("rate_limits", {})
                quota.requests_remaining = rate_limits.get("requests_per_day", 14400)
                quota.tokens_remaining = rate_limits.get("tokens_per_day", 500000)
                
            elif self.provider_id == "together":
                # Together AI - check based on tier
                rate_limits = self.config.get("rate_limits", {})
                quota.requests_remaining = rate_limits.get("requests_per_minute", 600) * 60
                quota.tokens_remaining = rate_limits.get("tokens_per_minute", 180000) * 60
                
            elif self.provider_id == "hf":
                # HuggingFace - free tier is very limited
                rate_limits = self.config.get("rate_limits", {})
                quota.requests_remaining = rate_limits.get("requests_per_minute", 60) * 60
                quota.tokens_remaining = rate_limits.get("tokens_per_minute", 50000) * 60
                
        except Exception as e:
            logger.warning(f"Failed to check quota for {self.name}: {e}")
            
        quota.last_update = datetime.now()
        return quota
    
    def generate(
        self,
        model: str,
        prompt: str,
        system: str = "",
        temperature: float = 0.0,
        max_tokens: int = 1024,
        timeout_sec: int = 60,
    ) -> HybridGenerateResult:
        """Generate response from remote provider."""
        t0 = time.time()
        
        try:
            if self.provider_id == "hf":
                response = self._generate_hf(model, prompt, system, temperature, max_tokens, timeout_sec)
            elif self.provider_id == "together":
                response = self._generate_openai_compat(model, prompt, system, temperature, max_tokens, timeout_sec)
            elif self.provider_id == "groq":
                response = self._generate_openai_compat(model, prompt, system, temperature, max_tokens, timeout_sec)
            else:
                raise ValueError(f"Unknown provider: {self.provider_id}")
            
            duration_ms = int((time.time() - t0) * 1000)
            tokens_est = len(response.split()) * 2  # Rough estimate
            
            return HybridGenerateResult(
                provider=self.provider_id,
                provider_type=ProviderType(self.provider_id),
                model=model,
                response=response,
                duration_ms=duration_ms,
                tokens_estimated=tokens_est,
                remote_validated=True,
            )
            
        except Exception as e:
            logger.error(f"Remote generation failed for {self.name}: {e}")
            raise
    
    def _generate_hf(
        self,
        model: str,
        prompt: str,
        system: str,
        temperature: float,
        max_tokens: int,
        timeout_sec: int,
    ) -> str:
        """Generate using HuggingFace Inference API."""
        url = f"https://api-inference.huggingface.co/models/{model}"
        
        # Build prompt with system message
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        
        payload = {
            "inputs": full_prompt,
            "parameters": {
                "temperature": temperature if temperature > 0 else 0.01,
                "max_new_tokens": max_tokens,
                "return_full_text": False,
            },
        }
        
        r = requests.post(
            url,
            headers=self._headers(),
            json=payload,
            timeout=timeout_sec,
        )
        r.raise_for_status()
        
        result = r.json()
        if isinstance(result, list) and len(result) > 0:
            return result[0].get("generated_text", "")
        return ""
    
    def _generate_openai_compat(
        self,
        model: str,
        prompt: str,
        system: str,
        temperature: float,
        max_tokens: int,
        timeout_sec: int,
    ) -> str:
        """Generate using OpenAI-compatible API (Together, Groq)."""
        url = f"{self.base_url}/chat/completions"
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        r = requests.post(
            url,
            headers=self._headers(),
            json=payload,
            timeout=timeout_sec,
        )
        r.raise_for_status()
        
        result = r.json()
        choices = result.get("choices", [])
        if choices:
            return choices[0].get("message", {}).get("content", "")
        return ""


class HybridRouter:
    """
    Hybrid LLM Router for Freya 2.1.
    
    Implements intelligent routing between local and remote providers
    with health monitoring, quota management, and benchmark-based selection.
    """
    
    def __init__(
        self,
        cfg: FreyaConfig,
        local_client: OllamaClient,
        bench_scores: dict[str, list[Any]] | None = None,
    ):
        self.cfg = cfg
        self.local_client = local_client
        self.bench_scores = bench_scores or {}
        
        # Health tracking
        self.provider_health: dict[str, ProviderHealth] = {}
        self.provider_quotas: dict[str, QuotaInfo] = {}
        
        # Remote clients (lazy-initialized)
        self._remote_clients: dict[str, RemoteProviderClient] = {}
        
        # Usage tracking (persisted to disk)
        self.usage_path = cfg.cache_root / "hybrid_usage.json"
        self.usage_data = self._load_usage()
        
        # Initialize health status
        self._init_health_tracking()
    
    def _init_health_tracking(self) -> None:
        """Initialize health tracking for all providers."""
        # Local provider
        self.provider_health["local"] = ProviderHealth(provider="local")
        
        # Remote providers
        for provider_id in PROVIDERS:
            self.provider_health[provider_id] = ProviderHealth(provider=provider_id)
            self.provider_quotas[provider_id] = QuotaInfo(provider=provider_id)
    
    def _get_remote_client(self, provider_id: str) -> Optional[RemoteProviderClient]:
        """Get or create remote client for provider."""
        if provider_id not in PROVIDERS:
            return None
        
        if provider_id not in self._remote_clients:
            config = PROVIDERS[provider_id]
            
            # Get API key from config or environment
            api_key = ""
            if provider_id == "hf":
                api_key = self.cfg.providers.hf_api_key or os.environ.get("HF_API_KEY", "")
            elif provider_id == "together":
                api_key = self.cfg.providers.together_api_key or os.environ.get("TOGETHER_API_KEY", "")
            elif provider_id == "groq":
                api_key = self.cfg.providers.groq_api_key or os.environ.get("GROQ_API_KEY", "")
            
            if not api_key:
                logger.warning(f"No API key configured for {config['name']}")
                return None
            
            self._remote_clients[provider_id] = RemoteProviderClient(provider_id, config, api_key)
        
        return self._remote_clients[provider_id]
    
    def _load_usage(self) -> dict[str, Any]:
        """Load usage data from disk."""
        if self.usage_path.exists():
            try:
                return json.loads(self.usage_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"daily": {}, "monthly": {}, "last_reset": datetime.now().isoformat()}
    
    def _save_usage(self) -> None:
        """Save usage data to disk."""
        try:
            self.usage_path.parent.mkdir(parents=True, exist_ok=True)
            self.usage_path.write_text(
                json.dumps(self.usage_data, indent=2, default=str),
                encoding="utf-8",
            )
        except Exception as e:
            logger.warning(f"Failed to save usage data: {e}")
    
    def _track_usage(self, provider: str, tokens: int) -> None:
        """Track usage for a provider."""
        today = datetime.now().strftime("%Y-%m-%d")
        month = datetime.now().strftime("%Y-%m")
        
        if "daily" not in self.usage_data:
            self.usage_data["daily"] = {}
        if "monthly" not in self.usage_data:
            self.usage_data["monthly"] = {}
        
        if today not in self.usage_data["daily"]:
            self.usage_data["daily"][today] = {}
        if month not in self.usage_data["monthly"]:
            self.usage_data["monthly"][month] = {}
        
        if provider not in self.usage_data["daily"][today]:
            self.usage_data["daily"][today][provider] = {"requests": 0, "tokens": 0}
        if provider not in self.usage_data["monthly"][month]:
            self.usage_data["monthly"][month][provider] = {"requests": 0, "tokens": 0}
        
        self.usage_data["daily"][today][provider]["requests"] += 1
        self.usage_data["daily"][today][provider]["tokens"] += tokens
        self.usage_data["monthly"][month][provider]["requests"] += 1
        self.usage_data["monthly"][month][provider]["tokens"] += tokens
        
        self._save_usage()
    
    def check_local_health(self) -> bool:
        """Check if local Ollama is healthy."""
        try:
            t0 = time.time()
            tags = self.local_client.tags()
            latency_ms = int((time.time() - t0) * 1000)
            
            if tags:
                self.provider_health["local"].mark_success(latency_ms)
                return True
            else:
                self.provider_health["local"].mark_failure("No models available")
                return False
                
        except Exception as e:
            self.provider_health["local"].mark_failure(str(e))
            return False
    
    def check_provider_health(self, provider_id: str) -> bool:
        """Check if a remote provider is healthy."""
        client = self._get_remote_client(provider_id)
        if not client:
            return False
        
        healthy, latency_ms = client.health_check(
            timeout=self.cfg.hybrid_routing.health_timeout_sec
        )
        
        if healthy:
            self.provider_health[provider_id].mark_success(latency_ms)
        else:
            self.provider_health[provider_id].mark_failure(
                "Health check failed",
                max_retries=self.cfg.hybrid_routing.max_retries,
            )
        
        return healthy
    
    def check_quota(self, provider_id: str) -> bool:
        """Check if provider has remaining quota."""
        if provider_id == "local":
            return True
        
        quota = self.provider_quotas.get(provider_id)
        if not quota or quota.is_stale(self.cfg.hybrid_routing.quota_cache_sec):
            client = self._get_remote_client(provider_id)
            if client:
                quota = client.check_quota()
                self.provider_quotas[provider_id] = quota
        
        return quota.has_quota() if quota else False
    
    def select_provider(
        self,
        role: str,
        local_score: float | None = None,
        task_complexity: str = "normal",
    ) -> RoutingDecision:
        """
        Select the best provider for a task.
        
        Process:
        1. Check local availability and score
        2. If local score >= threshold, use local
        3. Otherwise, evaluate remote providers
        4. Fall back through chain if needed
        """
        if not self.cfg.hybrid_routing.enabled:
            return RoutingDecision(
                provider="local",
                provider_type=ProviderType.LOCAL,
                model=self._get_local_model(role),
                reason="Hybrid routing disabled",
            )
        
        # Check local health first
        local_healthy = self.check_local_health()
        local_model = self._get_local_model(role)
        
        # If local score is good enough, use local
        if local_score is not None and local_score >= self.cfg.hybrid_routing.local_min_score:
            if local_healthy:
                return RoutingDecision(
                    provider="local",
                    provider_type=ProviderType.LOCAL,
                    model=local_model,
                    reason=f"Local score ({local_score}) meets threshold ({self.cfg.hybrid_routing.local_min_score})",
                    local_score=local_score,
                )
        
        # Try fallback chain
        for provider_id in self.cfg.hybrid_routing.fallback_chain:
            if provider_id == "local":
                if local_healthy:
                    return RoutingDecision(
                        provider="local",
                        provider_type=ProviderType.LOCAL,
                        model=local_model,
                        reason="Using local (fallback chain)",
                        local_score=local_score,
                        fallback_used=True,
                    )
                continue
            
            # Check provider config
            if provider_id not in PROVIDERS or not PROVIDERS[provider_id].get("enabled", False):
                continue
            
            # Check health and quota
            if not self.provider_health.get(provider_id, ProviderHealth(provider_id)).is_healthy():
                if not self.check_provider_health(provider_id):
                    continue
            
            if not self.check_quota(provider_id):
                continue
            
            # Provider is available
            remote_model = PROVIDERS[provider_id]["models"].get(role, "")
            if not remote_model:
                continue
            
            return RoutingDecision(
                provider=provider_id,
                provider_type=ProviderType(provider_id),
                model=remote_model,
                reason=f"Using {PROVIDERS[provider_id]['name']} (priority: {PROVIDERS[provider_id]['priority']})",
                local_score=local_score,
            )
        
        # Ultimate fallback to local
        return RoutingDecision(
            provider="local",
            provider_type=ProviderType.LOCAL,
            model=local_model,
            reason="Fallback to local (all remote providers unavailable)",
            local_score=local_score,
            fallback_used=True,
        )
    
    def _get_local_model(self, role: str) -> str:
        """Get local model for role from config or bench scores."""
        # Check bench scores first
        if role in self.bench_scores and self.bench_scores[role]:
            return self.bench_scores[role][0].model
        
        # Fall back to config
        return getattr(self.cfg.models, role, "llama3.1:8b")
    
    def generate(
        self,
        role: str,
        prompt: str,
        system: str = "",
        temperature: float = 0.0,
        max_tokens: int = 1024,
        local_score: float | None = None,
        force_provider: str | None = None,
    ) -> HybridGenerateResult:
        """
        Generate response using hybrid routing.
        
        Args:
            role: BMAD role (analyst, pm, architect, etc.)
            prompt: User prompt
            system: System prompt
            temperature: Sampling temperature
            max_tokens: Max tokens to generate
            local_score: Pre-computed local quality score
            force_provider: Force specific provider (bypass routing)
        
        Returns:
            HybridGenerateResult with response and metadata
        """
        # Select provider
        if force_provider:
            if force_provider == "local":
                decision = RoutingDecision(
                    provider="local",
                    provider_type=ProviderType.LOCAL,
                    model=self._get_local_model(role),
                    reason="Forced local",
                )
            else:
                decision = RoutingDecision(
                    provider=force_provider,
                    provider_type=ProviderType(force_provider),
                    model=PROVIDERS.get(force_provider, {}).get("models", {}).get(role, ""),
                    reason=f"Forced {force_provider}",
                )
        else:
            decision = self.select_provider(role, local_score)
        
        logger.info(f"Routing decision for {role}: {decision.provider} ({decision.reason})")
        
        try:
            if decision.provider_type == ProviderType.LOCAL:
                result = self._generate_local(decision.model, prompt, system, temperature, max_tokens)
            else:
                result = self._generate_remote(decision.provider, decision.model, prompt, system, temperature, max_tokens)
            
            # Track usage
            self._track_usage(decision.provider, result.tokens_estimated)
            
            return result
            
        except Exception as e:
            logger.error(f"Generation failed for {decision.provider}: {e}")
            
            # Mark provider as failed and retry
            if decision.provider != "local":
                self.provider_health[decision.provider].mark_failure(str(e))
                
                # Try fallback
                fallback = self.select_provider(role, local_score)
                if fallback.provider != decision.provider:
                    logger.info(f"Retrying with fallback: {fallback.provider}")
                    return self.generate(
                        role, prompt, system, temperature, max_tokens,
                        local_score, force_provider=fallback.provider,
                    )
            
            raise
    
    def _generate_local(
        self,
        model: str,
        prompt: str,
        system: str,
        temperature: float,
        max_tokens: int,
    ) -> HybridGenerateResult:
        """Generate using local Ollama."""
        result = self.local_client.generate(
            model=model,
            prompt=prompt,
            system=system,
            temperature=temperature,
            options_extra={"num_predict": max_tokens},
        )
        
        return HybridGenerateResult(
            provider="local",
            provider_type=ProviderType.LOCAL,
            model=model,
            response=result.response,
            duration_ms=result.duration_ms,
            tokens_estimated=len(result.response.split()) * 2,
            local_validated=True,
        )
    
    def _generate_remote(
        self,
        provider_id: str,
        model: str,
        prompt: str,
        system: str,
        temperature: float,
        max_tokens: int,
    ) -> HybridGenerateResult:
        """Generate using remote provider."""
        client = self._get_remote_client(provider_id)
        if not client:
            raise ValueError(f"No client available for {provider_id}")
        
        return client.generate(
            model=model,
            prompt=prompt,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    
    def evaluate_need_validation(self, prompt: str, role: str) -> bool:
        """
        Evaluate if a task needs remote validation.
        
        Uses a simple local prompt to determine if the task is complex
        enough to warrant remote validation.
        """
        if not self.cfg.hybrid_routing.enabled:
            return False
        
        # Simple heuristics
        complexity_indicators = [
            "complex", "critical", "important", "security", "production",
            "architecture", "design", "review", "analyze", "comprehensive",
        ]
        
        prompt_lower = prompt.lower()
        for indicator in complexity_indicators:
            if indicator in prompt_lower:
                return True
        
        # Check role-based complexity
        high_complexity_roles = ["architect", "dev", "qa"]
        if role in high_complexity_roles:
            return True
        
        return False
    
    def get_health_status(self) -> dict[str, Any]:
        """Get health status for all providers."""
        status = {}
        
        for provider_id, health in self.provider_health.items():
            status[provider_id] = {
                "status": health.status.value,
                "last_check": health.last_check.isoformat() if health.last_check else None,
                "last_success": health.last_success.isoformat() if health.last_success else None,
                "last_error": health.last_error,
                "consecutive_failures": health.consecutive_failures,
                "latency_ms": health.latency_ms,
            }
        
        return status
    
    def get_usage_stats(self) -> dict[str, Any]:
        """Get usage statistics."""
        return {
            "daily": self.usage_data.get("daily", {}),
            "monthly": self.usage_data.get("monthly", {}),
            "provider_health": self.get_health_status(),
        }
