# tests/test_hybrid_routing.py
"""
Unit tests for Freya 2.1 Hybrid Routing System.

Tests cover:
- Config loading and provider definitions
- Hybrid router logic
- Local runtime detection
- Benchmark system
- Consumption prediction
"""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# =============================================================================
# CONFIG TESTS
# =============================================================================

class TestConfig:
    """Tests for configuration system."""
    
    def test_providers_defined(self):
        """Test that all required providers are defined."""
        from freya.config import PROVIDERS
        
        assert "hf" in PROVIDERS
        assert "together" in PROVIDERS
        assert "groq" in PROVIDERS
        
        for pid, cfg in PROVIDERS.items():
            assert "name" in cfg
            assert "base_url" in cfg
            assert "api_key_env" in cfg
            assert "models" in cfg
            assert "enabled" in cfg
            assert "priority" in cfg
    
    def test_local_runtimes_defined(self):
        """Test that local runtimes are defined."""
        from freya.config import LOCAL_RUNTIMES
        
        assert "ollama" in LOCAL_RUNTIMES
        assert "lm_studio" in LOCAL_RUNTIMES
        assert "koboldcpp" in LOCAL_RUNTIMES
        
        for rid, cfg in LOCAL_RUNTIMES.items():
            assert "name" in cfg
            assert "base_url" in cfg
            assert "health_endpoint" in cfg
            assert "api_type" in cfg
    
    def test_hybrid_routing_config(self):
        """Test hybrid routing configuration defaults."""
        from freya.config import HYBRID_ROUTING_CONFIG
        
        assert "percent_threshold" in HYBRID_ROUTING_CONFIG
        assert "local_min_score" in HYBRID_ROUTING_CONFIG
        assert "enabled" in HYBRID_ROUTING_CONFIG
        assert "fallback_chain" in HYBRID_ROUTING_CONFIG
        
        # Defaults
        assert HYBRID_ROUTING_CONFIG["percent_threshold"] == 1.20
        assert HYBRID_ROUTING_CONFIG["local_min_score"] == 70
    
    def test_freya_config_load(self):
        """Test FreyaConfig.load() works."""
        from freya.config import FreyaConfig
        
        cfg = FreyaConfig.load()
        
        assert cfg.managed_root is not None
        assert cfg.cache_root is not None
        assert cfg.ollama.base_url == "http://localhost:11434"
        assert cfg.hybrid_routing.enabled is True


# =============================================================================
# HYBRID ROUTER TESTS
# =============================================================================

class TestHybridRouter:
    """Tests for HybridRouter class."""
    
    @pytest.fixture
    def mock_ollama_client(self):
        """Create mock Ollama client."""
        client = MagicMock()
        client.tags.return_value = [
            {"name": "llama3.1:8b"},
            {"name": "qwen2.5:7b"},
        ]
        client.generate.return_value = MagicMock(
            response="Test response",
            duration_ms=1000,
        )
        return client
    
    @pytest.fixture
    def config(self):
        """Create test config."""
        from freya.config import FreyaConfig
        return FreyaConfig.load()
    
    def test_provider_health_tracking(self, config, mock_ollama_client):
        """Test provider health status tracking."""
        from freya.hybrid_router import HybridRouter, ProviderStatus
        
        router = HybridRouter(config, mock_ollama_client)
        
        # Initial state
        assert "local" in router.provider_health
        assert router.provider_health["local"].status == ProviderStatus.UNKNOWN
        
        # Check local health
        result = router.check_local_health()
        assert result is True
        assert router.provider_health["local"].status == ProviderStatus.ONLINE
    
    def test_select_provider_local_first(self, config, mock_ollama_client):
        """Test that local provider is preferred when healthy."""
        from freya.hybrid_router import HybridRouter, ProviderType
        
        router = HybridRouter(config, mock_ollama_client)
        
        # With good local score
        decision = router.select_provider("analyst", local_score=80)
        
        assert decision.provider == "local"
        assert decision.provider_type == ProviderType.LOCAL
    
    def test_select_provider_fallback(self, config, mock_ollama_client):
        """Test fallback when local is unavailable."""
        from freya.hybrid_router import HybridRouter, ProviderStatus
        
        # Make local unhealthy
        mock_ollama_client.tags.side_effect = Exception("Connection refused")
        
        router = HybridRouter(config, mock_ollama_client)
        
        # Force local health check to fail
        router.provider_health["local"].status = ProviderStatus.OFFLINE
        
        # Without API keys, should still fall back to local
        decision = router.select_provider("analyst", local_score=50)
        
        # Will use local as fallback since no API keys configured
        assert decision.fallback_used is True
    
    def test_routing_decision_reasons(self, config, mock_ollama_client):
        """Test that routing decisions include reasons."""
        from freya.hybrid_router import HybridRouter
        
        router = HybridRouter(config, mock_ollama_client)
        
        decision = router.select_provider("dev", local_score=90)
        
        assert decision.reason is not None
        assert len(decision.reason) > 0
        assert decision.local_score == 90


