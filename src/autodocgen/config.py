"""
Configuration management for AutoDocGen.

All configurations are designed for offline-first, privacy-preserving operation.
Network access is strictly controlled and defaults to localhost only.
"""

from pathlib import Path
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator


class LLMConfig(BaseModel):
    """Local LLM configuration - NO external endpoints allowed."""

    backend: Literal["ollama", "llamacpp"] = Field(
        default="ollama",
        description="LLM backend to use: 'ollama' or 'llamacpp'"
    )

    # Ollama settings - localhost only
    ollama_host: str = Field(
        default="127.0.0.1",
        description="Ollama host address - MUST be localhost"
    )
    ollama_port: int = Field(
        default=11434,
        description="Ollama port"
    )

    # llama.cpp settings - localhost only
    llamacpp_host: str = Field(
        default="127.0.0.1",
        description="llama.cpp server host - MUST be localhost"
    )
    llamacpp_port: int = Field(
        default=8081,
        description="llama.cpp server port"
    )

    # Model settings - DEFAULT TO LIGHTWEIGHT 7B MODEL
    model_name: str = Field(
        default="qwen2.5-coder:7b",
        description="Model name to use for analysis (default: lightweight 7B)"
    )
    model_path: Optional[Path] = Field(
        default=None,
        description="Path to GGUF model file (for llamacpp)"
    )

    # Low resource mode for limited hardware
    low_resource_mode: bool = Field(
        default=True,
        description="Enable low resource mode for limited hardware (smaller context, fewer tokens)"
    )

    # Inference settings - REDUCED FOR LOW HARDWARE
    context_length: int = Field(
        default=8192,
        description="Context window size in tokens (reduced for low memory)"
    )
    temperature: float = Field(
        default=0.1,
        description="Temperature for generation (low for consistent docs)"
    )
    max_tokens: int = Field(
        default=2048,
        description="Maximum tokens to generate per response (reduced for speed)"
    )

    # GPU offloading
    gpu_layers: int = Field(
        default=0,
        description="Number of layers to offload to GPU (0 = CPU only)"
    )

    @field_validator("ollama_host", "llamacpp_host")
    @classmethod
    def validate_localhost(cls, v: str) -> str:
        """Ensure host is localhost for security."""
        allowed = {"127.0.0.1", "localhost", "::1"}
        if v not in allowed:
            raise ValueError(
                f"Host must be localhost for security. Got '{v}'. "
                f"Allowed values: {allowed}"
            )
        return v

    def get_base_url(self) -> str:
        """Get the base URL for LLM API calls."""
        if self.backend == "ollama":
            return f"http://{self.ollama_host}:{self.ollama_port}"
        return f"http://{self.llamacpp_host}:{self.llamacpp_port}"

    def get_effective_context(self) -> int:
        """Get effective context length based on mode."""
        if self.low_resource_mode:
            return min(self.context_length, 4096)
        return self.context_length

    def get_effective_max_tokens(self) -> int:
        """Get effective max tokens based on mode."""
        if self.low_resource_mode:
            return min(self.max_tokens, 1024)
        return self.max_tokens


class ServerConfig(BaseModel):
    """Web server configuration - localhost by default for privacy."""

    host: str = Field(
        default="127.0.0.1",
        description="Server host address"
    )
    port: int = Field(
        default=8080,
        description="Server port"
    )
    allow_network_access: bool = Field(
        default=False,
        description="If True, binds to 0.0.0.0 (all interfaces)"
    )
    debug: bool = Field(
        default=False,
        description="Enable Flask debug mode"
    )

    def get_bind_address(self) -> str:
        """Get the address to bind the server to."""
        if self.allow_network_access:
            return "0.0.0.0"
        return "127.0.0.1"


class PrivacyConfig(BaseModel):
    """Privacy settings - networking disabled by default."""

    # Network controls
    allow_any_network: bool = Field(
        default=False,
        description="Allow any network access (dangerous)"
    )
    block_outbound: bool = Field(
        default=True,
        description="Block all outbound network requests"
    )

    # Telemetry - ALWAYS disabled, cannot be changed
    enable_telemetry: bool = Field(
        default=False,
        description="Telemetry is always disabled"
    )
    enable_analytics: bool = Field(
        default=False,
        description="Analytics is always disabled"
    )
    enable_crash_reports: bool = Field(
        default=False,
        description="Crash reports are always disabled"
    )

    # Data handling
    log_llm_prompts: bool = Field(
        default=False,
        description="Log LLM prompts to disk (contains code)"
    )
    cache_llm_responses: bool = Field(
        default=True,
        description="Cache LLM responses for performance"
    )
    clear_cache_on_exit: bool = Field(
        default=False,
        description="Clear LLM cache when exiting"
    )

    @field_validator("enable_telemetry", "enable_analytics", "enable_crash_reports")
    @classmethod
    def force_disabled(cls, v: bool) -> bool:
        """Force these settings to always be False."""
        return False


