"""SQLite backend wrapper for ULE."""

import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Any


class SQLiteBackend:
    """Low-level SQLite backend for ULE storage."""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self._conn: Optional[sqlite3.Connection] = None
    
    def connect(self) -> None:
        """Connect to SQLite database."""
        self._conn = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False,
            isolation_level=None
        )
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA cache_size=-64000")  # 64MB cache
        self._conn.row_factory = sqlite3.Row
    
    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute SQL statement."""
        return self._conn.execute(sql, params)
    
    def executemany(self, sql: str, params_list: list) -> sqlite3.Cursor:
        """Execute SQL with multiple parameter sets."""
        return self._conn.executemany(sql, params_list)
    
    def fetchall(self, sql: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Execute and fetch all results."""
        cursor = self._conn.execute(sql, params)
        return cursor.fetchall()
    
    def fetchone(self, sql: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """Execute and fetch one result."""
        cursor = self._conn.execute(sql, params)
        return cursor.fetchone()
    
    def commit(self) -> None:
        """Commit transaction."""
        self._conn.commit()
    
    def rollback(self) -> None:
        """Rollback transaction."""
        self._conn.rollback()
    
    def close(self) -> None:
        """Close connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
    
    def table_exists(self, table_name: str) -> bool:
        """Check if table exists."""
        cursor = self._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        return cursor.fetchone() is not None
    
    def get_tables(self) -> List[str]:
        """List all user tables."""
        cursor = self._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '_%'"
        )
        return [row[0] for row in cursor]
    
    def get_schema(self, table_name: str) -> List[Dict]:
        """Get table schema."""
        cursor = self._conn.execute(f"PRAGMA table_info({table_name})")
        
        return [
            {
                "cid": row[0],
                "name": row[1],
                "type": row[2],
                "notnull": row[3],
                "default": row[4],
                "pk": row[5]
            }
            for row in cursor
        ]
    
    def create_index(self, table_name: str, columns: List[str], 
                     unique: bool = False) -> None:
        """Create index on table."""
        index_name = f"idx_{table_name}_{'_'.join(columns)}"
        unique_str = "UNIQUE " if unique else ""
        
        sql = f"CREATE {unique_str}INDEX IF NOT EXISTS {index_name} ON {table_name} ({', '.join(columns)})"
        self._conn.execute(sql)
        self._conn.commit()
    
    def analyze(self, table_name: str = None) -> None:
        """Run ANALYZE for query optimization."""
        if table_name:
            self._conn.execute(f"ANALYZE {table_name}")
        else:
            self._conn.execute("ANALYZE")
        self._conn.commit()
