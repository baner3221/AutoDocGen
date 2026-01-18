"""
Data models for the dependency graph.

Lightweight transfer objects - actual storage is in SQLite.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


class NodeType(Enum):
    """Types of nodes in the dependency graph."""
    FILE = "file"
    CLASS = "class"
    FUNCTION = "function"
    NAMESPACE = "namespace"
    STRUCT = "struct"
    ENUM = "enum"


class EdgeType(Enum):
    """Types of relationships between nodes."""
    INHERITS = "inherits"      # Class inherits from another
    USES = "uses"              # Uses a type (parameter, member, etc.)
    INCLUDES = "includes"      # File includes another file
    CALLS = "calls"            # Function calls another function
    CONTAINS = "contains"      # Namespace/class contains symbol
    INSTANTIATES = "instantiates"  # Creates instance of class


@dataclass
class DependencyNode:
    """
    Represents a symbol in the dependency graph.
    
    Attributes:
        id: Unique identifier (auto-generated if None)
        name: Symbol name (e.g., "MyClass", "myFunction")
        qualified_name: Fully qualified name (e.g., "ns::MyClass")
        node_type: Type of symbol
        file_path: Source file containing this symbol
        line_number: Line where symbol is defined
    """
    name: str
    qualified_name: str
    node_type: NodeType
    file_path: Optional[Path] = None
    line_number: Optional[int] = None
    id: Optional[int] = None

    def __hash__(self):
        return hash(self.qualified_name)

    def __eq__(self, other):
        if isinstance(other, DependencyNode):
            return self.qualified_name == other.qualified_name
        return False


@dataclass
class DependencyEdge:
    """
    Represents a relationship between two nodes.
    
    Attributes:
        source: The node that has the dependency
        target: The node being depended upon
        edge_type: Type of relationship
        context: Optional description (e.g., "via parameter type")
    """
    source_qualified_name: str
    target_qualified_name: str
    edge_type: EdgeType
    context: Optional[str] = None
    id: Optional[int] = None

    def __hash__(self):
        return hash((self.source_qualified_name, self.target_qualified_name, self.edge_type))

    def __eq__(self, other):
        if isinstance(other, DependencyEdge):
            return (
                self.source_qualified_name == other.source_qualified_name
                and self.target_qualified_name == other.target_qualified_name
                and self.edge_type == other.edge_type
            )
        return False


@dataclass
class DependencyQueryResult:
    """Result of a dependency query."""
    node: DependencyNode
    edges: list[DependencyEdge]
    related_nodes: list[DependencyNode]