class ParserConfig(BaseModel):
    """C++ parser configuration."""

    supported_extensions: list[str] = Field(
        default=[".cpp", ".cc", ".cxx", ".c", ".h", ".hpp", ".hxx", ".inl"],
        description="File extensions to parse"
    )
    include_paths: list[Path] = Field(
        default=[],
        description="Additional include paths for libclang"
    )
    compile_flags: list[str] = Field(
        default=["-std=c++17", "-DANDROID"],
        description="Compile flags for libclang"
    )
    exclude_patterns: list[str] = Field(
        default=["**/test/**", "**/tests/**", "**/third_party/**", "**/external/**"],
        description="Glob patterns to exclude from parsing"
    )


class ChunkerConfig(BaseModel):
    """Chunking configuration for large files."""

    max_chunk_lines: int = Field(
        default=300,
        description="Maximum lines per chunk (reduced for smaller context windows)"
    )
    min_chunk_lines: int = Field(
        default=30,
        description="Minimum lines per chunk (to avoid tiny chunks)"
    )
    context_lines: int = Field(
        default=10,
        description="Lines of context to include from surrounding code"
    )
    overlap_lines: int = Field(
        default=5,
        description="Lines to overlap between chunks for continuity"
    )


class DocumentationConfig(BaseModel):
    """Documentation generation configuration."""

    output_format: Literal["markdown", "html", "both"] = Field(
        default="markdown",
        description="Output format for documentation"
    )
    generate_diagrams: bool = Field(
        default=True,
        description="Generate class diagrams"
    )
    diagram_format: Literal["svg", "png"] = Field(
        default="svg",
        description="Diagram output format"
    )
    include_source_links: bool = Field(
        default=True,
        description="Include links to source code lines"
    )
    include_examples: bool = Field(
        default=True,
        description="Include usage examples in documentation"
    )


class Config(BaseModel):
    """Main configuration for AutoDocGen."""

    # Paths
    codebase_path: Path = Field(
        description="Path to the C++ codebase to document"
    )
    output_path: Path = Field(
        default=Path("./docs"),
        description="Path to output generated documentation"
    )
    cache_path: Path = Field(
        default=Path("./cache"),
        description="Path to cache directory"
    )
    database_path: Path = Field(
        default=Path("./data/autodocgen.db"),
        description="Path to SQLite database"
    )

    # Sub-configurations
    llm: LLMConfig = Field(default_factory=LLMConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    privacy: PrivacyConfig = Field(default_factory=PrivacyConfig)
    parser: ParserConfig = Field(default_factory=ParserConfig)
    chunker: ChunkerConfig = Field(default_factory=ChunkerConfig)
    documentation: DocumentationConfig = Field(default_factory=DocumentationConfig)

    # Processing settings
    parallel_workers: int = Field(
        default=4,
        description="Number of parallel workers for processing"
    )
    batch_size: int = Field(
        default=10,
        description="Batch size for LLM requests"
    )

    def validate_offline_mode(self) -> bool:
        """Verify configuration is safe for offline operation."""
        assert self.llm.ollama_host in ["127.0.0.1", "localhost", "::1"]
        assert self.llm.llamacpp_host in ["127.0.0.1", "localhost", "::1"]
        assert not self.privacy.enable_telemetry
        assert not self.privacy.enable_analytics
        assert not self.privacy.enable_crash_reports
        return True

    def ensure_directories(self) -> None:
        """Create required directories if they don't exist."""
        self.output_path.mkdir(parents=True, exist_ok=True)
        self.cache_path.mkdir(parents=True, exist_ok=True)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

    @classmethod
    def load_from_file(cls, path: Path) -> "Config":
        """Load configuration from a YAML or JSON file."""
        import json

        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        content = path.read_text()

        if path.suffix in [".yaml", ".yml"]:
            # We avoid external YAML dependency, use JSON instead
            raise ValueError("YAML not supported. Please use JSON config files.")

        data = json.loads(content)
        return cls(**data)

    def save_to_file(self, path: Path) -> None:
        """Save configuration to a JSON file."""
        import json

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.model_dump(mode="json"), f, indent=2, default=str)


def get_default_config(codebase_path: Path) -> Config:
    """Get a default configuration for the given codebase path."""
    return Config(codebase_path=codebase_path)
