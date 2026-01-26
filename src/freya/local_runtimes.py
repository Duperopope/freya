# src/freya/local_runtimes.py
"""
Local Runtime Detection for Freya 2.1
=====================================

Detects and manages multiple local LLM runtime environments:
- Ollama (primary)
- LM Studio
- KoboldCpp
- Oobabooga Text Generation WebUI
- llama.cpp server

Features:
- Auto-detection of running services
- GPU/driver detection
- Unified API abstraction
- Health monitoring

References:
- Ollama: https://ollama.ai/docs
- LM Studio: https://lmstudio.ai
- KoboldCpp: https://github.com/LostRuins/koboldcpp
- Oobabooga: https://github.com/oobabooga/text-generation-webui
- llama.cpp: https://github.com/ggerganov/llama.cpp
"""

from __future__ import annotations

import logging
import os
import platform
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import requests

from .config import LOCAL_RUNTIMES

logger = logging.getLogger(__name__)


class RuntimeType(str, Enum):
    """Local runtime type enumeration."""
    OLLAMA = "ollama"
    LM_STUDIO = "lm_studio"
    KOBOLDCPP = "koboldcpp"
    OOBABOOGA = "oobabooga"
    LLAMACPP = "llamacpp"


class RuntimeStatus(str, Enum):
    """Runtime status enumeration."""
    ONLINE = "online"
    OFFLINE = "offline"
    STARTING = "starting"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class GPUInfo:
    """GPU information."""
    name: str
    vendor: str
    memory_mb: int
    driver_version: str
    cuda_version: Optional[str] = None
    compute_capability: Optional[str] = None
    is_available: bool = True


@dataclass
class RuntimeInfo:
    """Information about a local runtime."""
    runtime_type: RuntimeType
    name: str
    base_url: str
    api_type: str
    status: RuntimeStatus = RuntimeStatus.UNKNOWN
    models_available: list[str] = field(default_factory=list)
    latency_ms: int = 0
    last_check: Optional[datetime] = None
    error_message: Optional[str] = None
    version: Optional[str] = None
    gpu_info: Optional[GPUInfo] = None


