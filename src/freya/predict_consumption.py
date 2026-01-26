# src/freya/predict_consumption.py
"""
Consumption Prediction for Freya 2.1
====================================

Machine learning model to predict token consumption and costs
based on historical usage data.

Features:
- Linear regression model (scikit-learn)
- Training on historical logs
- FastAPI endpoint integration
- Real-time prediction for routing decisions

References:
- scikit-learn: https://scikit-learn.org/stable/modules/linear_model.html
"""

from __future__ import annotations

import json
import logging
import pickle
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)

# Lazy import of sklearn to avoid hard dependency
_sklearn_available = False
_LinearRegression = None
_StandardScaler = None

def _ensure_sklearn():
    """Lazy load sklearn to avoid import errors if not installed."""
    global _sklearn_available, _LinearRegression, _StandardScaler
    if _sklearn_available:
        return True
    
    try:
        from sklearn.linear_model import LinearRegression
        from sklearn.preprocessing import StandardScaler
        _LinearRegression = LinearRegression
        _StandardScaler = StandardScaler
        _sklearn_available = True
        return True
    except ImportError:
        logger.warning("scikit-learn not installed. Prediction features disabled.")
        return False


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class UsageRecord:
    """A single usage record for training."""
    timestamp: datetime
    role: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    provider: str
    model: str
    latency_ms: int
    cost_usd: float = 0.0


@dataclass
class PredictionResult:
    """Result of a consumption prediction."""
    estimated_tokens: int
    estimated_cost_usd: float
    estimated_latency_ms: int
    confidence: float
    provider_recommendation: str
    breakdown: dict[str, Any]


# =============================================================================
# COST ESTIMATION CONSTANTS
# =============================================================================

# Approximate costs per 1M tokens (USD) - Updated Jan 2026
PROVIDER_COSTS: dict[str, dict[str, float]] = {
    "local": {
        "input": 0.0,  # Free (electricity only)
        "output": 0.0,
    },
    "hf": {
        "input": 0.10,  # HuggingFace varies by model
        "output": 0.10,
    },
    "together": {
        "input": 0.20,  # Together AI average
        "output": 0.20,
    },
    "groq": {
        "input": 0.05,  # Groq is very cheap
        "output": 0.10,
    },
}

# Role complexity factors (affects token estimation)
ROLE_COMPLEXITY: dict[str, float] = {
    "analyst": 1.2,
    "pm": 1.3,
    "architect": 1.5,
    "po": 1.2,
    "sm": 1.1,
    "dev": 2.0,  # Code generation tends to be longer
    "qa": 1.4,
}


# =============================================================================
# PREDICTOR CLASS
# =============================================================================

