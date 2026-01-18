"""
SQLite-backed persistent storage for the dependency graph.

Designed for scalability with 5k+ file codebases:
- All data stored on disk, not in memory
- Indexed queries for fast lookups
- Idempotent upserts for incremental updates
"""

import sqlite3
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

from autodocgen.graph.models import (
    NodeType,
    EdgeType,
    DependencyNode,
    DependencyEdge,
    DependencyQueryResult,
)


class DependencyStore:
    """
    SQLite-backed storage for dependency graph data.
    
    Optimized for large codebases with indexed lookups
    and streaming inserts.
    """

    def __init__(self, db_path: Path):
        """
        Initialize the dependency store.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_tables()

    @contextmanager
    def _get_connection(self):
        """Get a database connection with proper cleanup."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _ensure_tables(self) -> None:
        """Create tables and indexes if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Nodes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dependency_nodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    qualified_name TEXT UNIQUE NOT NULL,
                    node_type TEXT NOT NULL,
                    file_path TEXT,
                    line_number INTEGER
                )
            """)
            
            # Edges table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dependency_edges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_qualified_name TEXT NOT NULL,
                    target_qualified_name TEXT NOT NULL,
                    edge_type TEXT NOT NULL,
                    context TEXT,
                    UNIQUE(source_qualified_name, target_qualified_name, edge_type)
                )
            """)
            
            # Indexes for fast lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_nodes_name 
                ON dependency_nodes(name)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_nodes_file 
                ON dependency_nodes(file_path)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_nodes_qualified 
                ON dependency_nodes(qualified_name)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_edges_source 
                ON dependency_edges(source_qualified_name)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_edges_target 
                ON dependency_edges(target_qualified_name)
            """)

    def upsert_node(self, node: DependencyNode) -> int:
        """
        Insert or update a node.
        
        Returns:
            The node ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO dependency_nodes 
                    (name, qualified_name, node_type, file_path, line_number)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(qualified_name) DO UPDATE SET
                    name = excluded.name,
                    node_type = excluded.node_type,
                    file_path = excluded.file_path,
                    line_number = excluded.line_number
            """, (
                node.name,
                node.qualified_name,
                node.node_type.value,
                str(node.file_path) if node.file_path else None,
                node.line_number,
            ))
            
            # Get the ID
            cursor.execute(
                "SELECT id FROM dependency_nodes WHERE qualified_name = ?",
                (node.qualified_name,)
            )
            return cursor.fetchone()[0]

    def upsert_edge(self, edge: DependencyEdge) -> int:
        """
        Insert or update an edge.
        
        Returns:
            The edge ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO dependency_edges 
                    (source_qualified_name, target_qualified_name, edge_type, context)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(source_qualified_name, target_qualified_name, edge_type) 
                DO UPDATE SET context = excluded.context
            """, (
                edge.source_qualified_name,
                edge.target_qualified_name,
                edge.edge_type.value,
                edge.context,
            ))
            
            cursor.execute(
                """SELECT id FROM dependency_edges 
                   WHERE source_qualified_name = ? 
                   AND target_qualified_name = ? 
                   AND edge_type = ?""",
                (edge.source_qualified_name, edge.target_qualified_name, edge.edge_type.value)
            )
            return cursor.fetchone()[0]

    def delete_file_nodes(self, file_path: Path) -> int:
        """
        Delete all nodes (and their edges) from a specific file.
        Used for incremental updates when a file changes.
        
        Returns:
            Number of nodes deleted
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            file_str = str(file_path)
            
            # Get nodes to delete
            cursor.execute(
                "SELECT qualified_name FROM dependency_nodes WHERE file_path = ?",
                (file_str,)
            )
            node_names = [row[0] for row in cursor.fetchall()]
            
            if not node_names:
                return 0
            
            # Delete edges involving these nodes
            placeholders = ",".join("?" * len(node_names))
            cursor.execute(f"""
                DELETE FROM dependency_edges 
                WHERE source_qualified_name IN ({placeholders})
                   OR target_qualified_name IN ({placeholders})
            """, node_names + node_names)
            
            # Delete the nodes
            cursor.execute(
                f"DELETE FROM dependency_nodes WHERE file_path = ?",
                (file_str,)
            )
            
            return len(node_names)

    def get_node(self, qualified_name: str) -> Optional[DependencyNode]:
        """Get a node by its qualified name."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM dependency_nodes WHERE qualified_name = ?",
                (qualified_name,)
            )
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return DependencyNode(
                id=row["id"],
                name=row["name"],
                qualified_name=row["qualified_name"],
                node_type=NodeType(row["node_type"]),
                file_path=Path(row["file_path"]) if row["file_path"] else None,
                line_number=row["line_number"],
            )

    def get_dependencies(self, qualified_name: str) -> list[DependencyEdge]:
        """Get all edges where this node is the source (what it depends on)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM dependency_edges WHERE source_qualified_name = ?",
                (qualified_name,)
            )
            
            return [
                DependencyEdge(
                    id=row["id"],
                    source_qualified_name=row["source_qualified_name"],
                    target_qualified_name=row["target_qualified_name"],
                    edge_type=EdgeType(row["edge_type"]),
                    context=row["context"],
                )
                for row in cursor.fetchall()
            ]

    def get_dependents(self, qualified_name: str) -> list[DependencyEdge]:
        """Get all edges where this node is the target (what depends on it)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM dependency_edges WHERE target_qualified_name = ?",
                (qualified_name,)
            )
            
            return [
                DependencyEdge(
                    id=row["id"],
                    source_qualified_name=row["source_qualified_name"],
                    target_qualified_name=row["target_qualified_name"],
                    edge_type=EdgeType(row["edge_type"]),
                    context=row["context"],
                )
                for row in cursor.fetchall()
            ]

    def get_subgraph(
        self, 
        qualified_name: str, 
        depth: int = 1,
        direction: str = "both"
    ) -> DependencyQueryResult:
        """
        Get a subgraph centered on a node, up to N hops away.
        
        Args:
            qualified_name: Center node
            depth: How many hops to traverse
            direction: "in" (dependents), "out" (dependencies), or "both"
        
        Returns:
            Query result with node, edges, and related nodes
        """
        node = self.get_node(qualified_name)
        if not node:
            return DependencyQueryResult(
                node=DependencyNode(
                    name=qualified_name.split("::")[-1],
                    qualified_name=qualified_name,
                    node_type=NodeType.CLASS,
                ),
                edges=[],
                related_nodes=[],
            )
        
        all_edges: list[DependencyEdge] = []
        visited_names: set[str] = {qualified_name}
        frontier: set[str] = {qualified_name}
        
        for _ in range(depth):
            new_frontier: set[str] = set()
            
            for name in frontier:
                if direction in ("out", "both"):
                    deps = self.get_dependencies(name)
                    all_edges.extend(deps)
                    new_frontier.update(e.target_qualified_name for e in deps)
                
                if direction in ("in", "both"):
                    deps = self.get_dependents(name)
                    all_edges.extend(deps)
                    new_frontier.update(e.source_qualified_name for e in deps)
            
            new_frontier -= visited_names
            visited_names.update(new_frontier)
            frontier = new_frontier
        
        # Get all related nodes
        related_nodes: list[DependencyNode] = []
        for name in visited_names:
            if name != qualified_name:
                related = self.get_node(name)
                if related:
                    related_nodes.append(related)
        
        return DependencyQueryResult(
            node=node,
            edges=list(set(all_edges)),
            related_nodes=related_nodes,
        )

    def get_file_dependencies(self, file_path: Path) -> list[DependencyEdge]:
        """Get all edges for nodes in a specific file."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            file_str = str(file_path)
            
            # Get nodes in this file
            cursor.execute(
                "SELECT qualified_name FROM dependency_nodes WHERE file_path = ?",
                (file_str,)
            )
            node_names = [row[0] for row in cursor.fetchall()]
            
            if not node_names:
                return []
            
            # Get edges from these nodes
            placeholders = ",".join("?" * len(node_names))
            cursor.execute(f"""
                SELECT * FROM dependency_edges 
                WHERE source_qualified_name IN ({placeholders})
            """, node_names)
            
            return [
                DependencyEdge(
                    id=row["id"],
                    source_qualified_name=row["source_qualified_name"],
                    target_qualified_name=row["target_qualified_name"],
                    edge_type=EdgeType(row["edge_type"]),
                    context=row["context"],
                )
                for row in cursor.fetchall()
            ]

    def get_statistics(self) -> dict:
        """Get graph statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM dependency_nodes")
            node_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM dependency_edges")
            edge_count = cursor.fetchone()[0]
            
            cursor.execute(
                "SELECT node_type, COUNT(*) FROM dependency_nodes GROUP BY node_type"
            )
            type_counts = {row[0]: row[1] for row in cursor.fetchall()}
            
            return {
                "total_nodes": node_count,
                "total_edges": edge_count,
                "nodes_by_type": type_counts,
            }

    def clear(self) -> None:
        """Clear all data from the graph."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM dependency_edges")
            cursor.execute("DELETE FROM dependency_nodes")