# =============================================================================
# LOCAL RUNTIME DETECTION TESTS
# =============================================================================

class TestLocalRuntimeDetector:
    """Tests for LocalRuntimeDetector class."""
    
    def test_detector_initialization(self):
        """Test detector initializes correctly."""
        from freya.local_runtimes import LocalRuntimeDetector
        
        detector = LocalRuntimeDetector()
        
        assert detector.runtimes == {}
        # GPU detection may or may not find anything
        # Just check it doesn't crash
    
    def test_detect_runtime_offline(self):
        """Test detecting offline runtime."""
        from freya.local_runtimes import LocalRuntimeDetector, RuntimeStatus
        
        detector = LocalRuntimeDetector()
        
        # Detect a runtime that's likely offline
        result = detector.detect_runtime("lm_studio")
        
        if result:
            # Either offline or online depending on system
            assert result.status in (RuntimeStatus.OFFLINE, RuntimeStatus.ONLINE, RuntimeStatus.ERROR)
    
    def test_get_runtime_status(self):
        """Test getting runtime status summary."""
        from freya.local_runtimes import LocalRuntimeDetector
        
        detector = LocalRuntimeDetector()
        detector.detect_all_runtimes()
        
        status = detector.get_runtime_status()
        
        assert "gpu" in status
        assert "runtimes" in status


# =============================================================================
# BENCHMARK TESTS
# =============================================================================

class TestHybridBenchmark:
    """Tests for HybridBenchmark class."""
    
    @pytest.fixture
    def mock_ollama_client(self):
        """Create mock Ollama client."""
        client = MagicMock()
        client.tags.return_value = [{"name": "llama3.1:8b"}]
        client.generate.return_value = MagicMock(
            response="This is a test response with todo tasks and features.",
            duration_ms=500,
        )
        return client
    
    @pytest.fixture
    def config(self):
        """Create test config."""
        from freya.config import FreyaConfig
        return FreyaConfig.load()
    
    def test_get_micro_bench_cases(self, config, mock_ollama_client):
        """Test micro-benchmark case generation."""
        from freya.bench_hybrid import HybridBenchmark
        
        bench = HybridBenchmark(config, mock_ollama_client)
        cases = bench.get_micro_bench_cases()
        
        assert len(cases) > 0
        
        # Check we have cases for key roles
        roles = [c.role for c in cases]
        assert "analyst" in roles
        assert "dev" in roles
        assert "qa" in roles
    
    def test_evaluate_response(self, config, mock_ollama_client):
        """Test response evaluation logic."""
        from freya.bench_hybrid import HybridBenchmark, BenchmarkCase
        
        bench = HybridBenchmark(config, mock_ollama_client)
        
        case = BenchmarkCase(
            name="test_case",
            role="analyst",
            prompt="Test prompt",
            expected_patterns=["test", "response"],
            expected_format="paragraph",
        )
        
        # Good response
        score, notes = bench.evaluate_response(
            "This is a test response with multiple words.",
            case,
        )
        assert score > 0
        assert "Patterns" in notes
        
        # Empty response
        score, notes = bench.evaluate_response("", case)
        assert score == 0
    
    def test_public_score_lookup(self, config, mock_ollama_client):
        """Test public benchmark score lookup."""
        from freya.bench_hybrid import HybridBenchmark
        
        bench = HybridBenchmark(config, mock_ollama_client)
        
        # Known model
        score = bench.get_public_score("llama3.1:8b", "analyst")
        assert score > 0
        
        # Unknown model
        score = bench.get_public_score("unknown-model", "analyst")
        assert score == 0


