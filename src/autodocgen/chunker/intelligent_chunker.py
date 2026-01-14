"""
Intelligent chunking for large C++ files.

Splits large files into logical chunks that can be processed by the LLM
while preserving semantic context and relationships.
"""

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from autodocgen.config import Config
from autodocgen.parser.models import (
    CppFileAnalysis,
    ClassInfo,
    FunctionInfo,
    NamespaceInfo,
)
from autodocgen.chunker.models import CodeChunk, ChunkContext


@dataclass
class ChunkBoundary:
    """Represents a boundary for chunking."""
    line_start: int
    line_end: int
    symbol_name: str
    symbol_type: str  # class, function, namespace


class IntelligentChunker:
    """
    Intelligently chunks large C++ files for LLM processing.

    Strategy:
    1. Parse file to get structural information
    2. Identify logical boundaries (classes, namespaces, function groups)
    3. Split at boundaries, respecting max chunk size
    4. Add context headers to each chunk
    """

    def __init__(self, config: Config):
        """
        Initialize the chunker.

        Args:
            config: AutoDocGen configuration
        """
        self.config = config
        self.max_lines = config.chunker.max_chunk_lines
        self.min_lines = config.chunker.min_chunk_lines
        self.context_lines = config.chunker.context_lines
        self.overlap_lines = config.chunker.overlap_lines

    def chunk_file(
        self,
        file_path: Path,
        analysis: CppFileAnalysis,
        source_code: str,
    ) -> list[CodeChunk]:
        """
        Chunk a C++ file into logical segments.

        Args:
            file_path: Path to the source file
            analysis: Parsed analysis of the file
            source_code: The raw source code

        Returns:
            List of CodeChunk objects ready for LLM processing
        """
        lines = source_code.splitlines()
        total_lines = len(lines)

        # For small files, just return a single chunk
        if total_lines <= self.max_lines:
            return self._create_single_chunk(file_path, analysis, source_code, lines)

        # Identify logical boundaries
        boundaries = self._identify_boundaries(analysis)

        # Create chunks based on boundaries
        chunks = self._create_chunks_from_boundaries(
            file_path, analysis, source_code, lines, boundaries
        )

        return chunks

    def _identify_boundaries(self, analysis: CppFileAnalysis) -> list[ChunkBoundary]:
        """Identify logical chunk boundaries in the file."""
        boundaries: list[ChunkBoundary] = []

        # Classes are primary boundaries
        for cls in analysis.all_classes:
            if cls.location:
                boundaries.append(ChunkBoundary(
                    line_start=cls.location.line_start,
                    line_end=cls.location.line_end,
                    symbol_name=cls.qualified_name,
                    symbol_type="class",
                ))

        # Free functions grouped by prefix or proximity
        function_groups = self._group_functions(analysis.all_functions)
        for group_name, functions in function_groups.items():
            if functions:
                start = min(f.location.line_start for f in functions if f.location)
                end = max(f.location.line_end for f in functions if f.location)
                boundaries.append(ChunkBoundary(
                    line_start=start,
                    line_end=end,
                    symbol_name=group_name,
                    symbol_type="function_group",
                ))

        # Namespaces as boundaries
        for ns in analysis.namespaces:
            if ns.location:
                boundaries.append(ChunkBoundary(
                    line_start=ns.location.line_start,
                    line_end=ns.location.line_end,
                    symbol_name=ns.qualified_name,
                    symbol_type="namespace",
                ))

        # Sort by start line
        boundaries.sort(key=lambda b: b.line_start)

        return boundaries

    def _group_functions(
        self, functions: list[FunctionInfo]
    ) -> dict[str, list[FunctionInfo]]:
        """Group functions by common prefix or proximity."""
        if not functions:
            return {}

        groups: dict[str, list[FunctionInfo]] = {}

        for func in functions:
            # Try to find a common prefix
            prefix = self._get_function_prefix(func.name)
            if prefix:
                group_name = f"{prefix}_functions"
            else:
                group_name = "misc_functions"

            if group_name not in groups:
                groups[group_name] = []
            groups[group_name].append(func)

        return groups

    def _get_function_prefix(self, name: str) -> str:
        """Extract a grouping prefix from a function name."""
        # Common prefixes in Android/kernel code
        prefixes = [
            "on", "handle", "do", "process", "init", "destroy",
            "create", "get", "set", "is", "has", "can", "should",
            "update", "notify", "dispatch", "validate", "parse",
        ]

        name_lower = name.lower()
        for prefix in prefixes:
            if name_lower.startswith(prefix) and len(name) > len(prefix):
                # Check if it's a camelCase or snake_case boundary
                next_char = name[len(prefix)]
                if next_char.isupper() or next_char == "_":
                    return prefix

        # Try to split on underscore
        if "_" in name:
            return name.split("_")[0]

        return ""

    def _create_single_chunk(
        self,
        file_path: Path,
        analysis: CppFileAnalysis,
        source_code: str,
        lines: list[str],
    ) -> list[CodeChunk]:
        """Create a single chunk for a small file."""
        context = self._build_context(
            file_path=file_path,
            analysis=analysis,
            chunk_index=0,
            total_chunks=1,
            primary_ns="",
            primary_class=None,
        )

        chunk_id = self._generate_chunk_id(file_path, 0)
        symbols = self._extract_symbol_names(analysis)

        return [CodeChunk(
            chunk_id=chunk_id,
            file_path=file_path,
            chunk_index=0,
            total_chunks=1,
            code=source_code,
            line_start=1,
            line_end=len(lines),
            context=context,
            chunk_type="file",
            primary_symbol=file_path.stem,
            symbols_contained=symbols,
        )]

    def _create_chunks_from_boundaries(
        self,
        file_path: Path,
        analysis: CppFileAnalysis,
        source_code: str,
        lines: list[str],
        boundaries: list[ChunkBoundary],
    ) -> list[CodeChunk]:
        """Create chunks based on identified boundaries."""
        if not boundaries:
            return self._create_single_chunk(file_path, analysis, source_code, lines)

        chunks: list[CodeChunk] = []
        total_lines = len(lines)

        # Merge small adjacent boundaries
        merged = self._merge_small_boundaries(boundaries, total_lines)

        # Split large boundaries
        final_boundaries = self._split_large_boundaries(merged, lines)

        total_chunks = len(final_boundaries)

        for i, boundary in enumerate(final_boundaries):
            # Get the code for this boundary
            chunk_lines = lines[boundary.line_start - 1:boundary.line_end]
            chunk_code = "\n".join(chunk_lines)

            # Find associated class if this is a class chunk
            class_info = None
            if boundary.symbol_type == "class":
                class_info = analysis.get_class_by_name(boundary.symbol_name)

            # Build context
            context = self._build_context(
                file_path=file_path,
                analysis=analysis,
                chunk_index=i,
                total_chunks=total_chunks,
                primary_ns=self._get_namespace_for_line(
                    analysis, boundary.line_start
                ),
                primary_class=class_info,
            )

            chunk_id = self._generate_chunk_id(file_path, i)

            chunks.append(CodeChunk(
                chunk_id=chunk_id,
                file_path=file_path,
                chunk_index=i,
                total_chunks=total_chunks,
                code=chunk_code,
                line_start=boundary.line_start,
                line_end=boundary.line_end,
                context=context,
                chunk_type=boundary.symbol_type,
                primary_symbol=boundary.symbol_name,
                class_info=class_info,
            ))

        return chunks

    def _merge_small_boundaries(
        self,
        boundaries: list[ChunkBoundary],
        total_lines: int,
    ) -> list[ChunkBoundary]:
        """Merge small adjacent boundaries."""
        if not boundaries:
            return []

        merged: list[ChunkBoundary] = []
        current = boundaries[0]

        for next_boundary in boundaries[1:]:
            current_size = current.line_end - current.line_start + 1
            next_size = next_boundary.line_end - next_boundary.line_start + 1
            combined_size = next_boundary.line_end - current.line_start + 1

            # Merge if combined is still under max and both are small
            if combined_size <= self.max_lines and (
                current_size < self.min_lines or next_size < self.min_lines
            ):
                current = ChunkBoundary(
                    line_start=current.line_start,
                    line_end=next_boundary.line_end,
                    symbol_name=f"{current.symbol_name}+{next_boundary.symbol_name}",
                    symbol_type="mixed",
                )
            else:
                merged.append(current)
                current = next_boundary

        merged.append(current)
        return merged

    def _split_large_boundaries(
        self,
        boundaries: list[ChunkBoundary],
        lines: list[str],
    ) -> list[ChunkBoundary]:
        """Split boundaries that are too large."""
        result: list[ChunkBoundary] = []

        for boundary in boundaries:
            size = boundary.line_end - boundary.line_start + 1

            if size <= self.max_lines:
                result.append(boundary)
            else:
                # Split at logical points (method boundaries, etc.)
                splits = self._find_split_points(
                    lines,
                    boundary.line_start,
                    boundary.line_end,
                    self.max_lines,
                )

                for i, (start, end) in enumerate(splits):
                    result.append(ChunkBoundary(
                        line_start=start,
                        line_end=end,
                        symbol_name=f"{boundary.symbol_name}_part{i+1}",
                        symbol_type=boundary.symbol_type,
                    ))

        return result

    def _find_split_points(
        self,
        lines: list[str],
        start: int,
        end: int,
        max_size: int,
    ) -> list[tuple[int, int]]:
        """Find good split points within a large block."""
        splits: list[tuple[int, int]] = []
        current_start = start

        while current_start < end:
            target_end = min(current_start + max_size - 1, end)

            # Try to find a good split point (empty line, closing brace, etc.)
            actual_end = self._find_natural_break(
                lines, current_start, target_end, end
            )

            splits.append((current_start, actual_end))
            current_start = actual_end + 1

        return splits

    def _find_natural_break(
        self,
        lines: list[str],
        start: int,
        target: int,
        max_end: int,
    ) -> int:
        """Find a natural break point near the target line."""
        # Search backwards from target for a good break
        for line_num in range(target, start, -1):
            line = lines[line_num - 1].strip()

            # Empty line is a good break
            if not line:
                return line_num

            # Closing brace at start of line
            if line.startswith("}"):
                return line_num

            # End of function/method definition
            if line.endswith("{"):
                return line_num - 1 if line_num > start else line_num

        # If no good break found, just use target
        return min(target, max_end)

    def _build_context(
        self,
        file_path: Path,
        analysis: CppFileAnalysis,
        chunk_index: int,
        total_chunks: int,
        primary_ns: str,
        primary_class: Optional[ClassInfo],
    ) -> ChunkContext:
        """Build context information for a chunk."""
        # Get includes summary
        includes = [inc.path for inc in analysis.includes if not inc.is_system]
        includes_summary = ", ".join(includes[:5])
        if len(includes) > 5:
            includes_summary += f"... (+{len(includes) - 5} more)"

        # Get dependencies from class
        dependencies: list[str] = []
        if primary_class:
            dependencies = list(primary_class.base_classes)
            # Add types used in methods
            for method in primary_class.methods:
                for param in method.parameters:
                    type_name = self._extract_type_name(param.type_spelling)
                    if type_name and type_name not in dependencies:
                        dependencies.append(type_name)

        return ChunkContext(
            file_path=file_path,
            chunk_index=chunk_index,
            total_chunks=total_chunks,
            namespace=primary_ns,
            parent_class=primary_class.qualified_name if primary_class else None,
            parent_class_description=primary_class.brief_description if primary_class else "",
            dependencies=dependencies[:10],  # Limit to avoid overly long context
            includes_summary=includes_summary,
        )

    def _get_namespace_for_line(
        self,
        analysis: CppFileAnalysis,
        line: int,
    ) -> str:
        """Find which namespace a line belongs to."""
        for ns in analysis.namespaces:
            if ns.location:
                if ns.location.line_start <= line <= ns.location.line_end:
                    # Check nested namespaces
                    for nested in ns.nested_namespaces:
                        if nested.location:
                            if nested.location.line_start <= line <= nested.location.line_end:
                                return nested.qualified_name
                    return ns.qualified_name
        return ""

    def _extract_type_name(self, type_spelling: str) -> str:
        """Extract the base type name from a type spelling."""
        # Remove common qualifiers and decorators
        type_name = type_spelling
        for remove in ["const ", "volatile ", "&", "*", "&&"]:
            type_name = type_name.replace(remove, "")

        # Remove template arguments
        if "<" in type_name:
            type_name = type_name[:type_name.index("<")]

        # Remove namespace for checking
        if "::" in type_name:
            type_name = type_name.split("::")[-1]

        return type_name.strip()

    def _extract_symbol_names(self, analysis: CppFileAnalysis) -> list[str]:
        """Extract all symbol names from an analysis."""
        symbols: list[str] = []

        for cls in analysis.all_classes:
            symbols.append(cls.qualified_name)
            for method in cls.methods:
                symbols.append(f"{cls.qualified_name}::{method.name}")

        for func in analysis.all_functions:
            symbols.append(func.qualified_name)

        for enum in analysis.enums:
            symbols.append(enum.qualified_name)

        return symbols

    def _generate_chunk_id(self, file_path: Path, index: int) -> str:
        """Generate a unique ID for a chunk."""
        content = f"{file_path}:{index}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
