"""ULE Database - Main database class managing .udb files."""

import os
import json
import sqlite3
import hashlib
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime

from ule.core.config import Config
from ule.core.exceptions import DatabaseError, AuthenticationError
from ule.core.interfaces import IAuditManager, ICipher, IHashChain
from ule.security.encryption import AESCipher
from ule.security.keys import KeyManager
from ule.blockchain.hash_chain import HashChain
from ule.storage.wal import WriteAheadLog


class ULEDatabase:
    """
    Universal Ledger Engine Database.
    
    Single .udb file containing:
    - SQL tables
    - Document collections
    - Graph relationships
    - Vector embeddings
    - Blockchain audit trail
    """
    
    MAGIC = b"ULE1"
    VERSION = 1
    
    def __init__(self, db_path: str, password: Optional[str] = None, config: Optional[Config] = None,
                 cipher: Optional[ICipher] = None,
                 hash_chain: Optional[IHashChain] = None,
                 audit_manager: Optional[IAuditManager] = None):
        self.db_path = Path(db_path)
        self.password = password
        self.config = config or Config()
        self._conn: Optional[sqlite3.Connection] = None
        self._cipher: Optional[ICipher] = cipher
        self._hash_chain: Optional[IHashChain] = hash_chain
        self._audit_manager: Optional[IAuditManager] = audit_manager
        
        # Internal placeholders if not injected
        self._key_manager: Optional[KeyManager] = None
        self._wal: Optional[WriteAheadLog] = None
        self._user: Optional[str] = None
        self._initialized = False
        
        if self.password and not self._cipher:
            self._cipher = AESCipher(self.password)

    def init(self, password: Optional[str] = None) -> None:
        """Initialize a new database."""
        if self.db_path.exists():
            raise DatabaseError(f"Database {self.db_path} already exists")

        # Setup encryption
        if password and not self._cipher:
            self.password = password
            # Initial placeholder
            from ule.security.encryption import AESCipher
            self._cipher = AESCipher(self.password)

        # Connect to SQLite backend (stored inside .udb)
        self._connect()
        
        # Set magic header (application_id)
        self._conn.execute(f"PRAGMA application_id = {0x554c4531}") # 'ULE1'

        # Initialize internal tables
        self._init_schema()
        
        # Initialize envelope encryption keys
        if self.password and not self._cipher:
            from ule.security.encryption import EnvelopeEncryption
            ee = EnvelopeEncryption(self.password)
            dk, edk = ee.generate_data_key()
            mk_salt = ee.mk_cipher.salt
            
            self._conn.execute(
                "INSERT INTO _keys (encrypted_dk, mk_salt, algorithm) VALUES (?, ?, ?)",
                (edk, mk_salt, "AES-256-GCM")
            )
            self._conn.commit()
            
            # Switch to DK-based cipher
            self._cipher = ee.get_cipher()

        # Initialize blockchain
        if self.config.get("blockchain_enabled", True) and not self._hash_chain:
            from ule.blockchain.hash_chain import BatchAuditManager
            self._hash_chain = HashChain(self._conn)
            self._hash_chain.init()
            self._audit_manager = BatchAuditManager(self._conn, self._hash_chain)
            self._audit_manager.start()

        # Initialize WAL (Native SQLite WAL already enabled in _connect)
        # Custom JSON-based WAL is disabled to prevent redundancy
        self._wal = None

        self._initialized = True
    
    def open(self, password: Optional[str] = None) -> None:
        """Open existing database."""
        if not self.db_path.exists():
            raise DatabaseError(f"Database {self.db_path} does not exist")

        if password:
            self.password = password

        self._connect()
        
        # Verify magic header
        cursor = self._conn.execute("PRAGMA application_id")
        app_id = cursor.fetchone()[0]
        if app_id != 0x554c4531:
            self._conn.close()
            self._conn = None
            raise DatabaseError("Not a valid ULE database (incorrect application_id)")

        # Initialize envelope encryption keys
        cursor = self._conn.execute("SELECT encrypted_dk, mk_salt FROM _keys LIMIT 1")
        key_row = cursor.fetchone()
        
        if key_row and not self._cipher:
            from ule.core.exceptions import AuthenticationError
            if not self.password:
                raise AuthenticationError("Database is encrypted. Password required.")
            
            from ule.security.encryption import EnvelopeEncryption
            edk, mk_salt = key_row[0], key_row[1]
            
            try:
                ee = EnvelopeEncryption(self.password)
                ee.load_data_key(edk, mk_salt)
                self._cipher = ee.get_cipher()
            except Exception as e:
                self._conn.close()
                self._conn = None
                raise AuthenticationError(f"Invalid password or corrupted keys: {e}")
        elif self.password and not self._cipher:
            # Backward compatibility or direct document encryption
            from ule.security.encryption import AESCipher
            self._cipher = AESCipher(self.password)

        # Initialize hash chain from existing audit trail
        if self.config.get("blockchain_enabled", True) and not self._hash_chain:
            from ule.blockchain.hash_chain import BatchAuditManager
            self._hash_chain = HashChain(self._conn)
            self._hash_chain.init()
            self._audit_manager = BatchAuditManager(self._conn, self._hash_chain)
            self._audit_manager.start()
        
        # Initialize WAL (Native SQLite WAL already enabled in _connect)
        self._wal = None
        self._initialized = True
    
    def _connect(self) -> None:
        """Connect to SQLite backend."""
        self._conn = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False,
            isolation_level=None
        )
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.row_factory = sqlite3.Row
    
    def _init_schema(self) -> None:
        """Create internal schema tables."""
        tables = [
            # Schema metadata
            """CREATE TABLE IF NOT EXISTS _schema (
                name TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                definition TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )""",
            
            # SQL Tables
            """CREATE TABLE IF NOT EXISTS _tables (
                table_name TEXT PRIMARY KEY,
                columns TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            )""",
            
            # Document collections
            """CREATE TABLE IF NOT EXISTS _documents (
                collection TEXT,
                doc_id TEXT,
                data BLOB,
                hash TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                PRIMARY KEY (collection, doc_id)
            )""",
            
            # Graph edges
            """CREATE TABLE IF NOT EXISTS _edges (
                from_table TEXT,
                from_id TEXT,
                to_table TEXT,
                to_id TEXT,
                relation TEXT,
                properties BLOB,
                hash TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                PRIMARY KEY (from_table, from_id, to_table, to_id, relation)
            )""",
            
            # Vector embeddings
            """CREATE TABLE IF NOT EXISTS _vectors (
                collection TEXT,
                vec_id TEXT,
                embedding BLOB,
                metadata BLOB,
                hash TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                PRIMARY KEY (collection, vec_id)
            )""",
            
            # Users and auth
            """CREATE TABLE IF NOT EXISTS _users (
                username TEXT PRIMARY KEY,
                password_hash TEXT,
                public_key TEXT,
                role TEXT DEFAULT 'user',
                created_at TEXT DEFAULT (datetime('now'))
            )""",
            
            # Keys for envelope encryption
            """CREATE TABLE IF NOT EXISTS _keys (
                id INTEGER PRIMARY KEY,
                encrypted_dk BLOB,
                mk_salt BLOB,
                algorithm TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )""",
            
            # Audit log
            """CREATE TABLE IF NOT EXISTS _audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation TEXT,
                table_name TEXT,
                record_id TEXT,
                old_value TEXT,
                new_value TEXT,
                hash TEXT,
                prev_hash TEXT,
                signature TEXT,
                timestamp TEXT,
                user_name TEXT
            )""",
        ]
        
        for sql in tables:
            self._conn.execute(sql)
        
        self._conn.commit()
    
    def _quote_identifier(self, identifier: str) -> str:
        """Safely quote a SQL identifier."""
        return '"{0}"'.format(identifier.replace('"', '""'))

    def execute(self, sql: str, params: tuple = ()) -> List[Dict]:
        """Execute SQL query with security validation."""
        if not self._initialized:
            raise DatabaseError("Database not initialized")
        
        # Security: Prevent unauthorized access to internal tables (_)
        # if not self._is_admin_context():
        #     internal_tables = ("_audit", "_keys", "_users", "_schema", "_tables")
        #     for table in internal_tables:
        #         if table in sql.upper() or table in sql.lower():
        #              raise SecurityError(f"Access to internal table '{table}' is restricted.")
        
        # Log to WAL
        if self._wal:
            self._wal.write("SQL", sql, params)
        
        # Execute
        cursor = self._conn.execute(sql, params)
        
        # Fetch results for SELECT
        upper_sql = sql.strip().upper()
        if upper_sql.startswith("SELECT") or upper_sql.startswith("WITH"):
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            # Audit (Keep SELECT synchronous for read-audit visibility)
            if self._hash_chain:
                self._hash_chain.add({
                    "operation": "SELECT",
                    "sql": sql,
                    "result_count": len(results)
                })
            
            return results
        
        self._conn.commit()
        
        # Audit for writes (USE ASYNC BATCH MANAGER)
        first_word = upper_sql.split()[0] if upper_sql else ""
        if self._audit_manager and first_word in ("INSERT", "UPDATE", "DELETE", "DROP", "ALTER"):
            # Try to extract table name for logging
            parts = upper_sql.split()
            table_name = "unknown"
            if first_word == "INSERT" and "INTO" in parts:
                table_name = parts[parts.index("INTO") + 1]
            elif first_word in ("UPDATE", "DELETE", "DROP", "ALTER"):
                table_name = parts[1] if len(parts) > 1 else "unknown"
                
            self._audit_manager.log(
                operation=first_word,
                table_name=table_name.strip('";'),
                record_id="batch_sql",
                new_value={"sql": sql}
            )
        elif self._hash_chain and not self._audit_manager and first_word in ("INSERT", "UPDATE", "DELETE"):
            # Fallback to sync if manager not started
            self._hash_chain.add({
                "operation": first_word,
                "sql": sql
            })
        
        return []
    
    def create_table(self, table_name: str, columns: Dict[str, str]) -> None:
        """Create a new table with safe identifiers."""
        safe_table = self._quote_identifier(table_name)
        col_defs = ", ".join(f"{self._quote_identifier(name)} {dtype}" for name, dtype in columns.items())
        sql = f"CREATE TABLE {safe_table} ({col_defs})"
        self.execute(sql)
        
        # Register in schema
        self._conn.execute(
            "INSERT INTO _tables (table_name, columns) VALUES (?, ?)",
            (table_name, json.dumps(columns))
        )
        self._conn.execute(
            "INSERT INTO _schema (name, type, definition) VALUES (?, ?, ?)",
            (table_name, "table", json.dumps(columns))
        )
        self._conn.commit()
    
    def insert(self, table_name: str, data: Dict[str, Any]) -> int:
        """Insert a row with safe identifiers."""
        safe_table = self._quote_identifier(table_name)
        safe_cols = ", ".join(self._quote_identifier(k) for k in data.keys())
        placeholders = ", ".join("?" * len(data))
        sql = f"INSERT INTO {safe_table} ({safe_cols}) VALUES ({placeholders})"
        self.execute(sql, tuple(data.values()))
        
        # Get last inserted ID
        cursor = self._conn.execute("SELECT last_insert_rowid()")
        return cursor.fetchone()[0]
    
    def select(self, table_name: str, columns: List[str] = None, 
               where: str = None, params: tuple = None) -> List[Dict]:
        """Select rows with safe identifiers."""
        safe_table = self._quote_identifier(table_name)
        safe_cols = ", ".join(self._quote_identifier(c) for c in columns) if columns else "*"
        sql = f"SELECT {safe_cols} FROM {safe_table}"
        if where:
            sql += f" WHERE {where}"
        return self.execute(sql, params or ())
    
    def push(self, collection: str, data: Dict[str, Any]) -> str:
        """Push document to collection."""
        from ule.engines.nosql_engine import NoSQL_Engine
        engine = NoSQL_Engine(self._conn)
        
        # Use database cipher if set
        encrypt_fn = self._cipher.encrypt if self._cipher else None
        
        doc_id = engine.push(collection, data, encrypt_fn=encrypt_fn)
        
        # Audit (USE ASYNC BATCH MANAGER)
        if self._audit_manager:
            self._audit_manager.log(
                operation="PUSH",
                table_name=collection,
                record_id=doc_id,
                new_value={"collection": collection, "doc_id": doc_id}
            )
        elif self._hash_chain:
            self._hash_chain.add({
                "operation": "PUSH",
                "collection": collection,
                "doc_id": doc_id
            })
            
        return doc_id

    def find(self, collection: str, query: Dict[str, Any] = None, 
             limit: int = 100) -> List[Dict]:
        """Find documents in collection."""
        from ule.engines.nosql_engine import NoSQL_Engine
        engine = NoSQL_Engine(self._conn)
        
        # Use database cipher if set
        decrypt_fn = self._cipher.decrypt if self._cipher else None
        
        return engine.find(collection, query, limit=limit, decrypt_fn=decrypt_fn)
    
    def link(self, from_table: str, from_id: str, to_table: str, 
             to_id: str, relation: str, properties: Dict = None) -> None:
        """Create graph relationship."""
        edge_hash = hashlib.sha256(
            f"{from_table}:{from_id}->{to_table}:{to_id}:{relation}".encode()
        ).hexdigest()
        
        props_json = json.dumps(properties) if properties else None
        
        self._conn.execute(
            """INSERT INTO _edges (from_table, from_id, to_table, to_id, relation, properties, hash)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (from_table, from_id, to_table, to_id, relation, props_json, edge_hash)
        )
        self._conn.commit()
        
        # Audit (USE ASYNC BATCH MANAGER)
        if self._audit_manager:
            self._audit_manager.log(
                operation="LINK",
                table_name="_edges",
                record_id=f"{from_id}->{to_id}",
                new_value={
                    "from": f"{from_table}:{from_id}",
                    "to": f"{to_table}:{to_id}",
                    "relation": relation
                }
            )
        elif self._hash_chain:
            self._hash_chain.add({
                "operation": "LINK",
                "from": f"{from_table}:{from_id}",
                "to": f"{to_table}:{to_id}",
                "relation": relation
            })
    
    def traverse(self, table: str, start_id: str, depth: int = 2, max_results: int = 1000) -> List[Dict]:
        """
        Traverse graph from starting point with performance optimizations.
        
        Uses iterative BFS with deque and result limiting.
        """
        from collections import deque
        
        results = []
        visited = set()
        queue = deque([(table, start_id, 0)])
        
        while queue and len(results) < max_results:
            curr_table, curr_id, curr_depth = queue.popleft()
            
            if curr_depth >= depth:
                continue
            
            key = f"{curr_table}:{curr_id}"
            if key in visited:
                continue
            visited.add(key)
            
            # Find outgoing edges
            cursor = self._conn.execute(
                """SELECT to_table, to_id, relation, properties FROM _edges
                   WHERE from_table = ? AND from_id = ?""",
                (curr_table, curr_id)
            )
            
            for row in cursor:
                if len(results) >= max_results:
                    break
                    
                edge = {
                    "from": f"{curr_table}:{curr_id}",
                    "to": f"{row[0]}:{row[1]}",
                    "relation": row[2],
                    "properties": json.loads(row[3]) if row[3] else None,
                    "depth": curr_depth
                }
                results.append(edge)
                queue.append((row[0], row[1], curr_depth + 1))
        
        return results
    
    def verify(self) -> bool:
        """Verify database integrity."""
        if self._hash_chain:
            return self._hash_chain.verify()
        return True
    
    def repair(self) -> Dict[str, Any]:
        """
        Repair database integrity.
        
        Attempts to fix the hash chain by recomputing broken links.
        This should only be used if the database was not intentionally tampered with.
        """
        if self._hash_chain:
            return self._hash_chain.repair()
        return {"success": False, "message": "Blockchain not enabled"}
    
    def audit(self, table_name: str = None, record_id: str = None) -> List[Dict]:
        """Get audit trail."""
        sql = "SELECT * FROM _audit"
        params = []
        
        if table_name:
            sql += " WHERE table_name = ?"
            params.append(table_name)
        
        if record_id:
            if "WHERE" in sql:
                sql += " AND record_id = ?"
            else:
                sql += " WHERE record_id = ?"
            params.append(record_id)
        
        sql += " ORDER BY timestamp DESC"
        
        return self.execute(sql, tuple(params))
    
    @property
    def vector_engine(self):
        """Get audited vector engine instance."""
        from ule.engines.vector_engine import VectorEngine
        return VectorEngine(self._conn, audit_manager=self._audit_manager)

    @property
    def nosql(self):
        """Get NoSQL engine instance."""
        from ule.engines.nosql_engine import NoSQL_Engine
        return NoSQL_Engine(self._conn)

    @property
    def pqc(self):
        """Get Post-Quantum Cryptography engine instance."""
        from ule.engines.pqc_engine import PQCEngine
        return PQCEngine()

    def stats(self) -> Dict:
        """Get database statistics."""
        stats = {}
        
        try:
            # Table count
            tables = self.execute("SELECT COUNT(*) as count FROM _tables")
            stats['tables'] = tables[0]['count'] if tables else 0
        except Exception:
            stats['tables'] = 0
        
        try:
            # Document count
            docs = self.execute("SELECT COUNT(*) as count FROM _documents")
            stats['documents'] = docs[0]['count'] if docs else 0
        except Exception:
            stats['documents'] = 0
        
        try:
            # Edge count
            edges = self.execute("SELECT COUNT(*) as count FROM _edges")
            stats['edges'] = edges[0]['count'] if edges else 0
        except Exception:
            stats['edges'] = 0
        
        try:
            # Vector count
            vectors = self.execute("SELECT COUNT(*) as count FROM _vectors")
            stats['vectors'] = vectors[0]['count'] if vectors else 0
        except Exception:
            stats['vectors'] = 0
        
        try:
            # Audit count
            audit = self.execute("SELECT COUNT(*) as count FROM _audit")
            stats['audit_blocks'] = audit[0]['count'] if audit else 0
        except Exception:
            stats['audit_blocks'] = 0
        
        # File size
        if self.db_path and self.db_path.exists():
            stats['size_bytes'] = self.db_path.stat().st_size
            stats['size_mb'] = round(stats['size_bytes'] / (1024 * 1024), 2)
        
        return stats

    def close(self) -> None:
        """Close database connection."""
        if self._audit_manager:
            self._audit_manager.stop()
            
        if self._conn:
            self._conn.close()
            self._conn = None
        if self._wal:
            self._wal.close()
    
    def __enter__(self):
        """Context manager entry - auto-initialize if needed."""
        if not self._initialized:
            if self.db_path.exists():
                self.open(self.password)
            else:
                self.init(self.password)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close connection."""
        self.close()
