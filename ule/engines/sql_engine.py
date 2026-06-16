"""SQL Engine for ULE - Parse and execute SQL queries."""

import re
from typing import List, Dict, Any, Optional, Tuple


class SQLEngine:
    """
    SQL query engine with parser and executor.
    
    Supports: CREATE, INSERT, SELECT, UPDATE, DELETE, DROP
    """
    
    def __init__(self, db_connection):
        self._conn = db_connection

    def _quote(self, identifier: str) -> str:
        """Safely quote a SQL identifier (table or column name)."""
        return '"{0}"'.format(identifier.replace('"', '""'))
    
    def execute(self, sql: str, params: tuple = ()) -> List[Dict]:
        """
        Execute SQL query.
        
        Args:
            sql: SQL statement
            params: Query parameters
        
        Returns:
            Query results for SELECT, empty list for others
        """
        sql = sql.strip()
        sql_upper = sql.upper()
        
        # Determine query type
        if sql_upper.startswith("SELECT"):
            return self._select(sql, params)
        elif sql_upper.startswith("INSERT"):
            self._insert(sql, params)
            return []
        elif sql_upper.startswith("UPDATE"):
            self._update(sql, params)
            return []
        elif sql_upper.startswith("DELETE"):
            self._delete(sql, params)
            return []
        elif sql_upper.startswith("CREATE"):
            self._create(sql, params)
            return []
        elif sql_upper.startswith("DROP"):
            self._drop(sql, params)
            return []
        elif sql_upper.startswith("ALTER"):
            self._alter(sql, params)
            return []
        else:
            raise ValueError(f"Unsupported SQL statement: {sql[:50]}")
    
    def _select(self, sql: str, params: tuple) -> List[Dict]:
        """Execute SELECT query."""
        cursor = self._conn.execute(sql, params)
        
        if cursor.description:
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        return []
    
    def _insert(self, sql: str, params: tuple) -> None:
        """Execute INSERT query."""
        self._conn.execute(sql, params)
        self._conn.commit()
    
    def _update(self, sql: str, params: tuple) -> None:
        """Execute UPDATE query."""
        self._conn.execute(sql, params)
        self._conn.commit()
    
    def _delete(self, sql: str, params: tuple) -> None:
        """Execute DELETE query."""
        self._conn.execute(sql, params)
        self._conn.commit()
    
    def _create(self, sql: str, params: tuple) -> None:
        """Execute CREATE query."""
        self._conn.execute(sql, params)
        self._conn.commit()
    
    def _drop(self, sql: str, params: tuple) -> None:
        """Execute DROP query."""
        self._conn.execute(sql, params)
        self._conn.commit()
    
    def _alter(self, sql: str, params: tuple) -> None:
        """Execute ALTER query."""
        self._conn.execute(sql, params)
        self._conn.commit()
    
    def create_table(self, table_name: str, columns: Dict[str, str]) -> None:
        """
        Create a new table.
        
        Args:
            table_name: Table name
            columns: Column definitions {name: type}
        """
        safe_table = self._quote(table_name)
        col_defs = ", ".join(f"{self._quote(name)} {dtype}" for name, dtype in columns.items())
        sql = f"CREATE TABLE {safe_table} ({col_defs})"
        self._conn.execute(sql)
        self._conn.commit()
    
    def insert_row(self, table_name: str, data: Dict[str, Any]) -> int:
        """
        Insert a row.
        
        Args:
            table_name: Table name
            data: Column values {column: value}
        
        Returns:
            Last inserted row ID
        """
        safe_table = self._quote(table_name)
        safe_cols = ", ".join(self._quote(k) for k in data.keys())
        placeholders = ", ".join("?" * len(data))
        sql = f"INSERT INTO {safe_table} ({safe_cols}) VALUES ({placeholders})"
        
        self._conn.execute(sql, tuple(data.values()))
        self._conn.commit()
        
        cursor = self._conn.execute("SELECT last_insert_rowid()")
        return cursor.fetchone()[0]
    
    def select_rows(self, table_name: str, columns: List[str] = None,
                    where: str = None, params: tuple = None,
                    order_by: str = None, limit: int = None) -> List[Dict]:
        """
        Select rows from table.
        
        Args:
            table_name: Table name
            columns: Columns to select (None for all)
            where: WHERE clause (without 'WHERE')
            params: WHERE parameters
            order_by: ORDER BY clause
            limit: LIMIT value
        
        Returns:
            List of rows as dicts
        """
        safe_table = self._quote(table_name)
        safe_cols = ", ".join(self._quote(c) for c in columns) if columns else "*"
        sql = f"SELECT {safe_cols} FROM {safe_table}"
        
        query_params = list(params) if params else []
        
        if where:
            sql += f" WHERE {where}"
        
        if order_by:
            # Note: order_by could be complex, ideally should be quoted too if simple
            sql += f" ORDER BY {order_by}"
        
        if limit:
            sql += f" LIMIT ?"
            query_params.append(limit)
        
        cursor = self._conn.execute(sql, tuple(query_params))
        
        if cursor.description:
            cols = [desc[0] for desc in cursor.description]
            return [dict(zip(cols, row)) for row in cursor.fetchall()]
        
        return []
    
    def update_rows(self, table_name: str, data: Dict[str, Any],
                    where: str, params: tuple = None) -> int:
        """
        Update rows.
        
        Args:
            table_name: Table name
            data: New values {column: value}
            where: WHERE clause
            params: WHERE parameters
        
        Returns:
            Number of rows affected
        """
        safe_table = self._quote(table_name)
        set_clause = ", ".join(f"{self._quote(col)} = ?" for col in data.keys())
        sql = f"UPDATE {safe_table} SET {set_clause}"
        
        query_params = list(data.values())
        if params:
            sql += f" WHERE {where}"
            query_params.extend(params)
        
        cursor = self._conn.execute(sql, tuple(query_params))
        self._conn.commit()
        
        return cursor.rowcount
    
    def delete_rows(self, table_name: str, where: str, 
                    params: tuple = None) -> int:
        """
        Delete rows.
        
        Args:
            table_name: Table name
            where: WHERE clause
            params: WHERE parameters
        
        Returns:
            Number of rows deleted
        """
        safe_table = self._quote(table_name)
        sql = f"DELETE FROM {safe_table} WHERE {where}"
        cursor = self._conn.execute(sql, params or ())
        self._conn.commit()
        return cursor.rowcount
    
    def count(self, table_name: str, where: str = None, 
              params: tuple = None) -> int:
        """Count rows in table."""
        safe_table = self._quote(table_name)
        sql = f"SELECT COUNT(*) FROM {safe_table}"
        
        if where:
            sql += f" WHERE {where}"
        
        cursor = self._conn.execute(sql, params or ())
        return cursor.fetchone()[0]
    
    def exists(self, table_name: str, where: str, 
               params: tuple = None) -> bool:
        """Check if rows exist."""
        safe_table = self._quote(table_name)
        sql = f"SELECT 1 FROM {safe_table} WHERE {where} LIMIT 1"
        cursor = self._conn.execute(sql, params or ())
        return cursor.fetchone() is not None
    
    def get_tables(self) -> List[str]:
        """List all user tables."""
        cursor = self._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND substr(name, 1, 1) != '_'"
        )
        return [row[0] for row in cursor]
    
    def get_schema(self, table_name: str) -> List[Dict]:
        """Get table schema."""
        # Using PRAGMA table_info is safe if table_name is properly handled
        safe_table = self._quote(table_name)
        cursor = self._conn.execute(f"PRAGMA table_info({safe_table})")
        
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
    
    def drop_table(self, table_name: str) -> None:
        """Drop a table."""
        safe_table = self._quote(table_name)
        self._conn.execute(f"DROP TABLE IF EXISTS {safe_table}")
        self._conn.commit()
    
    def truncate(self, table_name: str) -> None:
        """Truncate a table."""
        safe_table = self._quote(table_name)
        self._conn.execute(f"DELETE FROM {safe_table}")
        self._conn.commit()
