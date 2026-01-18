"""
Ollama client for local LLM inference.

All communication is restricted to localhost for privacy.
"""

import json
import sqlite3
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Iterator
from urllib.request import urlopen, Request
from urllib.error import URLError

from autodocgen.config import Config


@dataclass
class LLMResponse:
    """Response from the LLM."""
    content: str
    model: str
    tokens_used: int
    cached: bool = False
    error: Optional[str] = None


class OllamaClient:
    """
    Client for Ollama local LLM server.

    SECURITY: All requests are made to localhost only.
    No telemetry, no external network access.
    """

    def __init__(self, config: Config):
        """
        Initialize the Ollama client.

        Args:
            config: AutoDocGen configuration
        """
        self.config = config
        self.base_url = config.llm.get_base_url()
        self.model = config.llm.model_name

        # Response cache
        self._cache_enabled = config.privacy.cache_llm_responses
        self._cache_db: Optional[sqlite3.Connection] = None
        if self._cache_enabled:
            self._init_cache()

    def _init_cache(self) -> None:
        """Initialize the response cache database."""
        cache_path = self.config.cache_path / "llm_cache.db"
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        self._cache_db = sqlite3.connect(str(cache_path))
        self._cache_db.execute("""
            CREATE TABLE IF NOT EXISTS response_cache (
                prompt_hash TEXT PRIMARY KEY,
                model TEXT,
                response TEXT,
                tokens_used INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self._cache_db.commit()

    def check_connection(self) -> bool:
        """
        Check if Ollama is running and accessible.

        Returns:
            True if Ollama is accessible, False otherwise
        """
        try:
            req = Request(f"{self.base_url}/api/tags")
            with urlopen(req, timeout=5) as response:
                return response.status == 200
        except (URLError, TimeoutError):
            return False

    def list_models(self) -> list[str]:
        """
        List available models in Ollama.

        Returns:
            List of model names
        """
        try:
            req = Request(f"{self.base_url}/api/tags")
            with urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                return [model["name"] for model in data.get("models", [])]
        except (URLError, json.JSONDecodeError):
            return []

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        use_cache: bool = True,
    ) -> LLMResponse:
        """
        Generate a response from the LLM.

        Args:
            prompt: The prompt to send
            system_prompt: Optional system prompt
            use_cache: Whether to use cached responses

        Returns:
            LLMResponse with the generated content
        """
        # Check cache first
        if use_cache and self._cache_enabled:
            cached = self._get_cached(prompt, system_prompt)
            if cached:
                return cached

        # Build request payload - use effective values for low resource mode
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.config.llm.temperature,
                "num_predict": self.config.llm.get_effective_max_tokens(),
                "num_ctx": self.config.llm.get_effective_context(),
                "num_gpu": self.config.llm.gpu_layers,  # 0 = CPU only (fixes CUDA errors)
            },
        }

        if system_prompt:
            payload["system"] = system_prompt

        try:
            req = Request(
                f"{self.base_url}/api/generate",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            with urlopen(req, timeout=600) as response:  # 10 min timeout for slow systems
                data = json.loads(response.read().decode())

                result = LLMResponse(
                    content=data.get("response", ""),
                    model=self.model,
                    tokens_used=data.get("eval_count", 0),
                    cached=False,
                )

                # Cache the response
                if use_cache and self._cache_enabled:
                    self._cache_response(prompt, system_prompt, result)

                return result

        except URLError as e:
            return LLMResponse(
                content="",
                model=self.model,
                tokens_used=0,
                error=f"Connection error: {e.reason}",
            )
        except json.JSONDecodeError as e:
            return LLMResponse(
                content="",
                model=self.model,
                tokens_used=0,
                error=f"Invalid response from Ollama: {e}",
            )
        except TimeoutError:
            return LLMResponse(
                content="",
                model=self.model,
                tokens_used=0,
                error="Request timed out",
            )

    def generate_streaming(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> Iterator[str]:
        """
        Generate a streaming response from the LLM.

        Args:
            prompt: The prompt to send
            system_prompt: Optional system prompt

        Yields:
            Chunks of generated text
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": self.config.llm.temperature,
                "num_predict": self.config.llm.get_effective_max_tokens(),
                "num_ctx": self.config.llm.get_effective_context(),
            },
        }

        if system_prompt:
            payload["system"] = system_prompt

        try:
            req = Request(
                f"{self.base_url}/api/generate",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            with urlopen(req, timeout=300) as response:
                for line in response:
                    if line:
                        try:
                            data = json.loads(line.decode())
                            chunk = data.get("response", "")
                            if chunk:
                                yield chunk
                            if data.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue

        except (URLError, TimeoutError) as e:
            yield f"\n\n[Error: {e}]"

    def _get_cache_key(self, prompt: str, system_prompt: Optional[str]) -> str:
        """Generate a cache key for a prompt."""
        content = f"{self.model}:{system_prompt or ''}:{prompt}"
        return hashlib.sha256(content.encode()).hexdigest()

    def _get_cached(
        self, prompt: str, system_prompt: Optional[str]
    ) -> Optional[LLMResponse]:
        """Get a cached response if available."""
        if not self._cache_db:
            return None

        cache_key = self._get_cache_key(prompt, system_prompt)
        cursor = self._cache_db.execute(
            "SELECT response, model, tokens_used FROM response_cache WHERE prompt_hash = ?",
            (cache_key,),
        )
        row = cursor.fetchone()

        if row:
            return LLMResponse(
                content=row[0],
                model=row[1],
                tokens_used=row[2],
                cached=True,
            )

        return None

    def _cache_response(
        self,
        prompt: str,
        system_prompt: Optional[str],
        response: LLMResponse,
    ) -> None:
        """Cache an LLM response."""
        if not self._cache_db or response.error:
            return

        cache_key = self._get_cache_key(prompt, system_prompt)
        self._cache_db.execute(
            """
            INSERT OR REPLACE INTO response_cache
            (prompt_hash, model, response, tokens_used)
            VALUES (?, ?, ?, ?)
            """,
            (cache_key, response.model, response.content, response.tokens_used),
        )
        self._cache_db.commit()

    def clear_cache(self) -> None:
        """Clear the response cache."""
        if self._cache_db:
            self._cache_db.execute("DELETE FROM response_cache")
            self._cache_db.commit()

    def close(self) -> None:
        """Close database connections."""
        if self._cache_db:
            self._cache_db.close()
            self._cache_db = None
