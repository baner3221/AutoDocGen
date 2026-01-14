"""
SQLite database for documentation storage and indexing.
"""

import sqlite3
from pathlib import Path
from typing import Optional
from datetime import datetime

from autodocgen.config import Config


class Database:
    """
    SQLite database for storing documentation and enabling search.

    Uses FTS5 for full-text search capabilities.
    """

    def __init__(self, config: Config):
        """
        Initialize the database.

        Args:
            config: AutoDocGen configuration
        """
        self.config = config
        self.db_path = config.database_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        """Initialize the database schema."""
        self.conn.executescript("""
            -- Files table
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY,
                path TEXT UNIQUE NOT NULL,
                relative_path TEXT NOT NULL,
                hash TEXT NOT NULL,
                last_analyzed TIMESTAMP,
                line_count INTEGER,
                class_count INTEGER DEFAULT 0,
                function_count INTEGER DEFAULT 0,
                doc_generated BOOLEAN DEFAULT FALSE
            );

            -- Symbols table
            CREATE TABLE IF NOT EXISTS symbols (
                id INTEGER PRIMARY KEY,
                file_id INTEGER REFERENCES files(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                qualified_name TEXT NOT NULL,
                kind TEXT NOT NULL,
                line_start INTEGER,
                line_end INTEGER,
                signature TEXT,
                brief_description TEXT,
                documentation TEXT,
                doc_hash TEXT,
                UNIQUE(file_id, qualified_name)
            );

            -- Relationships between symbols
            CREATE TABLE IF NOT EXISTS relationships (
                id INTEGER PRIMARY KEY,
                source_id INTEGER REFERENCES symbols(id) ON DELETE CASCADE,
                target_id INTEGER REFERENCES symbols(id) ON DELETE CASCADE,
                relationship_type TEXT NOT NULL,
                UNIQUE(source_id, target_id, relationship_type)
            );

            -- Full-text search index
            CREATE VIRTUAL TABLE IF NOT EXISTS symbol_search USING fts5(
                name,
                qualified_name,
                documentation,
                content='symbols',
                content_rowid='id'
            );

            -- Triggers to keep FTS in sync
            CREATE TRIGGER IF NOT EXISTS symbols_ai AFTER INSERT ON symbols BEGIN
                INSERT INTO symbol_search(rowid, name, qualified_name, documentation)
                VALUES (new.id, new.name, new.qualified_name, new.documentation);
            END;

            CREATE TRIGGER IF NOT EXISTS symbols_ad AFTER DELETE ON symbols BEGIN
                INSERT INTO symbol_search(symbol_search, rowid, name, qualified_name, documentation)
                VALUES ('delete', old.id, old.name, old.qualified_name, old.documentation);
            END;

            CREATE TRIGGER IF NOT EXISTS symbols_au AFTER UPDATE ON symbols BEGIN
                INSERT INTO symbol_search(symbol_search, rowid, name, qualified_name, documentation)
                VALUES ('delete', old.id, old.name, old.qualified_name, old.documentation);
                INSERT INTO symbol_search(rowid, name, qualified_name, documentation)
                VALUES (new.id, new.name, new.qualified_name, new.documentation);
            END;

            -- Indexes
            CREATE INDEX IF NOT EXISTS idx_symbols_file ON symbols(file_id);
            CREATE INDEX IF NOT EXISTS idx_symbols_kind ON symbols(kind);
            CREATE INDEX IF NOT EXISTS idx_symbols_name ON symbols(name);
            CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships(source_id);
            CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships(target_id);
        """)
        self.conn.commit()

    # File operations
    def upsert_file(
        self,
        path: Path,
        relative_path: str,
        file_hash: str,
        line_count: int,
        class_count: int = 0,
        function_count: int = 0,
    ) -> int:
        """Insert or update a file record."""
        cursor = self.conn.execute(
            """
            INSERT INTO files (path, relative_path, hash, last_analyzed, line_count, class_count, function_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
                hash = excluded.hash,
                last_analyzed = excluded.last_analyzed,
                line_count = excluded.line_count,
                class_count = excluded.class_count,
                function_count = excluded.function_count
            RETURNING id
            """,
            (str(path), relative_path, file_hash, datetime.now(), line_count, class_count, function_count),
        )
        self.conn.commit()
        return cursor.fetchone()[0]

    def get_file(self, path: Path) -> Optional[sqlite3.Row]:
        """Get a file record by path."""
        cursor = self.conn.execute(
            "SELECT * FROM files WHERE path = ?",
            (str(path),),
        )
        return cursor.fetchone()

    def file_changed(self, path: Path, new_hash: str) -> bool:
        """Check if a file has changed since last analysis."""
        file_row = self.get_file(path)
        if not file_row:
            return True
        return file_row["hash"] != new_hash

    def mark_documented(self, file_id: int) -> None:
        """Mark a file as documented."""
        self.conn.execute(
            "UPDATE files SET doc_generated = TRUE WHERE id = ?",
            (file_id,),
        )
        self.conn.commit()

    # Symbol operations
    def upsert_symbol(
        self,
        file_id: int,
        name: str,
        qualified_name: str,
        kind: str,
        line_start: int,
        line_end: int,
        signature: str = "",
        brief_description: str = "",
        documentation: str = "",
    ) -> int:
        """Insert or update a symbol."""
        cursor = self.conn.execute(
            """
            INSERT INTO symbols (file_id, name, qualified_name, kind, line_start, line_end, signature, brief_description, documentation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(file_id, qualified_name) DO UPDATE SET
                line_start = excluded.line_start,
                line_end = excluded.line_end,
                signature = excluded.signature,
                brief_description = excluded.brief_description,
                documentation = excluded.documentation
            RETURNING id
            """,
            (file_id, name, qualified_name, kind, line_start, line_end, signature, brief_description, documentation),
        )
        self.conn.commit()
        return cursor.fetchone()[0]

    def get_symbol(self, qualified_name: str) -> Optional[sqlite3.Row]:
        """Get a symbol by qualified name."""
        cursor = self.conn.execute(
            "SELECT * FROM symbols WHERE qualified_name = ?",
            (qualified_name,),
        )
        return cursor.fetchone()

    def get_symbols_in_file(self, file_id: int) -> list[sqlite3.Row]:
        """Get all symbols in a file."""
        cursor = self.conn.execute(
            "SELECT * FROM symbols WHERE file_id = ? ORDER BY line_start",
            (file_id,),
        )
        return cursor.fetchall()

    # Relationship operations
    def add_relationship(
        self,
        source_id: int,
        target_id: int,
        relationship_type: str,
    ) -> None:
        """Add a relationship between symbols."""
        self.conn.execute(
            """
            INSERT OR IGNORE INTO relationships (source_id, target_id, relationship_type)
            VALUES (?, ?, ?)
            """,
            (source_id, target_id, relationship_type),
        )
        self.conn.commit()

    def get_relationships(self, symbol_id: int) -> list[sqlite3.Row]:
        """Get all relationships for a symbol."""
        cursor = self.conn.execute(
            """
            SELECT r.*, s.qualified_name as target_name
            FROM relationships r
            JOIN symbols s ON r.target_id = s.id
            WHERE r.source_id = ?
            """,
            (symbol_id,),
        )
        return cursor.fetchall()

    # Search operations
    def search(self, query: str, limit: int = 50) -> list[sqlite3.Row]:
        """Search for symbols."""
        cursor = self.conn.execute(
            """
            SELECT s.*, f.relative_path as file_path
            FROM symbol_search ss
            JOIN symbols s ON ss.rowid = s.id
            JOIN files f ON s.file_id = f.id
            WHERE symbol_search MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (query, limit),
        )
        return cursor.fetchall()

    # Statistics
    def get_stats(self) -> dict:
        """Get database statistics."""
        cursor = self.conn.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM files) as file_count,
                (SELECT COUNT(*) FROM files WHERE doc_generated = TRUE) as documented_count,
                (SELECT COUNT(*) FROM symbols) as symbol_count,
                (SELECT COUNT(*) FROM symbols WHERE kind = 'class') as class_count,
                (SELECT COUNT(*) FROM symbols WHERE kind = 'function') as function_count,
                (SELECT COUNT(*) FROM relationships) as relationship_count
            """
        )
        row = cursor.fetchone()
        return dict(row)

    def close(self) -> None:
        """Close the database connection."""
        self.conn.close()
