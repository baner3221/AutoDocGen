"""
LLM integration module for local inference.
"""

from autodocgen.llm.ollama_client import OllamaClient
from autodocgen.llm.prompts import PromptBuilder

__all__ = [
    "OllamaClient",
    "PromptBuilder",
]
