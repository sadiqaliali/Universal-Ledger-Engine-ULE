"""
ULE Offline Mode - Disconnected Operation Support

Enables ULE to operate offline by queuing operations locally
and synchronizing when connection is restored.
"""

import json
import time
import uuid
import threading
from typing import Optional, Dict, Any, List, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum


class OperationType(Enum):
    """Type of database operation."""
    INSERT = 'INSERT'
    UPDATE = 'UPDATE'
    DELETE = 'DELETE'
    EXECUTE = 'EXECUTE'
    EXECUTEMANY = 'EXECUTEMANY'


class SyncStatus(Enum):
    """Synchronization status."""
    PENDING = 'pending'
    SYNCING = 'syncing'
    SYNCED = 'synced'
    CONFLICT = 'conflict'
    FAILED = 'failed'


@dataclass
class QueuedOperation:
    """Represents a queued offline operation."""
    id: str
    operation_type: OperationType
    sql: str
    params: Optional[tuple]
    table: str
    timestamp: float = field(default_factory=time.time)
    status: SyncStatus = SyncStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'operation_type': self.operation_type.value,
            'sql': self.sql,
            'params': self.params,
            'table': self.table,
            'timestamp': self.timestamp,
            'status': self.status.value,
            'result': self.result,
            'error': self.error,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QueuedOperation':
        return cls(
            id=data['id'],
            operation_type=OperationType(data['operation_type']),
            sql=data['sql'],
            params=tuple(data['params']) if data.get('params') else None,
            table=data['table'],
            timestamp=data.get('timestamp', time.time()),
            status=SyncStatus(data.get('status', 'pending')),
            result=data.get('result'),
            error=data.get('error'),
            retry_count=data.get('retry_count', 0),
            max_retries=data.get('max_retries', 3)
        )


