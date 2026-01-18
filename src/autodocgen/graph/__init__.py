"""
Dependency graph module for cross-file relationship analysis.

Provides scalable storage and querying of dependencies for large codebases.
"""

from autodocgen.graph.models import NodeType, EdgeType, DependencyNode, DependencyEdge
from autodocgen.graph.store import DependencyStore
from autodocgen.graph.extractor import DependencyExtractor
from autodocgen.graph.visualizer import GraphVisualizer

__all__ = [
    "NodeType",
    "EdgeType", 
    "DependencyNode",
    "DependencyEdge",
    "DependencyStore",
    "DependencyExtractor",
    "GraphVisualizer",
]
