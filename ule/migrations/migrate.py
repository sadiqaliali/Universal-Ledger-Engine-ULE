"""
ULE Database Migrations System

Manages schema changes and data migrations with version control.
Supports forward/backward migrations and migration dependencies.
"""

import os
import json
import time
import importlib
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class Migration:
    """Represents a single migration."""
    version: str
    description: str
    created_at: float = field(default_factory=time.time)
    up_sql: Optional[str] = None
    down_sql: Optional[str] = None
    up_fn: Optional[Callable] = None
    down_fn: Optional[Callable] = None
    dependencies: List[str] = field(default_factory=list)
    applied: bool = False
    applied_at: Optional[float] = None
    
    @property
    def version_tuple(self):
        """Convert version string to tuple for comparison."""
        return tuple(int(x) for x in self.version.split('.'))


class MigrationManager:
    """
    Database Migration Manager.
    
    Manages schema and data migrations with version tracking.
    
    Usage:
        migrations = MigrationManager(db, migrations_dir='migrations')
        
        # Create a new migration
        migrations.create_migration(
            version='001',
            description='Create users table',
            up_sql='CREATE TABLE users (...)',
            down_sql='DROP TABLE users'
        )
        
        # Apply migrations
        migrations.migrate()  # Apply all pending
        migrations.migrate(target='002')  # Migrate to specific version
        migrations.rollback()  # Rollback last migration
    """
    
    def __init__(self, db_connection=None, migrations_dir: Optional[str] = None):
        self.db = db_connection
        self.migrations_dir = migrations_dir or 'migrations'
        self._migrations: Dict[str, Migration] = {}
        
        if self.db:
            self._create_migration_table()
            self._load_applied_migrations()
    
    def _create_migration_table(self):
        """Create migration tracking table."""
        conn = self.db.get_connection()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                description TEXT,
                applied_at REAL NOT NULL,
                execution_time REAL,
                checksum TEXT
            )
        """)
        conn.commit()
    
    def _load_applied_migrations(self):
        """Load applied migrations from database."""
        try:
            conn = self.db.get_connection()
            cursor = conn.execute("SELECT version, description, applied_at FROM schema_migrations ORDER BY version")
            for row in cursor.fetchall():
                if row[0] in self._migrations:
                    self._migrations[row[0]].applied = True
                    self._migrations[row[0]].applied_at = row[2]
        except Exception:
            pass
    
    def create_migration(self, version: str, description: str,
                        up_sql: Optional[str] = None,
                        down_sql: Optional[str] = None,
                        up_fn: Optional[Callable] = None,
                        down_fn: Optional[Callable] = None,
                        dependencies: Optional[List[str]] = None) -> Migration:
        """
        Create a new migration.
        
        Args:
            version: Migration version (e.g., '001', '1.0.0')
            description: Migration description
            up_sql: SQL to apply migration
            down_sql: SQL to rollback migration
            up_fn: Python function for complex up migrations
            down_fn: Python function for complex down migrations
            dependencies: List of dependency versions
            
        Returns:
            Created migration
        """
        migration = Migration(
            version=version,
            description=description,
            up_sql=up_sql,
            down_sql=down_sql,
            up_fn=up_fn,
            down_fn=down_fn,
            dependencies=dependencies or []
        )
        
        self._migrations[version] = migration
        
        # Save to file if migrations_dir is set
        if self.migrations_dir:
            self._save_migration_file(migration)
        
        return migration
    
    def load_migrations_from_dir(self) -> List[Migration]:
        """Load all migrations from the migrations directory."""
        migrations_path = Path(self.migrations_dir)
        if not migrations_path.exists():
            return []
        
        migrations = []
        for file_path in sorted(migrations_path.glob('*.json')):
            try:
                with open(file_path) as f:
                    data = json.load(f)
                    migration = Migration(
                        version=data['version'],
                        description=data['description'],
                        up_sql=data.get('up_sql'),
                        down_sql=data.get('down_sql'),
                        dependencies=data.get('dependencies', []),
                        created_at=data.get('created_at', time.time())
                    )
                    self._migrations[migration.version] = migration
                    migrations.append(migration)
            except Exception as e:
                print(f"Error loading migration {file_path}: {e}")
        
        return migrations
    
    def migrate(self, target: Optional[str] = None, dry_run: bool = False) -> Dict[str, Any]:
        """
        Apply pending migrations.
        
        Args:
            target: Target version (None for all pending)
            dry_run: Don't actually apply, just show what would be done
            
        Returns:
            Migration statistics
        """
        pending = self.get_pending_migrations()
        
        if target:
            pending = [m for m in pending if m.version_tuple <= tuple(int(x) for x in target.split('.'))]
        
        stats = {
            'applied': 0,
            'skipped': 0,
            'failed': 0,
            'migrations': []
        }
        
        for migration in pending:
            # Check dependencies
            if not self._check_dependencies(migration):
                stats['skipped'] += 1
                continue
            
            if dry_run:
                stats['migrations'].append({
                    'version': migration.version,
                    'description': migration.description,
                    'status': 'would_apply'
                })
                continue
            
            start_time = time.time()
            try:
                self._apply_migration(migration)
                execution_time = time.time() - start_time
                
                stats['applied'] += 1
                stats['migrations'].append({
                    'version': migration.version,
                    'description': migration.description,
                    'status': 'applied',
                    'execution_time': execution_time
                })
            except Exception as e:
                stats['failed'] += 1
                stats['migrations'].append({
                    'version': migration.version,
                    'description': migration.description,
                    'status': f'failed: {str(e)}'
                })
                break
        
        return stats
    
    def rollback(self, steps: int = 1) -> Dict[str, Any]:
        """
        Rollback applied migrations.
        
        Args:
            steps: Number of migrations to rollback
            
        Returns:
            Rollback statistics
        """
        applied = self.get_applied_migrations()
        to_rollback = applied[-steps:] if len(applied) >= steps else applied
        to_rollback.reverse()
        
        stats = {
            'rolled_back': 0,
            'failed': 0,
            'migrations': []
        }
        
        for migration in to_rollback:
            try:
                self._rollback_migration(migration)
                stats['rolled_back'] += 1
                stats['migrations'].append({
                    'version': migration.version,
                    'description': migration.description,
                    'status': 'rolled_back'
                })
            except Exception as e:
                stats['failed'] += 1
                stats['migrations'].append({
                    'version': migration.version,
                    'description': migration.description,
                    'status': f'failed: {str(e)}'
                })
                break
        
        return stats
    
    def get_pending_migrations(self) -> List[Migration]:
        """Get all pending (not yet applied) migrations."""
        return [m for m in self._migrations.values() if not m.applied]
    
    def get_applied_migrations(self) -> List[Migration]:
        """Get all applied migrations."""
        return [m for m in self._migrations.values() if m.applied]
    
    def get_status(self) -> List[Dict[str, Any]]:
        """Get migration status for all migrations."""
        status = []
        for version, migration in sorted(self._migrations.items(), 
                                        key=lambda x: tuple(int(v) for v in x[0].split('.'))):
            status.append({
                'version': migration.version,
                'description': migration.description,
                'status': 'applied' if migration.applied else 'pending',
                'applied_at': migration.applied_at,
                'dependencies': migration.dependencies
            })
        return status
    
    def current_version(self) -> Optional[str]:
        """Get current schema version."""
        applied = self.get_applied_migrations()
        if applied:
            return applied[-1].version
        return None
    
    def _apply_migration(self, migration: Migration):
        """Apply a single migration."""
        start_time = time.time()
        
        # Execute up SQL
        if migration.up_sql:
            conn = self.db.get_connection()
            conn.executescript(migration.up_sql)
            conn.commit()
        
        # Execute up function
        if migration.up_fn:
            migration.up_fn(self.db)
        
        # Mark as applied
        execution_time = time.time() - start_time
        migration.applied = True
        migration.applied_at = time.time()
        
        # Update tracking table
        conn = self.db.get_connection()
        conn.execute(
            "INSERT OR REPLACE INTO schema_migrations (version, description, applied_at, execution_time) VALUES (?, ?, ?, ?)",
            (migration.version, migration.description, migration.applied_at, execution_time)
        )
        conn.commit()
    
    def _rollback_migration(self, migration: Migration):
        """Rollback a single migration."""
        # Execute down SQL
        if migration.down_sql:
            conn = self.db.get_connection()
            conn.executescript(migration.down_sql)
            conn.commit()
        
        # Execute down function
        if migration.down_fn:
            migration.down_fn(self.db)
        
        # Mark as not applied
        migration.applied = False
        migration.applied_at = None
        
        # Update tracking table
        conn = self.db.get_connection()
        conn.execute("DELETE FROM schema_migrations WHERE version = ?", (migration.version,))
        conn.commit()
    
    def _check_dependencies(self, migration: Migration) -> bool:
        """Check if all dependencies are satisfied."""
        for dep_version in migration.dependencies:
            if dep_version not in self._migrations:
                return False
            if not self._migrations[dep_version].applied:
                return False
        return True
    
    def _save_migration_file(self, migration: Migration):
        """Save migration to file."""
        os.makedirs(self.migrations_dir, exist_ok=True)
        
        file_path = Path(self.migrations_dir) / f"{migration.version}_{migration.description.lower().replace(' ', '_')}.json"
        
        data = {
            'version': migration.version,
            'description': migration.description,
            'up_sql': migration.up_sql,
            'down_sql': migration.down_sql,
            'dependencies': migration.dependencies,
            'created_at': migration.created_at
        }
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def generate_migration(self, from_version: Optional[str] = None,
                          to_version: Optional[str] = None) -> Optional[str]:
        """
        Generate migration SQL by comparing two schema versions.
        
        This is a simple implementation. In production, you'd want
        to use a proper schema comparison tool.
        """
        # Placeholder for automatic migration generation
        return None