class ConsumptionPredictor:
    """
    Predicts token consumption and costs using machine learning.
    """
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.model_path = cache_dir / "consumption_model.pkl"
        self.scaler_path = cache_dir / "consumption_scaler.pkl"
        self.history_path = cache_dir / "usage_history.json"
        
        self.model = None
        self.scaler = None
        self.history: list[UsageRecord] = []
        
        # Load existing data
        self._load_history()
        self._load_model()
    
    def _load_history(self) -> None:
        """Load usage history from disk."""
        if not self.history_path.exists():
            return
        
        try:
            data = json.loads(self.history_path.read_text(encoding="utf-8"))
            self.history = [
                UsageRecord(
                    timestamp=datetime.fromisoformat(r["timestamp"]),
                    role=r["role"],
                    prompt_tokens=r["prompt_tokens"],
                    completion_tokens=r["completion_tokens"],
                    total_tokens=r["total_tokens"],
                    provider=r["provider"],
                    model=r["model"],
                    latency_ms=r["latency_ms"],
                    cost_usd=r.get("cost_usd", 0.0),
                )
                for r in data
            ]
            logger.info(f"Loaded {len(self.history)} usage records")
        except Exception as e:
            logger.warning(f"Failed to load usage history: {e}")
    
    def _save_history(self) -> None:
        """Save usage history to disk."""
        try:
            data = [
                {
                    "timestamp": r.timestamp.isoformat(),
                    "role": r.role,
                    "prompt_tokens": r.prompt_tokens,
                    "completion_tokens": r.completion_tokens,
                    "total_tokens": r.total_tokens,
                    "provider": r.provider,
                    "model": r.model,
                    "latency_ms": r.latency_ms,
                    "cost_usd": r.cost_usd,
                }
                for r in self.history
            ]
            self.history_path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as e:
            logger.warning(f"Failed to save usage history: {e}")
    
    def _load_model(self) -> None:
        """Load trained model from disk."""
        if not _ensure_sklearn():
            return
        
        if self.model_path.exists() and self.scaler_path.exists():
            try:
                with open(self.model_path, "rb") as f:
                    self.model = pickle.load(f)
                with open(self.scaler_path, "rb") as f:
                    self.scaler = pickle.load(f)
                logger.info("Loaded consumption prediction model")
            except Exception as e:
                logger.warning(f"Failed to load model: {e}")
    
    def _save_model(self) -> None:
        """Save trained model to disk."""
        if self.model is None or self.scaler is None:
            return
        
        try:
            with open(self.model_path, "wb") as f:
                pickle.dump(self.model, f)
            with open(self.scaler_path, "wb") as f:
                pickle.dump(self.scaler, f)
            logger.info("Saved consumption prediction model")
        except Exception as e:
            logger.warning(f"Failed to save model: {e}")
    
    def add_record(self, record: UsageRecord) -> None:
        """Add a usage record to history."""
        # Calculate cost if not provided
        if record.cost_usd == 0.0:
            costs = PROVIDER_COSTS.get(record.provider, PROVIDER_COSTS["local"])
            record.cost_usd = (
                record.prompt_tokens / 1_000_000 * costs["input"] +
                record.completion_tokens / 1_000_000 * costs["output"]
            )
        
        self.history.append(record)
        self._save_history()
        
        # Retrain model periodically (every 100 records)
        if len(self.history) % 100 == 0:
            self.train()
    
    def train(self) -> bool:
        """Train the prediction model on historical data."""
        if not _ensure_sklearn():
            return False
        
        if len(self.history) < 10:
            logger.warning("Not enough data to train model (need at least 10 records)")
            return False
        
        try:
            # Prepare features
            # Features: [role_encoded, prompt_len_bucket, provider_encoded, hour_of_day]
            X = []
            y = []
            
            role_map = {r: i for i, r in enumerate(ROLE_COMPLEXITY.keys())}
            provider_map = {"local": 0, "hf": 1, "together": 2, "groq": 3}
            
            for record in self.history:
                role_idx = role_map.get(record.role, 0)
                provider_idx = provider_map.get(record.provider, 0)
                hour = record.timestamp.hour
                prompt_bucket = min(record.prompt_tokens // 100, 50)  # Buckets of 100 tokens
                
                X.append([role_idx, prompt_bucket, provider_idx, hour])
                y.append(record.total_tokens)
            
            X = np.array(X)
            y = np.array(y)
            
            # Scale features
            self.scaler = _StandardScaler()
            X_scaled = self.scaler.fit_transform(X)
            
            # Train model
            self.model = _LinearRegression()
            self.model.fit(X_scaled, y)
            
            # Calculate R² score
            score = self.model.score(X_scaled, y)
            logger.info(f"Trained consumption model with R² = {score:.3f}")
            
            self._save_model()
            return True
            
        except Exception as e:
            logger.error(f"Failed to train model: {e}")
            return False
    
    def predict(
        self,
        role: str,
        prompt_tokens: int,
        provider: str = "local",
    ) -> PredictionResult:
        """
        Predict token consumption and cost.
        
        Uses ML model if available, otherwise falls back to heuristics.
        """
        # Fallback prediction using heuristics
        complexity = ROLE_COMPLEXITY.get(role, 1.0)
        base_output = int(prompt_tokens * 1.5 * complexity)
        
        if self.model is not None and self.scaler is not None and _ensure_sklearn():
            try:
                # Prepare features
                role_map = {r: i for i, r in enumerate(ROLE_COMPLEXITY.keys())}
                provider_map = {"local": 0, "hf": 1, "together": 2, "groq": 3}
                
                role_idx = role_map.get(role, 0)
                provider_idx = provider_map.get(provider, 0)
                hour = datetime.now().hour
                prompt_bucket = min(prompt_tokens // 100, 50)
                
                X = np.array([[role_idx, prompt_bucket, provider_idx, hour]])
                X_scaled = self.scaler.transform(X)
                
                predicted_tokens = int(self.model.predict(X_scaled)[0])
                confidence = 0.8  # Model prediction
                
                # Ensure reasonable bounds
                predicted_tokens = max(prompt_tokens, min(predicted_tokens, prompt_tokens * 10))
                
            except Exception as e:
                logger.warning(f"Model prediction failed: {e}")
                predicted_tokens = base_output
                confidence = 0.5  # Heuristic fallback
        else:
            predicted_tokens = base_output
            confidence = 0.5  # Heuristic
        
        # Calculate cost
        costs = PROVIDER_COSTS.get(provider, PROVIDER_COSTS["local"])
        estimated_cost = (
            prompt_tokens / 1_000_000 * costs["input"] +
            predicted_tokens / 1_000_000 * costs["output"]
        )
        
        # Estimate latency based on provider
        # These are rough estimates based on typical performance
        latency_factors = {
            "local": 50,  # ~50ms per 100 tokens
            "hf": 100,
            "together": 80,
            "groq": 20,  # Groq is very fast
        }
        latency_factor = latency_factors.get(provider, 50)
        estimated_latency = int((predicted_tokens / 100) * latency_factor)
        
        # Provider recommendation
        best_provider = self._recommend_provider(role, prompt_tokens, predicted_tokens)
        
        return PredictionResult(
            estimated_tokens=predicted_tokens,
            estimated_cost_usd=estimated_cost,
            estimated_latency_ms=estimated_latency,
            confidence=confidence,
            provider_recommendation=best_provider,
            breakdown={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": predicted_tokens - prompt_tokens,
                "complexity_factor": complexity,
                "cost_per_1m_input": costs["input"],
                "cost_per_1m_output": costs["output"],
            },
        )
    
    def _recommend_provider(
        self,
        role: str,
        prompt_tokens: int,
        estimated_output: int,
    ) -> str:
        """Recommend the best provider based on cost/performance."""
        # Calculate costs for each provider
        provider_scores = {}
        
        for provider, costs in PROVIDER_COSTS.items():
            total_cost = (
                prompt_tokens / 1_000_000 * costs["input"] +
                estimated_output / 1_000_000 * costs["output"]
            )
            
            # Factor in performance (lower latency = higher score)
            latency_factors = {
                "local": 1.0,
                "hf": 0.7,
                "together": 0.8,
                "groq": 1.2,  # Bonus for speed
            }
            perf_factor = latency_factors.get(provider, 1.0)
            
            # Score: lower cost + higher performance = better
            # Invert cost so lower is better
            cost_score = 1.0 / (total_cost + 0.001)  # Avoid division by zero
            provider_scores[provider] = cost_score * perf_factor
        
        # Prefer local for most cases (free)
        provider_scores["local"] *= 1.5
        
        # Return best provider
        return max(provider_scores, key=provider_scores.get)
    
    def get_stats(self) -> dict[str, Any]:
        """Get usage statistics."""
        if not self.history:
            return {"total_records": 0, "has_model": False}
        
        # Group by provider
        by_provider = {}
        for record in self.history:
            if record.provider not in by_provider:
                by_provider[record.provider] = {
                    "count": 0,
                    "total_tokens": 0,
                    "total_cost": 0.0,
                }
            by_provider[record.provider]["count"] += 1
            by_provider[record.provider]["total_tokens"] += record.total_tokens
            by_provider[record.provider]["total_cost"] += record.cost_usd
        
        # Group by role
        by_role = {}
        for record in self.history:
            if record.role not in by_role:
                by_role[record.role] = {
                    "count": 0,
                    "avg_tokens": 0,
                }
            by_role[record.role]["count"] += 1
        
        # Calculate averages
        for role, data in by_role.items():
            role_records = [r for r in self.history if r.role == role]
            if role_records:
                data["avg_tokens"] = sum(r.total_tokens for r in role_records) / len(role_records)
        
        return {
            "total_records": len(self.history),
            "has_model": self.model is not None,
            "by_provider": by_provider,
            "by_role": by_role,
            "date_range": {
                "start": min(r.timestamp for r in self.history).isoformat() if self.history else None,
                "end": max(r.timestamp for r in self.history).isoformat() if self.history else None,
            },
        }


# =============================================================================
# FASTAPI ENDPOINT HELPERS
# =============================================================================

def create_predictor_from_config(cfg) -> ConsumptionPredictor:
    """Create predictor instance from FreyaConfig."""
    return ConsumptionPredictor(cfg.cache_root / "consumption")
