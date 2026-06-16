"""Tests for CDC (Change Data Capture) module."""

import pytest
import sqlite3
import tempfile
import os
import time
from ule.core.database import ULEDatabase
from ule.replication.cdc import CDCManager, ChangeEvent, ChangeType


class TestCDCManager:
    """Test CDC Manager functionality."""

    @pytest.fixture
    def db(self):
        """Create test database."""
        fd, db_path = tempfile.mkstemp(suffix='.udb')
        os.close(fd)
        
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT)")
        conn.execute("INSERT INTO users (name, email) VALUES ('Alice', 'alice@test.com')")
        conn.execute("INSERT INTO users (name, email) VALUES ('Bob', 'bob@test.com')")
        conn.commit()
        
        # Wrap in simple object with get_connection
        class SimpleDB:
            def __init__(self, conn):
                self._conn = conn
            def get_connection(self):
                return self._conn
        
        yield SimpleDB(conn)
        
        conn.close()
        os.unlink(db_path)

    @pytest.fixture
    def cdc(self, db):
        """Create CDC manager."""
        return CDCManager(db)

    def test_init(self, cdc):
        """Test CDC manager initialization."""
        assert cdc is not None
        assert len(cdc._enabled_tables) == 0

    def test_enable_table(self, cdc):
        """Test enabling CDC for a table."""
        result = cdc.enable_table('users')
        assert result is True
        assert 'users' in cdc._enabled_tables

    def test_disable_table(self, cdc):
        """Test disabling CDC for a table."""
        cdc.enable_table('users')
        result = cdc.disable_table('users')
        assert result is True
        assert 'users' not in cdc._enabled_tables

    def test_capture_insert(self, cdc):
        """Test capturing INSERT operation."""
        cdc.enable_table('users')
        
        event = cdc.capture_change(
            table='users',
            change_type=ChangeType.INSERT,
            row_id=1,
            new_data={'id': 1, 'name': 'Alice', 'email': 'alice@test.com'}
        )
        
        assert event.table == 'users'
        assert event.change_type == ChangeType.INSERT
        assert event.row_id == 1
        assert event.new_data['name'] == 'Alice'

    def test_capture_update(self, cdc):
        """Test capturing UPDATE operation."""
        cdc.enable_table('users')
        
        event = cdc.capture_change(
            table='users',
            change_type=ChangeType.UPDATE,
            row_id=1,
            old_data={'name': 'Alice'},
            new_data={'name': 'Alice Updated'}
        )
        
        assert event.change_type == ChangeType.UPDATE
        assert event.old_data['name'] == 'Alice'
        assert event.new_data['name'] == 'Alice Updated'

    def test_capture_delete(self, cdc):
        """Test capturing DELETE operation."""
        cdc.enable_table('users')
        
        event = cdc.capture_change(
            table='users',
            change_type=ChangeType.DELETE,
            row_id=1,
            old_data={'name': 'Alice'}
        )
        
        assert event.change_type == ChangeType.DELETE
        assert event.old_data['name'] == 'Alice'

    def test_get_changes(self, cdc):
        """Test retrieving changes."""
        cdc.enable_table('users')
        
        # Add some changes
        cdc.capture_change('users', ChangeType.INSERT, row_id=1, new_data={'name': 'Alice'})
        cdc.capture_change('users', ChangeType.UPDATE, row_id=1, old_data={'name': 'Alice'}, new_data={'name': 'Alice2'})
        cdc.capture_change('users', ChangeType.DELETE, row_id=1, old_data={'name': 'Alice2'})
        
        changes = cdc.get_changes('users')
        assert len(changes) == 3

    def test_get_changes_filtered(self, cdc):
        """Test retrieving filtered changes."""
        cdc.enable_table('users')
        cdc.enable_table('products')
        
        cdc.capture_change('users', ChangeType.INSERT, row_id=1)
        cdc.capture_change('products', ChangeType.INSERT, row_id=1)
        
        changes = cdc.get_changes('users')
        assert len(changes) == 1
        assert changes[0].table == 'users'

    def test_get_changes_by_type(self, cdc):
        """Test retrieving changes by type."""
        cdc.enable_table('users')
        
        cdc.capture_change('users', ChangeType.INSERT, row_id=1)
        cdc.capture_change('users', ChangeType.UPDATE, row_id=1)
        cdc.capture_change('users', ChangeType.DELETE, row_id=1)
        
        changes = cdc.get_changes('users', change_type=ChangeType.INSERT)
        assert len(changes) == 1

    def test_add_listener(self, cdc):
        """Test adding change listener."""
        cdc.enable_table('users')
        
        changes_received = []
        
        def listener(event):
            changes_received.append(event)
        
        cdc.add_listener('users', listener)
        cdc.capture_change('users', ChangeType.INSERT, row_id=1)
        
        assert len(changes_received) == 1

    def test_remove_listener(self, cdc):
        """Test removing change listener."""
        cdc.enable_table('users')
        
        changes_received = []
        
        def listener(event):
            changes_received.append(event)
        
        cdc.add_listener('users', listener)
        cdc.remove_listener('users', listener)
        cdc.capture_change('users', ChangeType.INSERT, row_id=1)
        
        assert len(changes_received) == 0

    def test_get_stats(self, cdc):
        """Test getting CDC statistics."""
        cdc.enable_table('users')
        
        cdc.capture_change('users', ChangeType.INSERT, row_id=1)
        cdc.capture_change('users', ChangeType.UPDATE, row_id=1)
        
        stats = cdc.get_stats()
        
        assert 'total_changes' in stats
        assert stats['total_changes'] == 2
        assert 'users' in stats['changes_by_table']

    def test_clear_changes(self, cdc):
        """Test clearing changes."""
        cdc.enable_table('users')
        
        cdc.capture_change('users', ChangeType.INSERT, row_id=1)
        cdc.capture_change('users', ChangeType.UPDATE, row_id=1)
        
        cdc.clear_changes()
        changes = cdc.get_changes()
        assert len(changes) == 0

    def test_event_to_dict(self):
        """Test event serialization."""
        event = ChangeEvent(
            table='users',
            change_type=ChangeType.INSERT,
            row_id=1,
            old_data=None,
            new_data={'name': 'Alice'}
        )
        
        data = event.to_dict()
        assert data['table'] == 'users'
        assert data['change_type'] == 'INSERT'
        assert data['row_id'] == 1

    def test_event_from_dict(self):
        """Test event deserialization."""
        data = {
            'table': 'users',
            'change_type': 'INSERT',
            'row_id': 1,
            'old_data': None,
            'new_data': {'name': 'Alice'},
            'timestamp': time.time(),
            'metadata': {}
        }
        
        event = ChangeEvent.from_dict(data)
        assert event.table == 'users'
        assert event.change_type == ChangeType.INSERT