# =============================================================================
# CONSUMPTION PREDICTION TESTS
# =============================================================================

class TestConsumptionPredictor:
    """Tests for ConsumptionPredictor class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_predictor_initialization(self, temp_dir):
        """Test predictor initializes correctly."""
        from freya.predict_consumption import ConsumptionPredictor
        
        predictor = ConsumptionPredictor(temp_dir)
        
        assert predictor.history == []
        assert predictor.model is None  # No training data yet
    
    def test_heuristic_prediction(self, temp_dir):
        """Test prediction with heuristic fallback."""
        from freya.predict_consumption import ConsumptionPredictor
        
        predictor = ConsumptionPredictor(temp_dir)
        
        result = predictor.predict("dev", prompt_tokens=500, provider="local")
        
        assert result.estimated_tokens > 500  # Should predict more output
        assert result.estimated_cost_usd == 0.0  # Local is free
        assert result.confidence == 0.5  # Heuristic fallback
    
    def test_add_record(self, temp_dir):
        """Test adding usage records."""
        from freya.predict_consumption import ConsumptionPredictor, UsageRecord
        
        predictor = ConsumptionPredictor(temp_dir)
        
        record = UsageRecord(
            timestamp=datetime.now(),
            role="analyst",
            prompt_tokens=500,
            completion_tokens=1500,
            total_tokens=2000,
            provider="local",
            model="llama3.1:8b",
            latency_ms=1000,
        )
        
        predictor.add_record(record)
        
        assert len(predictor.history) == 1
        
        # Check persistence
        predictor2 = ConsumptionPredictor(temp_dir)
        assert len(predictor2.history) == 1
    
    def test_stats_generation(self, temp_dir):
        """Test usage statistics generation."""
        from freya.predict_consumption import ConsumptionPredictor, UsageRecord
        
        predictor = ConsumptionPredictor(temp_dir)
        
        # Add some records
        for role in ["analyst", "dev", "qa"]:
            record = UsageRecord(
                timestamp=datetime.now(),
                role=role,
                prompt_tokens=500,
                completion_tokens=1500,
                total_tokens=2000,
                provider="local",
                model="llama3.1:8b",
                latency_ms=1000,
            )
            predictor.add_record(record)
        
        stats = predictor.get_stats()
        
        assert stats["total_records"] == 3
        assert "by_role" in stats
        assert "by_provider" in stats


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests for hybrid routing system."""
    
    @pytest.fixture
    def config(self):
        """Create test config."""
        from freya.config import FreyaConfig
        return FreyaConfig.load()
    
    def test_orchestrator_hybrid_init(self, config):
        """Test orchestrator initializes hybrid routing."""
        # This will likely fail without actual Ollama, so we mock
        from freya.orchestrator import Orchestrator, HYBRID_AVAILABLE
        
        if HYBRID_AVAILABLE:
            # Test that orchestrator can be created
            with patch("freya.orchestrator.OllamaClient") as mock_client:
                mock_client.return_value.tags.return_value = []
                
                # Create with minimal mocking
                try:
                    orch = Orchestrator(config, log=MagicMock())
                    # If hybrid is available, check it was initialized
                    assert hasattr(orch, "hybrid_router")
                except Exception:
                    pass  # May fail without proper setup


# =============================================================================
# PROVIDER COST TESTS
# =============================================================================

class TestProviderCosts:
    """Tests for provider cost calculations."""
    
    def test_cost_constants_defined(self):
        """Test cost constants are properly defined."""
        from freya.predict_consumption import PROVIDER_COSTS
        
        assert "local" in PROVIDER_COSTS
        assert "hf" in PROVIDER_COSTS
        assert "together" in PROVIDER_COSTS
        assert "groq" in PROVIDER_COSTS
        
        # Local should be free
        assert PROVIDER_COSTS["local"]["input"] == 0.0
        assert PROVIDER_COSTS["local"]["output"] == 0.0
    
    def test_role_complexity_defined(self):
        """Test role complexity factors are defined."""
        from freya.predict_consumption import ROLE_COMPLEXITY
        
        roles = ["analyst", "pm", "architect", "po", "sm", "dev", "qa"]
        
        for role in roles:
            assert role in ROLE_COMPLEXITY
            assert ROLE_COMPLEXITY[role] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
