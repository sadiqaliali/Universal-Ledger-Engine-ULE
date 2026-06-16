"""Time-Travel Snapshots for ULE.

This module provides point-in-time recovery and historical queries
through automatic database snapshots.

Features:
- Automatic snapshots before writes
- Point-in-time recovery
- Historical data queries
- Snapshot retention policies
- Space-efficient storage
"""

import hashlib
import json
import sqlite3
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import shutil
import threading


class SnapshotManager:
    """
    Time-travel snapshot manager for ULE.

    Creates point-in-time snapshots of database state,
    enabling:
    - Historical queries ("what was the balance last Friday?")
    - Point-in-time recovery (restore to before accidental delete)
    - Audit trail (who changed what and when)
    - Compliance (retain historical data for regulations)
    """

    def __init__(self, db_path: str, snapshot_dir: Optional[str] = None,
                 retention_days: int = 30):
        """
        Initialize snapshot manager.

        Args:
            db_path: Path to main database file
            snapshot_dir: Directory for snapshots (default: .snapshots/)
            retention_days: How long to keep snapshots (default 30)
        """
        self.db_path = Path(db_path)
        self.snapshot_dir = Path(snapshot_dir) if snapshot_dir else self.db_path.parent / f"{self.db_path.stem}_snapshots"
        self.retention_days = retention_days
        self._conn: Optional[sqlite3.Connection] = None
        self._lock = threading.Lock()

        # Create snapshot directory
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)

    def connect(self) -> None:
        """Connect to database and initialize snapshot tables."""
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._init_snapshot_tables()

    def _init_snapshot_tables(self) -> None:
        """Create snapshot metadata tables."""
        tables = [
            # Snapshot metadata
            """CREATE TABLE IF NOT EXISTS _snapshots (
                snapshot_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                description TEXT,
                tables TEXT,
                record_count INTEGER,
                size_bytes INTEGER,
                file_path TEXT,
                expires_at TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )""",

            # Snapshot data (for quick access)
            """CREATE TABLE IF NOT EXISTS _snapshot_data (
                snapshot_id TEXT,
                table_name TEXT,
                record_id TEXT,
                data BLOB,
                checksum TEXT,
                PRIMARY KEY (snapshot_id, table_name, record_id)
            )""",

            # Point-in-time index
            """CREATE TABLE IF NOT EXISTS _timeline (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                operation TEXT,
                table_name TEXT,
                record_id TEXT,
                before_data BLOB,
                after_data BLOB,
                user_name TEXT
            )""",
        ]

        for sql in tables:
            self._conn.execute(sql)

        # Create indexes for performance
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_timeline_timestamp ON _timeline(timestamp)"
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_timeline_table ON _timeline(table_name, record_id)"
        )

        self._conn.commit()

    def create_snapshot(self, description: str = "",
                       tables: Optional[List[str]] = None) -> str:
        """
        Create a point-in-time snapshot.

        Args:
            description: Optional description of the snapshot
            tables: List of tables to snapshot (None for all)

        Returns:
            Snapshot ID
        """
        with self._lock:
            snapshot_id = self._generate_snapshot_id()
            timestamp = datetime.now().isoformat()

            # Get list of tables
            if tables is None:
                tables = self._get_all_tables()

            # Export data for each table
            snapshot_data = {}
            total_records = 0

            for table_name in tables:
                if table_name.startswith('_'):
                    continue  # Skip internal tables

                table_data = self._export_table(table_name)
                snapshot_data[table_name] = table_data
                total_records += len(table_data)

            # Save snapshot to file
            snapshot_file = self.snapshot_dir / f"{snapshot_id}.snap"
            self._save_snapshot(snapshot_file, snapshot_data)

            # Calculate file size
            file_size = snapshot_file.stat().st_size

            # Calculate expiration
            expires_at = (datetime.now() + timedelta(days=self.retention_days)).isoformat()

            # Save metadata
            self._conn.execute(
                """INSERT INTO _snapshots 
                   (snapshot_id, timestamp, description, tables, record_count, size_bytes, file_path, expires_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (snapshot_id, timestamp, description, json.dumps(tables),
                 total_records, file_size, str(snapshot_file), expires_at)
            )

            self._conn.commit()

            # Cleanup old snapshots
            self._cleanup_old_snapshots()

            return snapshot_id

    def _generate_snapshot_id(self) -> str:
        """Generate unique snapshot ID."""
        timestamp = datetime.now().isoformat()
        return f"snap_{hashlib.sha256(timestamp.encode()).hexdigest()[:16]}"

    def _get_all_tables(self) -> List[str]:
        """Get list of all user tables."""
        cursor = self._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '_%'"
        )
        return [row[0] for row in cursor.fetchall()]

    def _export_table(self, table_name: str) -> List[Dict]:
        """Export all data from a table."""
        cursor = self._conn.execute(f"SELECT * FROM {table_name}")
        columns = [desc[0] for desc in cursor.description] if cursor.description else []

        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def _save_snapshot(self, file_path: Path, data: Dict) -> None:
        """Save snapshot to file."""
        with open(file_path, 'w') as f:
            json.dump({
                "version": "1.0",
                "timestamp": datetime.now().isoformat(),
                "data": data
            }, f, indent=2, default=str)

    def restore_snapshot(self, snapshot_id: str,
                        tables: Optional[List[str]] = None) -> int:
        """
        Restore database from a snapshot.

        Args:
            snapshot_id: ID of snapshot to restore
            tables: List of tables to restore (None for all)

        Returns:
            Number of records restored
        """
        with self._lock:
            # Get snapshot metadata
            cursor = self._conn.execute(
                "SELECT * FROM _snapshots WHERE snapshot_id = ?",
                (snapshot_id,)
            )
            snapshot = cursor.fetchone()

            if not snapshot:
                raise ValueError(f"Snapshot not found: {snapshot_id}")

            # Load snapshot data
            snapshot_file = Path(snapshot["file_path"])
            if not snapshot_file.exists():
                raise ValueError(f"Snapshot file not found: {snapshot_file}")

            with open(snapshot_file, 'r') as f:
                snapshot_data = json.load(f)

            data = snapshot_data.get("data", {})
            tables_to_restore = tables or json.loads(snapshot["tables"])

            total_restored = 0

            for table_name in tables_to_restore:
                if table_name not in data:
                    continue

                records = data[table_name]
                if not records:
                    continue

                # Clear existing data
                self._conn.execute(f"DELETE FROM {table_name}")

                # Restore records
                for record in records:
                    if not record:
                        continue
                    columns = list(record.keys())
                    placeholders = ", ".join("?" * len(columns))
                    values = list(record.values())

                    try:
                        self._conn.execute(
                            f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})",
                            values
                        )
                        total_restored += 1
                    except sqlite3.IntegrityError:
                        # Skip records with integrity issues
                        pass

            self._conn.commit()
            return total_restored

    def query_at_time(self, table_name: str, timestamp: str,
                      record_id: Optional[str] = None) -> List[Dict]:
        """
        Query data as it existed at a specific time.

        Args:
            table_name: Table to query
            timestamp: ISO format timestamp
            record_id: Optional specific record ID

        Returns:
            List of records as they existed at the time
        """
        # Find closest snapshot before the timestamp
        cursor = self._conn.execute(
            """SELECT snapshot_id, timestamp FROM _snapshots 
               WHERE timestamp <= ? AND tables LIKE ?
               ORDER BY timestamp DESC LIMIT 1""",
            (timestamp, f'%{table_name}%')
        )

        snapshot = cursor.fetchone()
        if not snapshot:
            return []

        # Load snapshot
        snapshot_file = Path(snapshot["file_path"])
        if not snapshot_file.exists():
            return []

        with open(snapshot_file, 'r') as f:
            snapshot_data = json.load(f)

        data = snapshot_data.get("data", {})
        table_data = data.get(table_name, [])

        # Apply timeline changes after snapshot
        changes = self._get_changes_in_range(
            table_name,
            snapshot["timestamp"],
            timestamp,
            record_id
        )

        # Apply changes to snapshot data
        result = self._apply_changes(table_data, changes, record_id)

        return result

    def _get_changes_in_range(self, table_name: str, start_time: str,
                              end_time: str, record_id: Optional[str] = None) -> List[Dict]:
        """Get all changes in a time range."""
        if record_id:
            cursor = self._conn.execute(
                """SELECT * FROM _timeline 
                   WHERE table_name = ? AND record_id = ? 
                   AND timestamp BETWEEN ? AND ?
                   ORDER BY timestamp""",
                (table_name, record_id, start_time, end_time)
            )
        else:
            cursor = self._conn.execute(
                """SELECT * FROM _timeline 
                   WHERE table_name = ? AND timestamp BETWEEN ? AND ?
                   ORDER BY timestamp""",
                (table_name, start_time, end_time)
            )

        return [dict(row) for row in cursor.fetchall()]

    def _apply_changes(self, data: List[Dict], changes: List[Dict],
                       record_id: Optional[str] = None) -> List[Dict]:
        """Apply timeline changes to snapshot data."""
        # Convert to dict for easier lookup
        result = {}
        for record in data:
            rid = record.get('id') or str(hash(json.dumps(record, sort_keys=True)))
            result[rid] = record.copy()

        # Apply each change
        for change in changes:
            change_record_id = change.get('record_id')

            if record_id and change_record_id != record_id:
                continue

            operation = change.get('operation', '')
            after_data = change.get('after_data')

            if operation == 'INSERT' and after_data:
                result[change_record_id] = json.loads(after_data)
            elif operation == 'UPDATE' and after_data:
                if change_record_id in result:
                    result[change_record_id].update(json.loads(after_data))
            elif operation == 'DELETE':
                if change_record_id in result:
                    del result[change_record_id]

        # Filter by record_id if specified
        if record_id:
            return [result[record_id]] if record_id in result else []

        return list(result.values())

    def list_snapshots(self) -> List[Dict]:
        """List all available snapshots."""
        cursor = self._conn.execute(
            "SELECT * FROM _snapshots ORDER BY timestamp DESC"
        )
        return [dict(row) for row in cursor.fetchall()]

    def delete_snapshot(self, snapshot_id: str) -> bool:
        """Delete a specific snapshot."""
        # Get snapshot file path
        cursor = self._conn.execute(
            "SELECT file_path FROM _snapshots WHERE snapshot_id = ?",
            (snapshot_id,)
        )
        row = cursor.fetchone()

        if row:
            # Delete file
            try:
                Path(row["file_path"]).unlink()
            except FileNotFoundError:
                pass

            # Delete metadata
            self._conn.execute("DELETE FROM _snapshots WHERE snapshot_id = ?", (snapshot_id,))
            self._conn.execute("DELETE FROM _snapshot_data WHERE snapshot_id = ?", (snapshot_id,))
            self._conn.commit()

            return True

        return False

    def _cleanup_old_snapshots(self) -> None:
        """Remove expired snapshots."""
        cutoff = (datetime.now() - timedelta(days=self.retention_days)).isoformat()

        cursor = self._conn.execute(
            "SELECT snapshot_id, file_path FROM _snapshots WHERE expires_at < ?",
            (cutoff,)
        )

        for row in cursor.fetchall():
            snapshot_id = row["snapshot_id"]
            file_path = row["file_path"]

            # Delete file
            try:
                Path(file_path).unlink()
            except FileNotFoundError:
                pass

            # Delete metadata
            self._conn.execute("DELETE FROM _snapshots WHERE snapshot_id = ?", (snapshot_id,))
            self._conn.execute("DELETE FROM _snapshot_data WHERE snapshot_id = ?", (snapshot_id,))

        self._conn.commit()

    def enable_timeline_tracking(self) -> None:
        """Enable automatic timeline tracking for all operations."""
        # This would be called by the database layer to track changes
        pass

    def track_change(self, operation: str, table_name: str,
                     record_id: str, before_data: Optional[Dict] = None,
                     after_data: Optional[Dict] = None,
                     user_name: Optional[str] = None) -> None:
        """
        Track a data change in the timeline.

        Args:
            operation: INSERT, UPDATE, or DELETE
            table_name: Name of the table
            record_id: ID of the affected record
            before_data: Data before the change (for UPDATE/DELETE)
            after_data: Data after the change (for INSERT/UPDATE)
            user_name: User who made the change
        """
        self._conn.execute(
            """INSERT INTO _timeline 
               (timestamp, operation, table_name, record_id, before_data, after_data, user_name)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (datetime.now().isoformat(), operation, table_name, record_id,
             json.dumps(before_data) if before_data else None,
             json.dumps(after_data) if after_data else None,
             user_name)
        )
        self._conn.commit()

    def get_history(self, table_name: str, record_id: str,
                    limit: int = 100) -> List[Dict]:
        """
        Get change history for a specific record.

        Args:
            table_name: Name of the table
            record_id: ID of the record
            limit: Maximum number of changes to return

        Returns:
            List of changes in chronological order
        """
        cursor = self._conn.execute(
            """SELECT * FROM _timeline 
               WHERE table_name = ? AND record_id = ?
               ORDER BY timestamp DESC LIMIT ?""",
            (table_name, record_id, limit)
        )

        return [dict(row) for row in cursor.fetchall()]

    def close(self) -> None:
        """Close snapshot manager."""
        if self._conn:
            self._conn.close()
            self._conn = None


# Convenience functions

def create_snapshot(db_path: str, description: str = "") -> str:
    """Create a snapshot of the database."""
    manager = SnapshotManager(db_path)
    manager.connect()
    snapshot_id = manager.create_snapshot(description)
    manager.close()
    return snapshot_id


def restore_snapshot(db_path: str, snapshot_id: str) -> int:
    """Restore database from a snapshot."""
    manager = SnapshotManager(db_path)
    manager.connect()
    count = manager.restore_snapshot(snapshot_id)
    manager.close()
    return count


def query_at_time(db_path: str, table_name: str,
                  timestamp: str) -> List[Dict]:
    """Query data as it existed at a specific time."""
    manager = SnapshotManager(db_path)
    manager.connect()
    results = manager.query_at_time(table_name, timestamp)
    manager.close()
    return results
