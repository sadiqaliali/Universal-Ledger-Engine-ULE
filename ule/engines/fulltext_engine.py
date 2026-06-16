"""Full-Text Search Engine for ULE.

Advanced text search with:
- Full-text indexing
- Relevance ranking
- Phrase search
- Wildcard search
- Highlighting
"""

import sqlite3
import re
import json
from datetime import datetime
from typing import Optional, Dict, List, Any, Set
from collections import defaultdict


class FullTextEngine:
    """Full-text search engine for ULE."""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn
        self._indexes: Dict[str, Dict[str, Set[int]]] = {}

    def create_index(self, index_name: str, table: str, columns: List[str]):
        """Create a full-text index on table columns."""
        # Create FTS5 virtual table
        fts_table = f"fts_{index_name}"
        cols = ', '.join(columns)
        
        self._conn.execute(f"DROP TABLE IF EXISTS {fts_table}")
        self._conn.execute(f"CREATE VIRTUAL TABLE {fts_table} USING fts5({cols})")
        
        # Populate FTS table from source table
        cursor = self._conn.execute(f"SELECT rowid, {cols} FROM {table}")
        rows = cursor.fetchall()
        
        for row in rows:
            rowid = row[0]
            values = row[1:]
            placeholders = ', '.join(['?' for _ in values])
            self._conn.execute(
                f"INSERT INTO {fts_table} (rowid, {cols}) VALUES ({rowid}, {placeholders})",
                (rowid,) + values
            )
        
        self._conn.commit()
        self._indexes[index_name] = {'table': table, 'columns': columns, 'fts_table': fts_table}

    def search(self, index_name: str, query: str, limit: int = 20) -> List[Dict]:
        """Search the full-text index."""
        if index_name not in self._indexes:
            raise ValueError(f"Index '{index_name}' not found")
        
        fts_table = self._indexes[index_name]['fts_table']
        source_table = self._indexes[index_name]['table']
        
        # Use FTS5 search
        cursor = self._conn.execute(
            f"""SELECT f.rowid, f.rank, s.*
                FROM {fts_table} f
                JOIN {source_table} s ON f.rowid = s.rowid
                WHERE {fts_table} MATCH ?
                ORDER BY rank
                LIMIT ?""",
            (query, limit)
        )
        
        columns = [d[0] for d in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def search_phrase(self, index_name: str, phrase: str, limit: int = 20) -> List[Dict]:
        """Search for an exact phrase."""
        if index_name not in self._indexes:
            raise ValueError(f"Index '{index_name}' not found")
        
        fts_table = self._indexes[index_name]['fts_table']
        source_table = self._indexes[index_name]['table']
        
        # Phrase search with quotes
        cursor = self._conn.execute(
            f"""SELECT f.rowid, f.rank, s.*
                FROM {fts_table} f
                JOIN {source_table} s ON f.rowid = s.rowid
                WHERE {fts_table} MATCH ?
                ORDER BY rank
                LIMIT ?""",
            (f'"{phrase}"', limit)
        )
        
        columns = [d[0] for d in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def search_wildcard(self, index_name: str, pattern: str, limit: int = 20) -> List[Dict]:
        """Search with wildcard pattern."""
        if index_name not in self._indexes:
            raise ValueError(f"Index '{index_name}' not found")
        
        fts_table = self._indexes[index_name]['fts_table']
        source_table = self._indexes[index_name]['table']
        
        cursor = self._conn.execute(
            f"""SELECT f.rowid, f.rank, s.*
                FROM {fts_table} f
                JOIN {source_table} s ON f.rowid = s.rowid
                WHERE {fts_table} MATCH ?
                ORDER BY rank
                LIMIT ?""",
            (pattern, limit)
        )
        
        columns = [d[0] for d in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def highlight(self, index_name: str, doc_id: int, query: str) -> Dict[str, Any]:
        """Get highlighted snippets for a document."""
        if index_name not in self._indexes:
            raise ValueError(f"Index '{index_name}' not found")
        
        fts_table = self._indexes[index_name]['fts_table']
        columns = self._indexes[index_name]['columns']
        
        # Get the document
        cursor = self._conn.execute(
            f"SELECT * FROM {fts_table} WHERE rowid = ?",
            (doc_id,)
        )
        row = cursor.fetchone()
        
        if not row:
            return {}
        
        result = {'id': doc_id}
        for i, col in enumerate(columns):
            text = row[i]
            # Highlight matching terms
            terms = query.lower().split()
            highlighted = text
            for term in terms:
                pattern = re.compile(re.escape(term), re.IGNORECASE)
                highlighted = pattern.sub(f'<mark>{term}</mark>', highlighted)
            result[col] = highlighted
        
        return result

    def suggest(self, index_name: str, prefix: str, limit: int = 10) -> List[str]:
        """Get autocomplete suggestions for a prefix."""
        if index_name not in self._indexes:
            raise ValueError(f"Index '{index_name}' not found")
        
        fts_table = self._indexes[index_name]['fts_table']
        
        # Use FTS5 autocomplete
        cursor = self._conn.execute(
            f"SELECT DISTINCT * FROM {fts_table} WHERE {fts_table} MATCH ? LIMIT ?",
            (f'{prefix}*', limit)
        )
        
        suggestions = set()
        for row in cursor.fetchall():
            for val in row:
                if isinstance(val, str) and prefix.lower() in val.lower():
                    # Extract matching words
                    words = re.findall(r'\b\w+\b', val)
                    for word in words:
                        if word.lower().startswith(prefix.lower()):
                            suggestions.add(word)
        
        return list(suggestions)[:limit]

    def update_document(self, index_name: str, doc_id: int, **kwargs):
        """Update a document in the index."""
        if index_name not in self._indexes:
            raise ValueError(f"Index '{index_name}' not found")
        
        fts_table = self._indexes[index_name]['fts_table']
        columns = self._indexes[index_name]['columns']
        
        # Delete old version
        self._conn.execute(f"DELETE FROM {fts_table} WHERE rowid = ?", (doc_id,))
        
        # Insert new version
        update_cols = []
        values = []
        for col in columns:
            if col in kwargs:
                update_cols.append(col)
                values.append(kwargs[col])
            else:
                update_cols.append(col)
                values.append('')
        
        if update_cols:
            placeholders = ', '.join(['?' for _ in values])
            col_names = ', '.join(update_cols)
            self._conn.execute(
                f"INSERT INTO {fts_table} (rowid, {col_names}) VALUES (?, {placeholders})",
                (doc_id,) + tuple(values)
            )
        
        self._conn.commit()

    def delete_document(self, index_name: str, doc_id: int):
        """Delete a document from the index."""
        if index_name not in self._indexes:
            raise ValueError(f"Index '{index_name}' not found")
        
        fts_table = self._indexes[index_name]['fts_table']
        self._conn.execute(f"DELETE FROM {fts_table} WHERE rowid = ?", (doc_id,))
        self._conn.commit()

    def get_stats(self, index_name: str) -> Dict[str, Any]:
        """Get index statistics."""
        if index_name not in self._indexes:
            raise ValueError(f"Index '{index_name}' not found")
        
        fts_table = self._indexes[index_name]['fts_table']
        
        cursor = self._conn.execute(f"SELECT COUNT(*) FROM {fts_table}")
        doc_count = cursor.fetchone()[0]
        
        return {
            'index_name': index_name,
            'document_count': doc_count,
            'columns': self._indexes[index_name]['columns']
        }
