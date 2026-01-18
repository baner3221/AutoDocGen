"""
Dependency extractor for C++ codebases.

Processes parsed file analyses to extract dependency relationships
and stores them in the DependencyStore.

Designed for streaming: processes one file at a time to keep memory usage low.
"""

from pathlib import Path
from typing import Optional

from autodocgen.graph.models import (
    NodeType,
    EdgeType,
    DependencyNode,
    DependencyEdge,
)
from autodocgen.graph.store import DependencyStore
from autodocgen.parser.models import (
    CppFileAnalysis,
    ClassInfo,
    FunctionInfo,
    NamespaceInfo,
    SymbolKind,
)


class DependencyExtractor:
    """
    Extracts dependency relationships from parsed C++ files.
    
    Uses streaming approach: extracts one file at a time,
    immediately writing to the database.
    """

    def __init__(self, store: DependencyStore):
        """
        Initialize the extractor.
        
        Args:
            store: DependencyStore for persisting extracted data
        """
        self.store = store

    def extract_file(
        self, 
        file_path: Path, 
        analysis: CppFileAnalysis,
        incremental: bool = True
    ) -> int:
        """
        Extract dependencies from a single file analysis.
        
        Args:
            file_path: Path to the source file
            analysis: Parsed analysis of the file
            incremental: If True, delete old data for this file first
        
        Returns:
            Number of edges extracted
        """
        if incremental:
            self.store.delete_file_nodes(file_path)
        
        edge_count = 0
        
        # Create file node
        file_node = DependencyNode(
            name=file_path.name,
            qualified_name=str(file_path),
            node_type=NodeType.FILE,
            file_path=file_path,
            line_number=1,
        )
        self.store.upsert_node(file_node)
        
        # Extract include relationships
        edge_count += self._extract_includes(file_path, analysis)
        
        # Extract class relationships
        for cls in analysis.all_classes:
            edge_count += self._extract_class(file_path, cls)
        
        # Extract function relationships
        for func in analysis.all_functions:
            edge_count += self._extract_function(file_path, func)
        
        # Extract namespace containment
        for ns in analysis.namespaces:
            edge_count += self._extract_namespace(file_path, ns)
        
        return edge_count

    def _extract_includes(self, file_path: Path, analysis: CppFileAnalysis) -> int:
        """Extract include dependencies."""
        edge_count = 0
        
        for include in analysis.includes:
            if include.is_system:
                continue  # Skip system includes
            
            # Create edge: this file includes another
            edge = DependencyEdge(
                source_qualified_name=str(file_path),
                target_qualified_name=include.path,
                edge_type=EdgeType.INCLUDES,
                context=f"Line {include.line}" if include.line else None,
            )
            self.store.upsert_edge(edge)
            edge_count += 1
        
        return edge_count

    def _extract_class(self, file_path: Path, cls: ClassInfo) -> int:
        """Extract class dependencies."""
        edge_count = 0
        
        # Create class node
        class_node = DependencyNode(
            name=cls.name,
            qualified_name=cls.qualified_name,
            node_type=NodeType.CLASS if cls.kind == SymbolKind.CLASS else NodeType.STRUCT,
            file_path=file_path,
            line_number=cls.location.line_start if cls.location else None,
        )
        self.store.upsert_node(class_node)
        
        # File contains class
        edge = DependencyEdge(
            source_qualified_name=str(file_path),
            target_qualified_name=cls.qualified_name,
            edge_type=EdgeType.CONTAINS,
        )
        self.store.upsert_edge(edge)
        edge_count += 1
        
        # Inheritance relationships
        for base in cls.base_classes:
            base_name = self._normalize_type_name(base)
            edge = DependencyEdge(
                source_qualified_name=cls.qualified_name,
                target_qualified_name=base_name,
                edge_type=EdgeType.INHERITS,
                context=f"extends {base}",
            )
            self.store.upsert_edge(edge)
            edge_count += 1
        
        # Member type dependencies
        for member in cls.members:
            type_names = self._extract_type_names(member.type_spelling)
            for type_name in type_names:
                if type_name and type_name != cls.qualified_name:
                    edge = DependencyEdge(
                        source_qualified_name=cls.qualified_name,
                        target_qualified_name=type_name,
                        edge_type=EdgeType.USES,
                        context=f"member: {member.name}",
                    )
                    self.store.upsert_edge(edge)
                    edge_count += 1
        
        # Method parameter/return type dependencies
        for method in cls.methods:
            edge_count += self._extract_method_dependencies(
                cls.qualified_name, method
            )
        
        return edge_count

    def _extract_function(self, file_path: Path, func: FunctionInfo) -> int:
        """Extract free function dependencies."""
        edge_count = 0
        
        # Create function node
        func_node = DependencyNode(
            name=func.name,
            qualified_name=func.qualified_name,
            node_type=NodeType.FUNCTION,
            file_path=file_path,
            line_number=func.location.line_start if func.location else None,
        )
        self.store.upsert_node(func_node)
        
        # File contains function
        edge = DependencyEdge(
            source_qualified_name=str(file_path),
            target_qualified_name=func.qualified_name,
            edge_type=EdgeType.CONTAINS,
        )
        self.store.upsert_edge(edge)
        edge_count += 1
        
        # Return type dependency
        type_names = self._extract_type_names(func.return_type)
        for type_name in type_names:
            if type_name:
                edge = DependencyEdge(
                    source_qualified_name=func.qualified_name,
                    target_qualified_name=type_name,
                    edge_type=EdgeType.USES,
                    context="return type",
                )
                self.store.upsert_edge(edge)
                edge_count += 1
        
        # Parameter type dependencies
        for param in func.parameters:
            type_names = self._extract_type_names(param.type_spelling)
            for type_name in type_names:
                if type_name:
                    edge = DependencyEdge(
                        source_qualified_name=func.qualified_name,
                        target_qualified_name=type_name,
                        edge_type=EdgeType.USES,
                        context=f"param: {param.name}",
                    )
                    self.store.upsert_edge(edge)
                    edge_count += 1
        
        return edge_count

    def _extract_method_dependencies(
        self, 
        class_name: str, 
        method: FunctionInfo
    ) -> int:
        """Extract dependencies from a method."""
        edge_count = 0
        
        # Return type
        type_names = self._extract_type_names(method.return_type)
        for type_name in type_names:
            if type_name and type_name != class_name:
                edge = DependencyEdge(
                    source_qualified_name=class_name,
                    target_qualified_name=type_name,
                    edge_type=EdgeType.USES,
                    context=f"method {method.name} returns",
                )
                self.store.upsert_edge(edge)
                edge_count += 1
        
        # Parameters
        for param in method.parameters:
            type_names = self._extract_type_names(param.type_spelling)
            for type_name in type_names:
                if type_name and type_name != class_name:
                    edge = DependencyEdge(
                        source_qualified_name=class_name,
                        target_qualified_name=type_name,
                        edge_type=EdgeType.USES,
                        context=f"method {method.name} param",
                    )
                    self.store.upsert_edge(edge)
                    edge_count += 1
        
        return edge_count

    def _extract_namespace(self, file_path: Path, ns: NamespaceInfo) -> int:
        """Extract namespace containment."""
        edge_count = 0
        
        # Create namespace node
        ns_node = DependencyNode(
            name=ns.name,
            qualified_name=ns.qualified_name,
            node_type=NodeType.NAMESPACE,
            file_path=file_path,
            line_number=ns.location.line_start if ns.location else None,
        )
        self.store.upsert_node(ns_node)
        
        # File contains namespace
        edge = DependencyEdge(
            source_qualified_name=str(file_path),
            target_qualified_name=ns.qualified_name,
            edge_type=EdgeType.CONTAINS,
        )
        self.store.upsert_edge(edge)
        edge_count += 1
        
        # Namespace contains classes
        for cls in ns.classes:
            edge = DependencyEdge(
                source_qualified_name=ns.qualified_name,
                target_qualified_name=cls.qualified_name,
                edge_type=EdgeType.CONTAINS,
            )
            self.store.upsert_edge(edge)
            edge_count += 1
        
        # Namespace contains functions
        for func in ns.functions:
            edge = DependencyEdge(
                source_qualified_name=ns.qualified_name,
                target_qualified_name=func.qualified_name,
                edge_type=EdgeType.CONTAINS,
            )
            self.store.upsert_edge(edge)
            edge_count += 1
        
        # Nested namespaces
        for nested in ns.nested_namespaces:
            edge_count += self._extract_namespace(file_path, nested)
            edge = DependencyEdge(
                source_qualified_name=ns.qualified_name,
                target_qualified_name=nested.qualified_name,
                edge_type=EdgeType.CONTAINS,
            )
            self.store.upsert_edge(edge)
            edge_count += 1
        
        return edge_count

    def _normalize_type_name(self, type_str: str) -> str:
        """Normalize a type name by removing qualifiers."""
        # Remove common C++ qualifiers
        result = type_str
        for remove in ["const ", "volatile ", "mutable ", "&", "*", "&&"]:
            result = result.replace(remove, "")
        
        # Remove template parameters for base name
        if "<" in result:
            result = result[:result.index("<")]
        
        return result.strip()

    def _extract_type_names(self, type_str: str) -> list[str]:
        """Extract all type names from a type string."""
        if not type_str:
            return []
        
        # Skip primitive types
        primitives = {
            "void", "int", "char", "bool", "float", "double", 
            "long", "short", "unsigned", "signed", "auto",
            "size_t", "int8_t", "int16_t", "int32_t", "int64_t",
            "uint8_t", "uint16_t", "uint32_t", "uint64_t",
        }
        
        base_name = self._normalize_type_name(type_str)
        
        # Handle fully qualified names
        if "::" in base_name:
            parts = base_name.split("::")
            base_name = "::".join(p for p in parts if p)
        
        if base_name.lower() in primitives or not base_name:
            return []
        
        # Also extract template parameter types
        result = [base_name]
        
        if "<" in type_str and ">" in type_str:
            template_content = type_str[type_str.index("<")+1:type_str.rindex(">")]
            # Simple split by comma (doesn't handle nested templates perfectly)
            for part in template_content.split(","):
                nested = self._normalize_type_name(part.strip())
                if nested and nested.lower() not in primitives:
                    result.append(nested)
        
        return result
