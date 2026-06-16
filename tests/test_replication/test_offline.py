"""Tests for Offline Mode module."""

import pytest
import sqlite3
import tempfile
import os
import time
from ule.core.database import ULEDatabase
from ule.replication.offline import OfflineManager, QueuedOperation, OperationType, SyncStatus


class TestOfflineManager:
    """Test Offline Manager functionality."""

    @pytest.fixture
    def db(self):
        """Create test database."""
        fd, db_path = tempfile.mkstemp(suffix='.udb')
        os.close(fd)
        
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
        conn.commit()
        
        class SimpleDB:
            def __init__(self, conn):
                self._conn = conn
            def get_connection(self):
                return self._conn
        
        yield SimpleDB(conn)
        
        conn.close()
        os.unlink(db_path)

    @pytest.fixture
    def offline(self, db):
        """Create offline manager."""
        return OfflineManager(db)

    def test_init(self, offline):
        """Test offline manager initialization."""
        assert offline is not None
        assert offline.is_online is True

    def test_go_offline(self, offline):
        """Test switching to offline mode."""
        offline.go_offline()
        assert offline.is_offline is True
        assert offline.is_online is False

    def test_go_online(self, offline):
        """Test switching to online mode."""
        offline.go_offline()
        offline.go_online()
        assert offline.is_online is True

    def test_queue_operation(self, offline):
        """Test queuing an operation."""
        offline.go_offline()
        
        op_id = offline.queue_operation(
            OperationType.INSERT,
            'users',
            'INSERT INTO users (name) VALUES (?)',
            ('Alice',)
        )
        
        assert op_id is not None
        pending = offline.get_pending_operations()
        assert len(pending) == 1

    def test_execute_offline(self, offline):
        """Test executing operation while offline."""
        offline.go_offline()
        
        op_id = offline.execute(
            'INSERT INTO users (name) VALUES (?)',
            ('Alice',),
            table='users'
        )
        
        assert op_id is not None
        pending = offline.get_pending_operations()
        assert len(pending) == 1

    def test_execute_online(self, offline):
        """Test executing operation while online."""
        result = offline.execute(
            'INSERT INTO users (name) VALUES (?)',
            ('Alice',)
        )
        
        # Should execute immediately and return rowid
        assert result is not None

    def test_sync_operations(self, offline):
        """Test syncing queued operations."""
        offline.go_offline()
        
        # Queue some operations
        offline.execute('INSERT INTO users (name) VALUES (?)', ('Alice',), table='users')
        offline.execute('INSERT INTO users (name) VALUES (?)', ('Bob',), table='users')
        
        # Go online and sync
        offline.go_online()
        stats = offline.sync()
        
        assert stats['synced'] == 2
        assert stats['failed'] == 0

    def test_get_queue_status(self, offline):
        """Test getting queue status."""
        offline.go_offline()
        
        offline.execute('INSERT INTO users (name) VALUES (?)', ('Alice',), table='users')
        
        status = offline.get_queue_status()
        
        assert status['total_queued'] == 1
        assert status['is_online'] is False

    def test_clear_queue(self, offline):
        """Test clearing queue."""
        offline.go_offline()
        
        offline.execute('INSERT INTO users (name) VALUES (?)', ('Alice',), table='users')
        offline.execute('INSERT INTO users (name) VALUES (?)', ('Bob',), table='users')
        
        offline.clear_queue()
        status = offline.get_queue_status()
        assert status['total_queued'] == 0

    def test_operation_to_dict(self):
        """Test operation serialization."""
        op = QueuedOperation(
            id='test-123',
            operation_type=OperationType.INSERT,
            sql='INSERT INTO users (name) VALUES (?)',
            params=('Alice',),
            table='users'
        )
        
        data = op.to_dict()
        assert data['id'] == 'test-123'
        assert data['operation_type'] == 'INSERT'
        assert data['table'] == 'users'

    def test_operation_from_dict(self):
        """Test operation deserialization."""
        data = {
            'id': 'test-123',
            'operation_type': 'INSERT',
            'sql': 'INSERT INTO users (name) VALUES (?)',
            'params': ['Alice'],
            'table': 'users',
            'timestamp': time.time(),
            'status': 'pending',
            'retry_count': 0,
            'max_retries': 3
        }
        
        op = QueuedOperation.from_dict(data)
        assert op.id == 'test-123'
        assert op.operation_type == OperationType.INSERT
        assert op.table == 'users'


class TestSyncStatus:
    """Test SyncStatus enum."""

    def test_status_values(self):
        """Test all status values."""
        assert SyncStatus.PENDING.value == 'pending'
        assert SyncStatus.SYNCING.value == 'syncing'
        assert SyncStatus.SYNCED.value == 'synced'
        assert SyncStatus.CONFLICT.value == 'conflict'
        assert SyncStatus.FAILED.value == 'failed'


class TestOperationType:
    """Test OperationType enum."""

    def test_operation_values(self):
        """Test all operation type values."""
        assert OperationType.INSERT.value == 'INSERT'
        assert OperationType.UPDATE.value == 'UPDATE'
        assert OperationType.DELETE.value == 'DELETE'
        assert OperationType.EXECUTE.value == 'EXECUTE'
        assert OperationType.EXECUTEMANY.value == 'EXECUTEMANY'
