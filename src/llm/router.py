"""Provider routing and selection."""
import os
from typing import Optional
from .base import BaseLLM
from .kimi_adapter import KimiAdapter
from .anthropic_adapter import AnthropicAdapter
from .openai_adapter import OpenAIAdapter
from .ollama_adapter import OllamaAdapter
from .lmstudio_adapter import LMStudioAdapter
from .mock_adapter import MockAdapter


class LLMRouter:
    PROVIDERS = {
        "kimi": KimiAdapter,
        "anthropic": AnthropicAdapter,
        "openai": OpenAIAdapter,
        "ollama": OllamaAdapter,
        "lmstudio": LMStudioAdapter,
        "mock": MockAdapter,
    }

    def __init__(self, default_provider: Optional[str] = None):
        self.default = default_provider or os.getenv("DEFAULT_PROVIDER", "kimi")
        self._instances: dict[str, BaseLLM] = {}

    def get(self, provider: Optional[str] = None, model: Optional[str] = None) -> BaseLLM:
        name = (provider or self.default).lower()
        if name not in self.PROVIDERS:
            raise ValueError(f"Unknown provider: {name}")
        key = f"{name}:{model or 'default'}"
        if key not in self._instances:
            self._instances[key] = self.PROVIDERS[name](model=model)
        return self._instances[key]
