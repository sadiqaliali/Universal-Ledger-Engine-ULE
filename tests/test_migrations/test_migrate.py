"""Tests for Migrations module."""

import pytest
import sqlite3
import tempfile
import os
import time
from ule.core.database import ULEDatabase
from ule.migrations.migrate import MigrationManager, Migration


class TestMigrationManager:
    """Test Migration Manager functionality."""

    @pytest.fixture
    def db(self):
        """Create test database."""
        fd, db_path = tempfile.mkstemp(suffix='.udb')
        os.close(fd)
        
        conn = sqlite3.connect(db_path)
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
    def migrations(self, db):
        """Create migration manager."""
        return MigrationManager(db)

    def test_init(self, migrations):
        """Test migration manager initialization."""
        assert migrations is not None

    def test_create_migration(self, migrations):
        """Test creating a migration."""
        migration = migrations.create_migration(
            version='001',
            description='Create users table',
            up_sql='CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)',
            down_sql='DROP TABLE users'
        )
        
        assert migration.version == '001'
        assert migration.description == 'Create users table'
        assert migration.up_sql is not None
        assert migration.down_sql is not None

    def test_apply_migration(self, migrations):
        """Test applying a migration."""
        migrations.create_migration(
            version='001',
            description='Create users table',
            up_sql='CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)',
            down_sql='DROP TABLE users'
        )
        
        result = migrations.migrate()
        
        assert result['applied'] == 1
        assert result['failed'] == 0

    def test_rollback_migration(self, migrations):
        """Test rolling back a migration."""
        # Create and apply migration
        migrations.create_migration(
            version='001',
            description='Create users table',
            up_sql='CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)',
            down_sql='DROP TABLE users'
        )
        
        migrations.migrate()
        
        # Rollback
        result = migrations.rollback(steps=1)
        
        assert result['rolled_back'] == 1
        assert result['failed'] == 0

    def test_get_pending_migrations(self, migrations):
        """Test getting pending migrations."""
        migrations.create_migration('001', 'First migration')
        migrations.create_migration('002', 'Second migration')
        
        pending = migrations.get_pending_migrations()
        assert len(pending) == 2

    def test_get_applied_migrations(self, migrations):
        """Test getting applied migrations."""
        migrations.create_migration(
            version='001',
            description='First migration',
            up_sql='SELECT 1'
        )
        
        migrations.migrate()
        
        applied = migrations.get_applied_migrations()
        assert len(applied) == 1
        assert applied[0].version == '001'

    def test_get_status(self, migrations):
        """Test getting migration status."""
        migrations.create_migration('001', 'First migration', up_sql='SELECT 1')
        migrations.create_migration('002', 'Second migration', up_sql='SELECT 1')
        
        migrations.migrate(target='001')
        
        status = migrations.get_status()
        assert len(status) == 2
        
        # First should be applied, second pending
        assert status[0]['status'] == 'applied'
        assert status[1]['status'] == 'pending'

    def test_current_version(self, migrations):
        """Test getting current schema version."""
        migrations.create_migration('001', 'First', up_sql='SELECT 1')
        migrations.create_migration('002', 'Second', up_sql='SELECT 1')
        
        assert migrations.current_version() is None
        
        migrations.migrate()
        
        assert migrations.current_version() == '002'

    def test_dry_run(self, migrations):
        """Test dry run migration."""
        migrations.create_migration('001', 'First', up_sql='SELECT 1')
        
        result = migrations.migrate(dry_run=True)
        
        assert result['applied'] == 0
        assert len(result['migrations']) == 1
        assert result['migrations'][0]['status'] == 'would_apply'

    def test_migration_dependencies(self, migrations):
        """Test migration with dependencies."""
        migrations.create_migration('001', 'First', up_sql='SELECT 1')
        migrations.create_migration(
            '002',
            'Second',
            up_sql='SELECT 1',
            dependencies=['001']
        )
        
        # Apply first migration
        migrations.migrate(target='001')
        
        # Now second should apply
        result = migrations.migrate(target='002')
        assert result['applied'] == 1

    def test_migration_with_function(self, migrations):
        """Test migration with Python function."""
        executed = []
        
        def up_fn(db):
            executed.append('up')
        
        def down_fn(db):
            executed.append('down')
        
        migrations.create_migration(
            '001',
            'Function migration',
            up_fn=up_fn,
            down_fn=down_fn
        )
        
        migrations.migrate()
        assert 'up' in executed
        
        migrations.rollback()
        assert 'down' in executed


class TestMigration:
    """Test Migration dataclass."""

    def test_migration_creation(self):
        """Test creating a migration."""
        migration = Migration(
            version='001',
            description='Test migration',
            up_sql='CREATE TABLE test (id INTEGER PRIMARY KEY)',
            down_sql='DROP TABLE test'
        )
        
        assert migration.version == '001'
        assert migration.applied is False

    def test_version_tuple(self):
        """Test version tuple conversion."""
        migration = Migration(version='1.2.3', description='Test')
        
        assert migration.version_tuple == (1, 2, 3)