class OfflineManager:
    """
    Offline Operation Manager.
    
    Queues database operations when offline and syncs when online.
    
    Usage:
        offline = OfflineManager(db)
        
        # Go offline
        offline.go_offline()
        
        # Operations are queued
        offline.queue_operation('INSERT', 'users', 
                               'INSERT INTO users (name) VALUES (?)', 
                               ('Alice',))
        
        # Go online and sync
        offline.go_online()
        offline.sync()
    """
    
    def __init__(self, db_connection=None):
        self.db = db_connection
        self._is_online = True
        self._queue: List[QueuedOperation] = []
        self._lock = threading.Lock()
        self._sync_in_progress = False
        self._conflict_handler: Optional[Callable] = None
        
        if self.db:
            self._create_offline_tables()
    
    def _create_offline_tables(self):
        """Create offline operation tracking tables."""
        conn = self.db.get_connection()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS offline_queue (
                id TEXT PRIMARY KEY,
                operation_type TEXT NOT NULL,
                sql TEXT NOT NULL,
                params TEXT,
                table_name TEXT NOT NULL,
                timestamp REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                result TEXT,
                error TEXT,
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3
            );
            
            CREATE TABLE IF NOT EXISTS offline_conflicts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation_id TEXT NOT NULL,
                conflict_type TEXT NOT NULL,
                local_data TEXT,
                remote_data TEXT,
                resolved BOOLEAN DEFAULT 0,
                resolution TEXT,
                timestamp REAL NOT NULL
            );
            
            CREATE INDEX IF NOT EXISTS idx_offline_status ON offline_queue(status);
            CREATE INDEX IF NOT EXISTS idx_offline_timestamp ON offline_queue(timestamp);
        """)
        conn.commit()
    
    def go_offline(self):
        """Switch to offline mode."""
        self._is_online = False
    
    def go_online(self):
        """Switch to online mode and trigger sync."""
        self._is_online = True
    
    @property
    def is_online(self) -> bool:
        return self._is_online
    
    @property
    def is_offline(self) -> bool:
        return not self._is_online
    
    def queue_operation(self, operation_type: OperationType, table: str,
                       sql: str, params: Optional[tuple] = None) -> str:
        """
        Queue an operation for later sync.
        
        Args:
            operation_type: Type of operation
            table: Target table
            sql: SQL statement
            params: SQL parameters
            
        Returns:
            Operation ID
        """
        op = QueuedOperation(
            id=str(uuid.uuid4()),
            operation_type=operation_type,
            sql=sql,
            params=params,
            table=table
        )
        
        with self._lock:
            self._queue.append(op)
        
        # Persist to database
        if self.db:
            self._persist_operation(op)
        
        return op.id
    
    def execute(self, sql: str, params: Optional[tuple] = None,
               table: str = 'unknown') -> Any:
        """
        Execute a SQL statement (queues if offline).
        
        Args:
            sql: SQL statement
            params: SQL parameters
            table: Table name (for queue tracking)
            
        Returns:
            Result if online, operation ID if offline
        """
        if self._is_online:
            if self.db:
                conn = self.db.get_connection()
                cursor = conn.execute(sql, params or ())
                conn.commit()
                return cursor.lastrowid
        else:
            op_id = self.queue_operation(
                OperationType.EXECUTE,
                table,
                sql,
                params
            )
            return op_id
    
    def execute_many(self, sql: str, params_list: List[tuple],
                    table: str = 'unknown') -> List[str]:
        """
        Execute multiple SQL statements (queues if offline).
        
        Args:
            sql: SQL statement
            params_list: List of parameter tuples
            table: Table name
            
        Returns:
            List of operation IDs if offline
        """
        if self._is_online:
            if self.db:
                conn = self.db.get_connection()
                conn.executemany(sql, params_list)
                conn.commit()
                return []
        else:
            op_ids = []
            for params in params_list:
                op_id = self.queue_operation(
                    OperationType.EXECUTEMANY,
                    table,
                    sql,
                    params
                )
                op_ids.append(op_id)
            return op_ids
    
    def sync(self, batch_size: int = 100) -> Dict[str, Any]:
        """
        Synchronize queued operations with the database.
        
        Args:
            batch_size: Number of operations to sync at once
            
        Returns:
            Sync statistics
        """
        if not self._is_online:
            return {'error': 'Cannot sync while offline'}
        
        if self._sync_in_progress:
            return {'error': 'Sync already in progress'}
        
        self._sync_in_progress = True
        
        stats = {
            'synced': 0,
            'failed': 0,
            'conflicts': 0,
            'remaining': 0
        }
        
        try:
            with self._lock:
                pending = [op for op in self._queue if op.status == SyncStatus.PENDING]
            
            # Process in batches
            for i in range(0, len(pending), batch_size):
                batch = pending[i:i + batch_size]
                
                for op in batch:
                    success = self._sync_operation(op)
                    
                    if success:
                        stats['synced'] += 1
                        op.status = SyncStatus.SYNCED
                    else:
                        if op.retry_count < op.max_retries:
                            op.retry_count += 1
                            stats['remaining'] += 1
                        else:
                            op.status = SyncStatus.FAILED
                            stats['failed'] += 1
            
            # Clean up synced operations
            with self._lock:
                self._queue = [op for op in self._queue 
                             if op.status not in (SyncStatus.SYNCED, SyncStatus.FAILED)]
                stats['remaining'] = len(self._queue)
            
            # Update database
            if self.db:
                self._update_queue_status()
        
        finally:
            self._sync_in_progress = False
        
        return stats
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status."""
        with self._lock:
            by_status = {}
            for op in self._queue:
                status = op.status.value
                by_status[status] = by_status.get(status, 0) + 1
            
            return {
                'total_queued': len(self._queue),
                'by_status': by_status,
                'is_online': self._is_online
            }
    
    def get_pending_operations(self) -> List[QueuedOperation]:
        """Get all pending operations."""
        with self._lock:
            return [op for op in self._queue if op.status == SyncStatus.PENDING]
    
    def clear_queue(self, status: Optional[SyncStatus] = None):
        """
        Clear queued operations.
        
        Args:
            status: Only clear operations with this status (None for all)
        """
        with self._lock:
            if status:
                self._queue = [op for op in self._queue if op.status != status]
            else:
                self._queue.clear()
    
    def set_conflict_handler(self, handler: Callable):
        """
        Set a custom conflict handler.
        
        Args:
            handler: Function(conflict_data) -> resolution
        """
        self._conflict_handler = handler
    
    def _sync_operation(self, op: QueuedOperation) -> bool:
        """Sync a single operation to the database."""
        if not self.db:
            return False
        
        try:
            op.status = SyncStatus.SYNCING
            conn = self.db.get_connection()
            cursor = conn.execute(op.sql, op.params or ())
            conn.commit()
            op.result = cursor.lastrowid
            return True
        except Exception as e:
            op.error = str(e)
            
            # Check for conflicts
            if 'UNIQUE constraint' in str(e) or 'PRIMARY KEY' in str(e):
                op.status = SyncStatus.CONFLICT
                self._handle_conflict(op)
            
            return False
    
    def _handle_conflict(self, op: QueuedOperation):
        """Handle a sync conflict."""
        conflict = {
            'operation_id': op.id,
            'conflict_type': 'constraint_violation',
            'local_data': op.to_dict(),
            'timestamp': time.time()
        }
        
        if self._conflict_handler:
            try:
                resolution = self._conflict_handler(conflict)
                conflict['resolved'] = True
                conflict['resolution'] = resolution
            except Exception:
                conflict['resolved'] = False
        else:
            # Default: keep local version
            conflict['resolved'] = False
        
        if self.db:
            try:
                conn = self.db.get_connection()
                conn.execute(
                    "INSERT INTO offline_conflicts (operation_id, conflict_type, local_data, timestamp) VALUES (?, ?, ?, ?)",
                    (op.id, conflict['conflict_type'], json.dumps(conflict['local_data']), time.time())
                )
                conn.commit()
            except Exception:
                pass
    
    def _persist_operation(self, op: QueuedOperation):
        """Persist operation to database."""
        try:
            conn = self.db.get_connection()
            conn.execute(
                "INSERT INTO offline_queue (id, operation_type, sql, params, table_name, timestamp, status, retry_count, max_retries) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    op.id,
                    op.operation_type.value,
                    op.sql,
                    json.dumps(op.params) if op.params else None,
                    op.table,
                    op.timestamp,
                    op.status.value,
                    op.retry_count,
                    op.max_retries
                )
            )
            conn.commit()
        except Exception:
            pass
    
    def _update_queue_status(self):
        """Update queue status in database."""
        if not self.db:
            return
        
        try:
            conn = self.db.get_connection()
            for op in self._queue:
                conn.execute(
                    "UPDATE offline_queue SET status = ?, result = ?, error = ?, retry_count = ? WHERE id = ?",
                    (op.status.value, 
                     json.dumps(op.result) if op.result else None,
                     op.error,
                     op.retry_count,
                     op.id)
                )
            conn.commit()
        except Exception:
            pass
