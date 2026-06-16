"""
ULE Change Data Capture (CDC) System

Tracks all data changes (INSERT, UPDATE, DELETE) in the database.
Enables real-time replication, audit logging, and event streaming.
"""

import json
import time
import threading
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum


class ChangeType(Enum):
    """Type of data change."""
    INSERT = 'INSERT'
    UPDATE = 'UPDATE'
    DELETE = 'DELETE'


@dataclass
class ChangeEvent:
    """Represents a single change event."""
    table: str
    change_type: ChangeType
    row_id: Optional[Any]
    old_data: Optional[Dict[str, Any]]
    new_data: Optional[Dict[str, Any]]
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'table': self.table,
            'change_type': self.change_type.value,
            'row_id': self.row_id,
            'old_data': self.old_data,
            'new_data': self.new_data,
            'timestamp': self.timestamp,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChangeEvent':
        return cls(
            table=data['table'],
            change_type=ChangeType(data['change_type']),
            row_id=data.get('row_id'),
            old_data=data.get('old_data'),
            new_data=data.get('new_data'),
            timestamp=data.get('timestamp', time.time()),
            metadata=data.get('metadata', {})
        )


class CDCManager:
    """
    Change Data Capture Manager.
    
    Tracks all data changes and provides streaming capabilities.
    
    Usage:
        cdc = CDCManager(db)
        cdc.enable_table('users')
        cdc.add_listener('users', handle_user_changes)
        
        # Changes are automatically captured
        db.execute("INSERT INTO users (name) VALUES (?)", ('Alice',))
        
        # Get changes
        changes = cdc.get_changes('users')
    """
    
    def __init__(self, db_connection=None):
        self.db = db_connection
        self._enabled_tables: set = set()
        self._listeners: Dict[str, List[Callable]] = {}
        self._changes: List[ChangeEvent] = []
        self._lock = threading.Lock()
        self._running = False
        self._change_log_size = 10000  # Max changes to keep in memory
        
        if self.db:
            self._create_cdc_tables()
    
    def _create_cdc_tables(self):
        """Create CDC tracking tables."""
        conn = self.db.get_connection()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS cdc_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT NOT NULL,
                change_type TEXT NOT NULL CHECK(change_type IN ('INSERT', 'UPDATE', 'DELETE')),
                row_id TEXT,
                old_data TEXT,
                new_data TEXT,
                timestamp REAL NOT NULL,
                metadata TEXT
            );
            
            CREATE INDEX IF NOT EXISTS idx_cdc_table ON cdc_log(table_name);
            CREATE INDEX IF NOT EXISTS idx_cdc_timestamp ON cdc_log(timestamp);
        """)
        conn.commit()
    
    def enable_table(self, table: str, track_old_values: bool = True) -> bool:
        """
        Enable CDC tracking for a table.
        
        Args:
            table: Table name to track
            track_old_values: Whether to store old values on UPDATE/DELETE
            
        Returns:
            True if enabled successfully
        """
        self._enabled_tables.add(table)
        
        if self.db:
            try:
                conn = self.db.get_connection()
                conn.execute(
                    "INSERT OR IGNORE INTO cdc_tables (table_name, track_old_values) VALUES (?, ?)",
                    (table, track_old_values)
                )
                conn.commit()
            except Exception:
                pass  # Table may not exist yet
        
        return True
    
    def disable_table(self, table: str) -> bool:
        """Disable CDC tracking for a table."""
        self._enabled_tables.discard(table)
        return True
    
    def add_listener(self, table: str, callback: Callable[[ChangeEvent], None]) -> bool:
        """
        Add a change listener for a table.
        
        Args:
            table: Table name to listen to (use '*' for all tables)
            callback: Function to call on changes
            
        Returns:
            True if listener added
        """
        if table not in self._listeners:
            self._listeners[table] = []
        self._listeners[table].append(callback)
        return True
    
    def remove_listener(self, table: str, callback: Callable) -> bool:
        """Remove a change listener."""
        if table in self._listeners:
            try:
                self._listeners[table].remove(callback)
                return True
            except ValueError:
                pass
        return False
    
    def capture_change(self, table: str, change_type: ChangeType,
                      row_id: Optional[Any] = None,
                      old_data: Optional[Dict[str, Any]] = None,
                      new_data: Optional[Dict[str, Any]] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> ChangeEvent:
        """
        Capture a data change event.
        
        Args:
            table: Table that changed
            change_type: Type of change
            row_id: Row identifier
            old_data: Previous data (for UPDATE/DELETE)
            new_data: New data (for INSERT/UPDATE)
            metadata: Additional metadata
            
        Returns:
            The captured change event
        """
        event = ChangeEvent(
            table=table,
            change_type=change_type,
            row_id=row_id,
            old_data=old_data,
            new_data=new_data,
            timestamp=time.time(),
            metadata=metadata or {}
        )
        
        with self._lock:
            self._changes.append(event)
            
            # Trim old changes if over limit
            if len(self._changes) > self._change_log_size:
                self._changes = self._changes[-self._change_log_size:]
        
        # Persist to database
        if self.db:
            self._persist_event(event)
        
        # Notify listeners
        self._notify_listeners(event)
        
        return event
    
    def get_changes(self, table: Optional[str] = None,
                   change_type: Optional[ChangeType] = None,
                   since: Optional[float] = None,
                   limit: int = 100) -> List[ChangeEvent]:
        """
        Get captured changes.
        
        Args:
            table: Filter by table name
            change_type: Filter by change type
            since: Filter by timestamp (get changes after this time)
            limit: Maximum number of changes to return
            
        Returns:
            List of change events
        """
        with self._lock:
            changes = list(self._changes)
        
        # Apply filters
        if table:
            changes = [c for c in changes if c.table == table]
        if change_type:
            changes = [c for c in changes if c.change_type == change_type]
        if since:
            changes = [c for c in changes if c.timestamp > since]
        
        return changes[-limit:]
    
    def get_changes_from_db(self, table: Optional[str] = None,
                           since: Optional[float] = None,
                           limit: int = 100) -> List[ChangeEvent]:
        """Get changes from the database log."""
        if not self.db:
            return []
        
        try:
            conn = self.db.get_connection()
            query = "SELECT * FROM cdc_log WHERE 1=1"
            params = []
            
            if table:
                query += " AND table_name = ?"
                params.append(table)
            if since:
                query += " AND timestamp > ?"
                params.append(since)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            changes = []
            for row in rows:
                changes.append(ChangeEvent(
                    table=row[1],
                    change_type=ChangeType(row[2]),
                    row_id=row[3],
                    old_data=json.loads(row[4]) if row[4] else None,
                    new_data=json.loads(row[5]) if row[5] else None,
                    timestamp=row[6],
                    metadata=json.loads(row[7]) if row[7] else {}
                ))
            
            return changes
        except Exception:
            return []
    
    def stream_changes(self, table: Optional[str] = None,
                      callback: Optional[Callable[[ChangeEvent], None]] = None,
                      interval: float = 0.1) -> None:
        """
        Stream changes continuously (blocking).
        
        Args:
            table: Filter by table name
            callback: Function to call for each change
            interval: Polling interval in seconds
        """
        self._running = True
        last_timestamp = time.time()
        
        while self._running:
            changes = self.get_changes(table, since=last_timestamp)
            for change in changes:
                last_timestamp = max(last_timestamp, change.timestamp)
                if callback:
                    callback(change)
            
            time.sleep(interval)
    
    def stop_streaming(self):
        """Stop the change stream."""
        self._running = False
    
    def clear_changes(self, table: Optional[str] = None):
        """Clear captured changes."""
        with self._lock:
            if table:
                self._changes = [c for c in self._changes if c.table != table]
            else:
                self._changes.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get CDC statistics."""
        with self._lock:
            total = len(self._changes)
            by_table = {}
            by_type = {}
            
            for change in self._changes:
                by_table[change.table] = by_table.get(change.table, 0) + 1
                by_type[change.change_type.value] = by_type.get(change.change_type.value, 0) + 1
            
            return {
                'total_changes': total,
                'enabled_tables': list(self._enabled_tables),
                'active_listeners': sum(len(v) for v in self._listeners.values()),
                'changes_by_table': by_table,
                'changes_by_type': by_type
            }
    
    def _persist_event(self, event: ChangeEvent):
        """Persist event to database."""
        try:
            conn = self.db.get_connection()
            conn.execute(
                "INSERT INTO cdc_log (table_name, change_type, row_id, old_data, new_data, timestamp, metadata) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    event.table,
                    event.change_type.value,
                    str(event.row_id) if event.row_id else None,
                    json.dumps(event.old_data) if event.old_data else None,
                    json.dumps(event.new_data) if event.new_data else None,
                    event.timestamp,
                    json.dumps(event.metadata) if event.metadata else None
                )
            )
            conn.commit()
        except Exception:
            pass
    
    def _notify_listeners(self, event: ChangeEvent):
        """Notify all registered listeners of a change."""
        # Notify table-specific listeners
        if event.table in self._listeners:
            for listener in self._listeners[event.table]:
                try:
                    listener(event)
                except Exception as e:
                    print(f"Error in CDC listener: {e}")
        
        # Notify wildcard listeners
        if '*' in self._listeners:
            for listener in self._listeners['*']:
                try:
                    listener(event)
                except Exception as e:
                    print(f"Error in CDC listener: {e}")
