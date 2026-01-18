"""
Graph visualization for dependency relationships.

Generates filtered subgraph visualizations in Mermaid and Graphviz formats.
Never loads the full graph - always queries for specific neighborhoods.
"""

from pathlib import Path
from typing import Optional
import subprocess
import tempfile

from autodocgen.graph.models import (
    NodeType,
    EdgeType,
    DependencyQueryResult,
)
from autodocgen.graph.store import DependencyStore


class GraphVisualizer:
    """
    Generates visual representations of dependency subgraphs.
    
    Optimized for large codebases - only renders filtered views.
    """

    # Node styling by type
    NODE_STYLES = {
        NodeType.FILE: {"shape": "note", "color": "#E8E8E8"},
        NodeType.CLASS: {"shape": "box", "color": "#A7C7E7"},
        NodeType.STRUCT: {"shape": "box", "color": "#B4D7A8"},
        NodeType.FUNCTION: {"shape": "ellipse", "color": "#FFE4B5"},
        NodeType.NAMESPACE: {"shape": "folder", "color": "#DDA0DD"},
        NodeType.ENUM: {"shape": "hexagon", "color": "#F0E68C"},
    }

    # Edge styling by type
    EDGE_STYLES = {
        EdgeType.INHERITS: {"style": "solid", "color": "#2E7D32", "label": "extends"},
        EdgeType.USES: {"style": "dashed", "color": "#1565C0", "label": "uses"},
        EdgeType.INCLUDES: {"style": "dotted", "color": "#757575", "label": "includes"},
        EdgeType.CALLS: {"style": "solid", "color": "#F57C00", "label": "calls"},
        EdgeType.CONTAINS: {"style": "solid", "color": "#9E9E9E", "label": "contains"},
        EdgeType.INSTANTIATES: {"style": "dashed", "color": "#7B1FA2", "label": "creates"},
    }

    def __init__(self, store: DependencyStore):
        """
        Initialize the visualizer.
        
        Args:
            store: DependencyStore to query
        """
        self.store = store

    def generate_mermaid(
        self,
        center_symbol: str,
        depth: int = 2,
        direction: str = "both",
        include_contains: bool = False,
    ) -> str:
        """
        Generate a Mermaid.js flowchart for a symbol's neighborhood.
        
        Args:
            center_symbol: Qualified name of the center node
            depth: Number of hops to include
            direction: "in", "out", or "both"
            include_contains: Include containment edges (can be noisy)
        
        Returns:
            Mermaid flowchart definition
        """
        result = self.store.get_subgraph(center_symbol, depth, direction)
        
        lines = ["flowchart TD"]
        
        # Track added nodes
        added_nodes: set[str] = set()
        
        def get_node_id(name: str) -> str:
            """Create a safe Mermaid node ID."""
            return name.replace("::", "_").replace("<", "_").replace(">", "_").replace(" ", "_")
        
        def add_node(qualified_name: str, node_type: NodeType, is_center: bool = False):
            """Add a node to the diagram."""
            if qualified_name in added_nodes:
                return
            
            node_id = get_node_id(qualified_name)
            display_name = qualified_name.split("::")[-1]
            
            # Truncate long names
            if len(display_name) > 30:
                display_name = display_name[:27] + "..."
            
            style = self.NODE_STYLES.get(node_type, {"shape": "box", "color": "#FFFFFF"})
            
            if is_center:
                lines.append(f'    {node_id}["{display_name}"]:::center')
            else:
                lines.append(f'    {node_id}["{display_name}"]')
            
            added_nodes.add(qualified_name)
        
        # Add center node
        add_node(
            result.node.qualified_name, 
            result.node.node_type, 
            is_center=True
        )
        
        # Add related nodes
        for node in result.related_nodes:
            add_node(node.qualified_name, node.node_type)
        
        # Add edges
        for edge in result.edges:
            if not include_contains and edge.edge_type == EdgeType.CONTAINS:
                continue
            
            source_id = get_node_id(edge.source_qualified_name)
            target_id = get_node_id(edge.target_qualified_name)
            
            edge_style = self.EDGE_STYLES.get(edge.edge_type, {})
            label = edge_style.get("label", "")
            
            if edge.edge_type == EdgeType.INHERITS:
                lines.append(f"    {source_id} -->|{label}| {target_id}")
            elif edge.edge_type == EdgeType.USES:
                lines.append(f"    {source_id} -.->|{label}| {target_id}")
            else:
                lines.append(f"    {source_id} --> {target_id}")
        
        # Add styling
        lines.append("")
        lines.append("    classDef center fill:#FFD700,stroke:#333,stroke-width:3px")
        
        return "\n".join(lines)

    def generate_graphviz(
        self,
        center_symbol: str,
        depth: int = 2,
        direction: str = "both",
        include_contains: bool = False,
    ) -> str:
        """
        Generate a Graphviz DOT definition for a symbol's neighborhood.
        
        Args:
            center_symbol: Qualified name of the center node
            depth: Number of hops to include
            direction: "in", "out", or "both"
            include_contains: Include containment edges
        
        Returns:
            DOT language definition
        """
        result = self.store.get_subgraph(center_symbol, depth, direction)
        
        lines = [
            "digraph Dependencies {",
            '    rankdir=TB;',
            '    node [fontname="Arial", fontsize=10];',
            '    edge [fontname="Arial", fontsize=8];',
            "",
        ]
        
        added_nodes: set[str] = set()
        
        def get_node_id(name: str) -> str:
            """Create a safe DOT node ID."""
            return '"' + name.replace('"', '\\"') + '"'
        
        def add_node(qualified_name: str, node_type: NodeType, is_center: bool = False):
            if qualified_name in added_nodes:
                return
            
            node_id = get_node_id(qualified_name)
            display_name = qualified_name.split("::")[-1]
            
            if len(display_name) > 25:
                display_name = display_name[:22] + "..."
            
            style = self.NODE_STYLES.get(node_type, {"shape": "box", "color": "#FFFFFF"})
            shape = style["shape"]
            color = style["color"]
            
            if is_center:
                lines.append(
                    f'    {node_id} [label="{display_name}", shape={shape}, '
                    f'style=filled, fillcolor="#FFD700", penwidth=3];'
                )
            else:
                lines.append(
                    f'    {node_id} [label="{display_name}", shape={shape}, '
                    f'style=filled, fillcolor="{color}"];'
                )
            
            added_nodes.add(qualified_name)
        
        # Add nodes
        add_node(result.node.qualified_name, result.node.node_type, is_center=True)
        for node in result.related_nodes:
            add_node(node.qualified_name, node.node_type)
        
        lines.append("")
        
        # Add edges
        for edge in result.edges:
            if not include_contains and edge.edge_type == EdgeType.CONTAINS:
                continue
            
            source_id = get_node_id(edge.source_qualified_name)
            target_id = get_node_id(edge.target_qualified_name)
            
            edge_style = self.EDGE_STYLES.get(edge.edge_type, {})
            color = edge_style.get("color", "#000000")
            style = "dashed" if edge_style.get("style") == "dashed" else "solid"
            label = edge_style.get("label", "")
            
            lines.append(
                f'    {source_id} -> {target_id} '
                f'[color="{color}", style={style}, label="{label}"];'
            )
        
        lines.append("}")
        return "\n".join(lines)

    def render_svg(
        self,
        center_symbol: str,
        output_path: Path,
        depth: int = 2,
        direction: str = "both",
    ) -> bool:
        """
        Render a subgraph to an SVG file using Graphviz.
        
        Args:
            center_symbol: Center node
            output_path: Where to save the SVG
            depth: Hops to include
            direction: "in", "out", or "both"
        
        Returns:
            True if successful, False otherwise
        """
        dot_content = self.generate_graphviz(center_symbol, depth, direction)
        
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", 
                suffix=".dot", 
                delete=False
            ) as f:
                f.write(dot_content)
                dot_file = f.name
            
            result = subprocess.run(
                ["dot", "-Tsvg", dot_file, "-o", str(output_path)],
                capture_output=True,
                text=True,
            )
            
            return result.returncode == 0
            
        except FileNotFoundError:
            # Graphviz not installed
            return False
        except Exception:
            return False

    def generate_file_diagram(
        self,
        file_path: Path,
        output_path: Optional[Path] = None,
    ) -> str:
        """
        Generate a diagram showing dependencies for all symbols in a file.
        
        Args:
            file_path: Path to the source file
            output_path: Optional path to save SVG
        
        Returns:
            Mermaid diagram definition
        """
        edges = self.store.get_file_dependencies(file_path)
        
        if not edges:
            return f"flowchart TD\n    note[No dependencies found for {file_path.name}]"
        
        lines = ["flowchart LR"]
        added_nodes: set[str] = set()
        
        def get_node_id(name: str) -> str:
            return name.replace("::", "_").replace("<", "_").replace(">", "_").replace(" ", "_").replace("/", "_").replace("\\", "_")
        
        for edge in edges:
            source_id = get_node_id(edge.source_qualified_name)
            target_id = get_node_id(edge.target_qualified_name)
            
            source_display = edge.source_qualified_name.split("::")[-1]
            target_display = edge.target_qualified_name.split("::")[-1]
            
            if edge.source_qualified_name not in added_nodes:
                lines.append(f'    {source_id}["{source_display}"]')
                added_nodes.add(edge.source_qualified_name)
            
            if edge.target_qualified_name not in added_nodes:
                lines.append(f'    {target_id}["{target_display}"]')
                added_nodes.add(edge.target_qualified_name)
            
            if edge.edge_type == EdgeType.INHERITS:
                lines.append(f"    {source_id} -->|extends| {target_id}")
            elif edge.edge_type == EdgeType.USES:
                lines.append(f"    {source_id} -.-> {target_id}")
            elif edge.edge_type != EdgeType.CONTAINS:
                lines.append(f"    {source_id} --> {target_id}")
        
        return "\n".join(lines)
