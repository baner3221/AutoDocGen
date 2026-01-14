"""
Context builder for code chunks.

Builds rich context information for chunks by analyzing dependencies
and cross-referencing with other documented symbols.
"""

from pathlib import Path
from typing import Optional

from autodocgen.config import Config
from autodocgen.parser.models import CppFileAnalysis, ClassInfo
from autodocgen.chunker.models import CodeChunk, ChunkContext


class ContextBuilder:
    """
    Builds rich context for code chunks by cross-referencing symbols.

    This class enhances chunk context by looking up documentation
    for dependencies, base classes, and related types.
    """

    def __init__(self, config: Config):
        """
        Initialize the context builder.

        Args:
            config: AutoDocGen configuration
        """
        self.config = config
        self._symbol_docs: dict[str, str] = {}  # Cache of symbol -> documentation
        self._class_cache: dict[str, ClassInfo] = {}  # Cache of qualified_name -> ClassInfo

    def register_analysis(self, analysis: CppFileAnalysis) -> None:
        """
        Register symbols from a file analysis for cross-referencing.

        Args:
            analysis: Parsed file analysis to register
        """
        for cls in analysis.all_classes:
            self._class_cache[cls.qualified_name] = cls
            if cls.documentation:
                self._symbol_docs[cls.qualified_name] = cls.documentation

            for method in cls.methods:
                method_key = f"{cls.qualified_name}::{method.name}"
                if method.documentation:
                    self._symbol_docs[method_key] = method.documentation

        for func in analysis.all_functions:
            if func.documentation:
                self._symbol_docs[func.qualified_name] = func.documentation

    def enrich_chunk_context(
        self,
        chunk: CodeChunk,
        analysis: CppFileAnalysis,
    ) -> None:
        """
        Enrich a chunk's context with cross-referenced information.

        Args:
            chunk: The chunk to enrich
            analysis: The file analysis
        """
        context = chunk.context

        # Add dependency descriptions
        for dep in context.dependencies:
            if dep in self._symbol_docs:
                context.dependency_descriptions[dep] = self._truncate(
                    self._symbol_docs[dep], 100
                )
            elif dep in self._class_cache:
                cls = self._class_cache[dep]
                context.dependency_descriptions[dep] = cls.brief_description or ""

        # Add descriptions for related types
        for type_name in context.related_types:
            if type_name in self._symbol_docs:
                context.type_descriptions[type_name] = self._truncate(
                    self._symbol_docs[type_name], 100
                )

        # If this is a class chunk, add base class info
        if chunk.class_info and chunk.class_info.base_classes:
            for base in chunk.class_info.base_classes:
                base_name = self._extract_base_name(base)
                if base_name in self._class_cache:
                    base_cls = self._class_cache[base_name]
                    context.dependency_descriptions[base] = (
                        f"Base class: {base_cls.brief_description or 'No description'}"
                    )

        # Extract types used in this chunk
        if chunk.class_info:
            self._add_used_types(chunk, chunk.class_info)

    def get_dependency_context(
        self,
        symbol: str,
        method_name: Optional[str] = None,
    ) -> str:
        """
        Get comprehensive context for a dependency.

        This is used when generating documentation that references
        another class or method.

        Args:
            symbol: The symbol to get context for
            method_name: Optional specific method name

        Returns:
            Markdown-formatted context string
        """
        if method_name:
            full_symbol = f"{symbol}::{method_name}"
            if full_symbol in self._symbol_docs:
                return self._symbol_docs[full_symbol]

        if symbol in self._symbol_docs:
            return self._symbol_docs[symbol]

        if symbol in self._class_cache:
            cls = self._class_cache[symbol]
            return self._build_class_context(cls)

        return ""

    def _build_class_context(self, cls: ClassInfo) -> str:
        """Build a context string for a class."""
        lines = [f"## {cls.qualified_name}"]

        if cls.brief_description:
            lines.append(f"\n{cls.brief_description}\n")

        if cls.base_classes:
            lines.append(f"\n**Base classes:** {', '.join(cls.base_classes)}")

        # Add public method signatures
        public_methods = cls.public_methods
        if public_methods:
            lines.append("\n**Key methods:**")
            for method in public_methods[:10]:  # Limit to first 10
                lines.append(f"- `{method.signature}`")

        return "\n".join(lines)

    def _add_used_types(self, chunk: CodeChunk, cls: ClassInfo) -> None:
        """Add types used by a class to the chunk context."""
        types_used: set[str] = set()

        # From method parameters
        for method in cls.methods:
            for param in method.parameters:
                type_name = self._extract_type_name(param.type_spelling)
                if type_name and not self._is_builtin_type(type_name):
                    types_used.add(type_name)

            # From return types
            ret_type = self._extract_type_name(method.return_type_spelling)
            if ret_type and not self._is_builtin_type(ret_type):
                types_used.add(ret_type)

        # From member types
        for member in cls.members:
            type_name = self._extract_type_name(member.type_spelling)
            if type_name and not self._is_builtin_type(type_name):
                types_used.add(type_name)

        chunk.context.related_types = list(types_used)

    def _extract_type_name(self, type_spelling: str) -> str:
        """Extract the base type name from a type spelling."""
        type_name = type_spelling

        # Remove qualifiers
        for remove in ["const ", "volatile ", "&", "*", "&&", "struct ", "class ", "enum "]:
            type_name = type_name.replace(remove, "")

        # Handle templates - get the primary type
        if "<" in type_name:
            type_name = type_name[:type_name.index("<")]

        # Handle namespaced types
        type_name = type_name.strip()

        return type_name

    def _extract_base_name(self, base_spelling: str) -> str:
        """Extract clean base class name."""
        # Remove access specifiers if present
        for spec in ["public ", "protected ", "private ", "virtual "]:
            base_spelling = base_spelling.replace(spec, "")

        return base_spelling.strip()

    def _is_builtin_type(self, type_name: str) -> bool:
        """Check if a type is a C++ builtin."""
        builtins = {
            "void", "bool", "char", "short", "int", "long", "float", "double",
            "size_t", "int8_t", "int16_t", "int32_t", "int64_t",
            "uint8_t", "uint16_t", "uint32_t", "uint64_t",
            "string", "wstring", "u16string", "u32string",
            "auto", "nullptr_t",
        }
        return type_name.lower() in builtins or type_name.startswith("std::")

    def _truncate(self, text: str, max_length: int) -> str:
        """Truncate text to max length."""
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."
