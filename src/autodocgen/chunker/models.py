"""
Data models for code chunking.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from autodocgen.parser.models import ClassInfo, FunctionInfo, NamespaceInfo


@dataclass
class ChunkContext:
    """
    Context information for a code chunk.

    This context is prepended to each chunk to help the LLM understand
    the broader context of the code being analyzed.
    """
    file_path: Path
    chunk_index: int
    total_chunks: int
    namespace: str
    parent_class: Optional[str]
    parent_class_description: str

    # Dependencies used in this chunk
    dependencies: list[str] = field(default_factory=list)
    dependency_descriptions: dict[str, str] = field(default_factory=dict)

    # Related types that appear in this chunk
    related_types: list[str] = field(default_factory=list)
    type_descriptions: dict[str, str] = field(default_factory=dict)

    # Includes summary
    includes_summary: str = ""

    def to_header(self) -> str:
        """Generate a context header string for the LLM."""
        lines = [
            "/*",
            f" * FILE: {self.file_path}",
            f" * CHUNK: {self.chunk_index + 1} of {self.total_chunks}",
        ]

        if self.namespace:
            lines.append(f" * NAMESPACE: {self.namespace}")

        if self.parent_class:
            lines.append(f" * PARENT CLASS: {self.parent_class}")
            if self.parent_class_description:
                lines.append(f" *   Description: {self.parent_class_description}")

        if self.dependencies:
            lines.append(" *")
            lines.append(" * DEPENDENCIES:")
            for dep in self.dependencies:
                desc = self.dependency_descriptions.get(dep, "")
                if desc:
                    lines.append(f" *   - {dep}: {desc}")
                else:
                    lines.append(f" *   - {dep}")

        if self.related_types:
            lines.append(" *")
            lines.append(" * RELEVANT TYPES:")
            for typ in self.related_types:
                desc = self.type_descriptions.get(typ, "")
                if desc:
                    lines.append(f" *   - {typ}: {desc}")
                else:
                    lines.append(f" *   - {typ}")

        if self.includes_summary:
            lines.append(" *")
            lines.append(f" * INCLUDES: {self.includes_summary}")

        lines.append(" */")
        return "\n".join(lines)


@dataclass
class CodeChunk:
    """
    A chunk of code to be processed by the LLM.

    Each chunk contains a logical unit of code (class, function group, etc.)
    along with context information to help the LLM understand it.
    """
    chunk_id: str
    file_path: Path
    chunk_index: int
    total_chunks: int

    # Code content
    code: str
    line_start: int
    line_end: int

    # Context
    context: ChunkContext

    # What this chunk contains
    chunk_type: str  # "class", "function_group", "namespace", "mixed"
    primary_symbol: str  # Main symbol being documented in this chunk
    symbols_contained: list[str] = field(default_factory=list)

    # Associated parsed structures (if available)
    class_info: Optional[ClassInfo] = None
    functions: list[FunctionInfo] = field(default_factory=list)
    namespace_info: Optional[NamespaceInfo] = None

    # Processing state
    is_processed: bool = False
    llm_response: str = ""
    processing_error: Optional[str] = None

    @property
    def line_count(self) -> int:
        """Get the number of lines in this chunk."""
        return self.line_end - self.line_start + 1

    @property
    def full_content(self) -> str:
        """Get the full content including context header."""
        return f"{self.context.to_header()}\n\n{self.code}"

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "chunk_id": self.chunk_id,
            "file_path": str(self.file_path),
            "chunk_index": self.chunk_index,
            "total_chunks": self.total_chunks,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "chunk_type": self.chunk_type,
            "primary_symbol": self.primary_symbol,
            "symbols_contained": self.symbols_contained,
            "is_processed": self.is_processed,
        }