class LocalRuntimeDetector:
    """
    Detects and manages local LLM runtimes.
    """
    
    def __init__(self):
        self.runtimes: dict[RuntimeType, RuntimeInfo] = {}
        self.gpu_info: Optional[GPUInfo] = None
        self._detect_gpu()
    
    def _detect_gpu(self) -> None:
        """Detect available GPU(s)."""
        try:
            # Try NVIDIA first (most common)
            self.gpu_info = self._detect_nvidia_gpu()
            if self.gpu_info:
                return
            
            # Try AMD
            self.gpu_info = self._detect_amd_gpu()
            if self.gpu_info:
                return
            
            # Try Apple Silicon
            self.gpu_info = self._detect_apple_gpu()
            
        except Exception as e:
            logger.warning(f"GPU detection failed: {e}")
    
    def _detect_nvidia_gpu(self) -> Optional[GPUInfo]:
        """Detect NVIDIA GPU using nvidia-smi."""
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            
            if result.returncode == 0 and result.stdout.strip():
                parts = result.stdout.strip().split(",")
                if len(parts) >= 3:
                    name = parts[0].strip()
                    memory_mb = int(float(parts[1].strip()))
                    driver = parts[2].strip()
                    
                    # Try to get CUDA version
                    cuda_version = None
                    try:
                        cuda_result = subprocess.run(
                            ["nvidia-smi", "--query-gpu=compute_cap", "--format=csv,noheader"],
                            capture_output=True,
                            text=True,
                            timeout=5,
                        )
                        if cuda_result.returncode == 0:
                            compute_cap = cuda_result.stdout.strip()
                            cuda_version = compute_cap
                    except Exception:
                        pass
                    
                    return GPUInfo(
                        name=name,
                        vendor="NVIDIA",
                        memory_mb=memory_mb,
                        driver_version=driver,
                        cuda_version=cuda_version,
                        compute_capability=cuda_version,
                    )
                    
        except FileNotFoundError:
            pass
        except Exception as e:
            logger.debug(f"NVIDIA GPU detection failed: {e}")
        
        return None
    
    def _detect_amd_gpu(self) -> Optional[GPUInfo]:
        """Detect AMD GPU using rocm-smi."""
        try:
            result = subprocess.run(
                ["rocm-smi", "--showproductname", "--showmeminfo", "vram"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            
            if result.returncode == 0 and result.stdout.strip():
                # Parse rocm-smi output (simplified)
                lines = result.stdout.strip().split("\n")
                name = "AMD GPU"
                memory_mb = 0
                
                for line in lines:
                    if "GPU" in line and ":" in line:
                        name = line.split(":")[-1].strip()
                    if "Total Memory" in line:
                        try:
                            # Parse memory in MB
                            mem_str = line.split(":")[-1].strip()
                            memory_mb = int(float(mem_str.replace("MB", "").strip()))
                        except Exception:
                            pass
                
                return GPUInfo(
                    name=name,
                    vendor="AMD",
                    memory_mb=memory_mb,
                    driver_version="ROCm",
                )
                
        except FileNotFoundError:
            pass
        except Exception as e:
            logger.debug(f"AMD GPU detection failed: {e}")
        
        return None
    
    def _detect_apple_gpu(self) -> Optional[GPUInfo]:
        """Detect Apple Silicon GPU."""
        if platform.system() != "Darwin":
            return None
        
        try:
            # Check for Apple Silicon
            result = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            
            if result.returncode == 0 and "Apple" in result.stdout:
                cpu_name = result.stdout.strip()
                
                # Get memory info
                mem_result = subprocess.run(
                    ["sysctl", "-n", "hw.memsize"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                
                memory_mb = 0
                if mem_result.returncode == 0:
                    try:
                        memory_mb = int(mem_result.stdout.strip()) // (1024 * 1024)
                    except Exception:
                        pass
                
                return GPUInfo(
                    name=cpu_name,
                    vendor="Apple",
                    memory_mb=memory_mb,
                    driver_version="Metal",
                )
                
        except FileNotFoundError:
            pass
        except Exception as e:
            logger.debug(f"Apple GPU detection failed: {e}")
        
        return None
    
    def detect_runtime(self, runtime_id: str) -> Optional[RuntimeInfo]:
        """Detect a specific runtime."""
        if runtime_id not in LOCAL_RUNTIMES:
            return None
        
        config = LOCAL_RUNTIMES[runtime_id]
        runtime_type = RuntimeType(runtime_id)
        
        info = RuntimeInfo(
            runtime_type=runtime_type,
            name=config["name"],
            base_url=config["base_url"],
            api_type=config["api_type"],
            gpu_info=self.gpu_info,
        )
        
        try:
            t0 = time.time()
            
            # Check health endpoint
            health_url = f"{config['base_url']}{config['health_endpoint']}"
            response = requests.get(health_url, timeout=5)
            
            latency_ms = int((time.time() - t0) * 1000)
            info.latency_ms = latency_ms
            info.last_check = datetime.now()
            
            if response.status_code == 200:
                info.status = RuntimeStatus.ONLINE
                
                # Parse models from response
                try:
                    data = response.json()
                    info.models_available = self._parse_models(data, config["api_type"])
                except Exception:
                    pass
            else:
                info.status = RuntimeStatus.ERROR
                info.error_message = f"HTTP {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            info.status = RuntimeStatus.OFFLINE
            info.error_message = "Connection refused"
        except requests.exceptions.Timeout:
            info.status = RuntimeStatus.OFFLINE
            info.error_message = "Connection timeout"
        except Exception as e:
            info.status = RuntimeStatus.ERROR
            info.error_message = str(e)
        
        self.runtimes[runtime_type] = info
        return info
    
    def _parse_models(self, data: Any, api_type: str) -> list[str]:
        """Parse models from API response."""
        models = []
        
        try:
            if api_type == "ollama":
                # Ollama /api/tags response
                if isinstance(data, dict):
                    for model in data.get("models", []):
                        if isinstance(model, dict):
                            name = model.get("name") or model.get("model")
                            if name:
                                models.append(name)
                                
            elif api_type == "openai":
                # OpenAI-compatible /v1/models response
                if isinstance(data, dict):
                    for model in data.get("data", []):
                        if isinstance(model, dict):
                            model_id = model.get("id")
                            if model_id:
                                models.append(model_id)
                                
            elif api_type == "kobold":
                # KoboldCpp /api/v1/model response
                if isinstance(data, dict):
                    model = data.get("result")
                    if model:
                        models.append(model)
                        
            elif api_type == "llamacpp":
                # llama.cpp /health response
                if isinstance(data, dict):
                    model = data.get("model")
                    if model:
                        models.append(model)
                        
        except Exception as e:
            logger.debug(f"Failed to parse models: {e}")
        
        return models
    
    def detect_all_runtimes(self) -> dict[RuntimeType, RuntimeInfo]:
        """Detect all configured runtimes."""
        for runtime_id in LOCAL_RUNTIMES:
            self.detect_runtime(runtime_id)
        return self.runtimes
    
    def get_available_runtimes(self) -> list[RuntimeInfo]:
        """Get list of available (online) runtimes."""
        return [
            info for info in self.runtimes.values()
            if info.status == RuntimeStatus.ONLINE
        ]
    
    def get_best_runtime(self) -> Optional[RuntimeInfo]:
        """Get the best available runtime based on priority and latency."""
        available = self.get_available_runtimes()
        
        if not available:
            return None
        
        # Sort by priority (from config) then by latency
        def sort_key(info: RuntimeInfo) -> tuple[int, int]:
            priority = LOCAL_RUNTIMES.get(info.runtime_type.value, {}).get("priority", 99)
            return (priority, info.latency_ms)
        
        available.sort(key=sort_key)
        return available[0]
    
    def get_runtime_status(self) -> dict[str, Any]:
        """Get status of all runtimes."""
        return {
            "gpu": {
                "detected": self.gpu_info is not None,
                "name": self.gpu_info.name if self.gpu_info else None,
                "vendor": self.gpu_info.vendor if self.gpu_info else None,
                "memory_mb": self.gpu_info.memory_mb if self.gpu_info else None,
            },
            "runtimes": {
                runtime_type.value: {
                    "name": info.name,
                    "status": info.status.value,
                    "base_url": info.base_url,
                    "models": info.models_available,
                    "latency_ms": info.latency_ms,
                    "last_check": info.last_check.isoformat() if info.last_check else None,
                    "error": info.error_message,
                }
                for runtime_type, info in self.runtimes.items()
            },
        }


class UnifiedLocalClient:
    """
    Unified client for all local LLM runtimes.
    Provides a consistent API regardless of backend.
    """
    
    def __init__(self, runtime_info: RuntimeInfo):
        self.runtime = runtime_info
        self.base_url = runtime_info.base_url
        self.api_type = runtime_info.api_type
    
    def generate(
        self,
        model: str,
        prompt: str,
        system: str = "",
        temperature: float = 0.0,
        max_tokens: int = 1024,
        timeout_sec: int = 120,
    ) -> dict[str, Any]:
        """Generate text using the runtime's API."""
        if self.api_type == "ollama":
            return self._generate_ollama(model, prompt, system, temperature, max_tokens, timeout_sec)
        elif self.api_type == "openai":
            return self._generate_openai(model, prompt, system, temperature, max_tokens, timeout_sec)
        elif self.api_type == "kobold":
            return self._generate_kobold(model, prompt, system, temperature, max_tokens, timeout_sec)
        elif self.api_type == "llamacpp":
            return self._generate_llamacpp(model, prompt, system, temperature, max_tokens, timeout_sec)
        else:
            raise ValueError(f"Unknown API type: {self.api_type}")
    
    def _generate_ollama(
        self,
        model: str,
        prompt: str,
        system: str,
        temperature: float,
        max_tokens: int,
        timeout_sec: int,
    ) -> dict[str, Any]:
        """Generate using Ollama API."""
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        
        if system:
            payload["system"] = system
        
        t0 = time.time()
        response = requests.post(
            f"{self.base_url}/api/generate",
            json=payload,
            timeout=timeout_sec,
        )
        response.raise_for_status()
        duration_ms = int((time.time() - t0) * 1000)
        
        data = response.json()
        return {
            "response": data.get("response", ""),
            "model": model,
            "duration_ms": duration_ms,
        }
    
    def _generate_openai(
        self,
        model: str,
        prompt: str,
        system: str,
        temperature: float,
        max_tokens: int,
        timeout_sec: int,
    ) -> dict[str, Any]:
        """Generate using OpenAI-compatible API."""
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
        
        t0 = time.time()
        response = requests.post(
            f"{self.base_url}/v1/chat/completions",
            json=payload,
            timeout=timeout_sec,
        )
        response.raise_for_status()
        duration_ms = int((time.time() - t0) * 1000)
        
        data = response.json()
        content = ""
        choices = data.get("choices", [])
        if choices:
            content = choices[0].get("message", {}).get("content", "")
        
        return {
            "response": content,
            "model": model,
            "duration_ms": duration_ms,
        }
    
    def _generate_kobold(
        self,
        model: str,
        prompt: str,
        system: str,
        temperature: float,
        max_tokens: int,
        timeout_sec: int,
    ) -> dict[str, Any]:
        """Generate using KoboldCpp API."""
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        
        payload = {
            "prompt": full_prompt,
            "max_length": max_tokens,
            "temperature": temperature if temperature > 0 else 0.01,
        }
        
        t0 = time.time()
        response = requests.post(
            f"{self.base_url}/api/v1/generate",
            json=payload,
            timeout=timeout_sec,
        )
        response.raise_for_status()
        duration_ms = int((time.time() - t0) * 1000)
        
        data = response.json()
        results = data.get("results", [])
        text = results[0].get("text", "") if results else ""
        
        return {
            "response": text,
            "model": model,
            "duration_ms": duration_ms,
        }
    
    def _generate_llamacpp(
        self,
        model: str,
        prompt: str,
        system: str,
        temperature: float,
        max_tokens: int,
        timeout_sec: int,
    ) -> dict[str, Any]:
        """Generate using llama.cpp server API."""
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        
        payload = {
            "prompt": full_prompt,
            "n_predict": max_tokens,
            "temperature": temperature if temperature > 0 else 0.01,
        }
        
        t0 = time.time()
        response = requests.post(
            f"{self.base_url}/completion",
            json=payload,
            timeout=timeout_sec,
        )
        response.raise_for_status()
        duration_ms = int((time.time() - t0) * 1000)
        
        data = response.json()
        return {
            "response": data.get("content", ""),
            "model": model,
            "duration_ms": duration_ms,
        }
    
    def list_models(self) -> list[str]:
        """List available models."""
        return self.runtime.models_available


def detect_and_get_best_runtime() -> Optional[RuntimeInfo]:
    """Convenience function to detect all runtimes and return the best one."""
    detector = LocalRuntimeDetector()
    detector.detect_all_runtimes()
    return detector.get_best_runtime()
