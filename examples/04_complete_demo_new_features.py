"""
ULE Comprehensive Demo - All New Features

This script demonstrates all the new features added to ULE:
- MQTT Client
- Change Data Capture (CDC)
- Offline Mode
- Database Migrations
- Transformer NLQ
- Tutorial System

Run: python examples/04_complete_demo_new_features.py
"""

import os
import sys
import tempfile
import time
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ule.core.database import ULEDatabase
from ule.iot import MQTTClient, QoS
from ule.replication import CDCManager, ChangeType, OfflineManager
from ule.migrations import MigrationManager
from ule.ai import TransformerNLQ
from ule.tutorials import TutorialManager


def print_section(title):
    """Print section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_subsection(title):
    """Print subsection header."""
    print(f"\n--- {title} ---")


def demo_migrations(db):
    """Demonstrate database migrations."""
    print_section("1. DATABASE MIGRATIONS")
    
    migrations = MigrationManager(db)
    
    print_subsection("Creating migrations")
    
    # Migration 1: Create users table
    migrations.create_migration(
        version='001',
        description='Create users table',
        up_sql='''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                age INTEGER
            )
        ''',
        down_sql='DROP TABLE users'
    )
    print("✓ Created migration 001: Create users table")
    
    # Migration 2: Create products table
    migrations.create_migration(
        version='002',
        description='Create products table',
        up_sql='''
            CREATE TABLE products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                price REAL,
                category TEXT
            )
        ''',
        down_sql='DROP TABLE products',
        dependencies=['001']
    )
    print("✓ Created migration 002: Create products table")
    
    # Migration 3: Create orders table
    migrations.create_migration(
        version='003',
        description='Create orders table',
        up_sql='''
            CREATE TABLE orders (
                id INTEGER PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                product_id INTEGER REFERENCES products(id),
                quantity INTEGER,
                total REAL
            )
        ''',
        down_sql='DROP TABLE orders',
        dependencies=['001', '002']
    )
    print("✓ Created migration 003: Create orders table")
    
    print_subsection("Checking migration status")
    status = migrations.get_status()
    for s in status:
        status_icon = "✓" if s['status'] == 'applied' else "○"
        print(f"  {status_icon} {s['version']}: {s['description']} ({s['status']})")
    
    print_subsection("Applying migrations")
    result = migrations.migrate()
    print(f"✓ Applied {result['applied']} migrations")
    print(f"✗ Failed: {result['failed']}")
    
    print_subsection("Current schema version")
    version = migrations.current_version()
    print(f"Current version: {version}")
    
    print_subsection("Rolling back last migration")
    rollback_result = migrations.rollback(steps=1)
    print(f"Rolled back {rollback_result['rolled_back']} migration(s)")
    print(f"Current version: {migrations.current_version()}")
    
    print_subsection("Re-applying migrations")
    migrations.migrate()
    print(f"Current version: {migrations.current_version()}")


def demo_cdc(db):
    """Demonstrate Change Data Capture."""
    print_section("2. CHANGE DATA CAPTURE (CDC)")
    
    cdc = CDCManager(db)
    
    print_subsection("Enabling CDC for tables")
    cdc.enable_table('users')
    cdc.enable_table('products')
    print("✓ CDC enabled for 'users' and 'products' tables")
    
    print_subsection("Adding change listener")
    changes_log = []
    
    def on_change(event):
        changes_log.append(event)
        print(f"  → {event.change_type.value} on {event.table} (row {event.row_id})")
    
    cdc.add_listener('users', on_change)
    cdc.add_listener('products', on_change)
    print("✓ Change listeners added")
    
    print_subsection("Capturing changes")
    
    # Simulate INSERT
    cdc.capture_change(
        table='users',
        change_type=ChangeType.INSERT,
        row_id=1,
        new_data={'id': 1, 'name': 'Alice', 'email': 'alice@example.com', 'age': 30}
    )
    
    # Simulate UPDATE
    cdc.capture_change(
        table='users',
        change_type=ChangeType.UPDATE,
        row_id=1,
        old_data={'name': 'Alice'},
        new_data={'name': 'Alice Smith'}
    )
    
    # Simulate DELETE
    cdc.capture_change(
        table='products',
        change_type=ChangeType.DELETE,
        row_id=1,
        old_data={'name': 'Old Product'}
    )
    
    print_subsection("Retrieving changes")
    all_changes = cdc.get_changes()
    print(f"Total changes captured: {len(all_changes)}")
    
    user_changes = cdc.get_changes('users')
    print(f"User table changes: {len(user_changes)}")
    
    inserts = cdc.get_changes('users', change_type=ChangeType.INSERT)
    print(f"User inserts: {len(inserts)}")
    
    print_subsection("CDC Statistics")
    stats = cdc.get_stats()
    print(f"Total changes: {stats['total_changes']}")
    print(f"Changes by table: {stats['changes_by_table']}")
    print(f"Changes by type: {stats['changes_by_type']}")


def demo_offline_mode(db):
    """Demonstrate offline mode."""
    print_section("3. OFFLINE MODE")
    
    offline = OfflineManager(db)
    
    print_subsection("Going offline")
    offline.go_offline()
    print(f"Online: {offline.is_online}")
    print(f"Offline: {offline.is_offline}")
    
    print_subsection("Queueing operations while offline")
    
    # Queue some operations
    op1 = offline.execute(
        "INSERT INTO users (name, email, age) VALUES (?, ?, ?)",
        ("Bob", "bob@example.com", 25),
        table="users"
    )
    print(f"✓ Queued operation 1: INSERT user (ID: {op1})")
    
    op2 = offline.execute(
        "INSERT INTO users (name, email, age) VALUES (?, ?, ?)",
        ("Charlie", "charlie@example.com", 35),
        table="users"
    )
    print(f"✓ Queued operation 2: INSERT user (ID: {op2})")
    
    print_subsection("Checking queue status")
    status = offline.get_queue_status()
    print(f"Total queued: {status['total_queued']}")
    print(f"By status: {status['by_status']}")
    
    print_subsection("Going online and syncing")
    offline.go_online()
    result = offline.sync()
    
    print(f"✓ Synced: {result['synced']} operations")
    print(f"✗ Failed: {result['failed']}")
    print(f"⏳ Remaining: {result['remaining']}")
    
    print_subsection("Verifying data was inserted")
    conn = db.get_connection()
    cursor = conn.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    print(f"Users in database: {count}")


def demo_mqtt_client():
    """Demonstrate MQTT client (simulated mode)."""
    print_section("4. MQTT CLIENT (Simulated Mode)")
    
    print_subsection("Creating MQTT client")
    client = MQTTClient(broker='localhost', port=1883)
    
    print("✓ MQTT client created (simulated mode)")
    
    print_subsection("Connecting to broker")
    connected = client.connect()
    print(f"✓ Connected: {connected}")
    
    print_subsection("Subscribing to topics")
    client.subscribe('sensors/temperature')
    client.subscribe('sensors/humidity')
    client.subscribe('devices/+/status')  # Wildcard subscription
    print(f"✓ Subscribed to {client.subscription_count} topics")
    
    print_subsection("Publishing messages")
    client.publish('sensors/temperature', {'value': 25.5, 'unit': 'Celsius'})
    print("✓ Published temperature reading")
    
    client.publish('sensors/humidity', {'value': 65.2, 'unit': 'Percent'})
    print("✓ Published humidity reading")
    
    client.publish('devices/sensor1/status', {'status': 'online', 'battery': 85})
    print("✓ Published device status")
    
    print_subsection("Retrieving queued messages")
    messages = client.get_queued_messages()
    print(f"Messages in queue: {len(messages)}")
    
    for msg in messages:
        print(f"  Topic: {msg.topic}")
        print(f"  Payload: {msg.payload}")
        print()
    
    print_subsection("Disconnecting")
    client.disconnect()
    print("✓ Disconnected")


def demo_transformer_nlq(db):
    """Demonstrate Transformer NLQ."""
    print_section("5. TRANSFORMER NLQ")
    
    nlq = TransformerNLQ()
    
    print_subsection("Model status")
    print(f"Has transformer: {nlq.has_transformer}")
    if nlq.has_transformer:
        print("Using HuggingFace transformer model")
    else:
        print("Using pattern matching fallback")
    
    print_subsection("Natural language queries")
    
    queries = [
        "show all users",
        "count users",
        "find users where age > 25",
        "show products",
        "count products"
    ]
    
    for query in queries:
        result = nlq.query_to_sql(query)
        print(f"\nQuery: '{query}'")
        print(f"  SQL: {result['sql']}")
        print(f"  Params: {result['params']}")
        print(f"  Confidence: {result['confidence']:.0%}")
        print(f"  Method: {result['method']}")


def demo_tutorials(db):
    """Demonstrate Tutorial System."""
    print_section("6. TUTORIAL SYSTEM")
    
    tutorials = TutorialManager(db)
    
    print_subsection("Available tutorials")
    all_tutorials = tutorials.list_tutorials()
    print(f"Total tutorials: {len(all_tutorials)}")
    
    print("\nTutorials by category:")
    categories = {}
    for t in all_tutorials:
        if t.category not in categories:
            categories[t.category] = []
        categories[t.category].append(t)
    
    for category, category_tutorials in categories.items():
        print(f"\n  {category}:")
        for t in category_tutorials:
            print(f"    - {t.title} ({t.difficulty}, {t.estimated_time} min)")
    
    print_subsection("Starting a tutorial")
    tutorial = tutorials.start_tutorial('basic_sql')
    
    if tutorial:
        print(f"✓ Started: {tutorial.title}")
        print(f"Description: {tutorial.description}")
        print(f"Steps: {len(tutorial.steps)}")
        print(f"Estimated time: {tutorial.estimated_time} minutes")
        
        print_subsection("First step")
        step = tutorials.get_current_step()
        print(f"Step {step.id}: {step.title}")
        print(f"Description: {step.description}")
        print(f"Code:\n{step.code}")
        if step.hint:
            print(f"Hint: {step.hint}")
        
        print_subsection("Tutorial progress")
        progress = tutorials.get_progress('basic_sql')
        print(f"Status: {progress['status']}")
        print(f"Current step: {progress['current_step']}")
        print(f"Progress: {progress['progress']:.0%}")
        
        print_subsection("Moving through steps")
        for i in range(min(3, len(tutorial.steps))):
            next_step = tutorials.next_step()
            if next_step:
                print(f"→ Step {next_step.id}: {next_step.title}")
        
        final_progress = tutorials.get_progress('basic_sql')
        print(f"\nProgress: {final_progress['progress']:.0%}")


def main():
    """Run complete demo."""
    print("=" * 70)
    print("  ULE - Universal Ledger Engine")
    print("  Complete Feature Demo")
    print("=" * 70)
    
    # Create temporary database
    fd, db_path = tempfile.mkstemp(suffix='.udb')
    os.close(fd)
    
    try:
        print(f"\nCreating test database: {db_path}")
        db = ULEDatabase(db_path)
        db.init()
        print("✓ Database initialized")
        
        # Run all demos
        demo_migrations(db)
        demo_cdc(db)
        demo_offline_mode(db)
        demo_mqtt_client()
        demo_transformer_nlq(db)
        demo_tutorials(db)
        
        # Final summary
        print_section("DEMO COMPLETE")
        print("\n✓ All features demonstrated successfully")
        print(f"\nDatabase location: {db_path}")
        print("\nFeatures demonstrated:")
        print("  1. ✓ Database Migrations")
        print("  2. ✓ Change Data Capture (CDC)")
        print("  3. ✓ Offline Mode")
        print("  4. ✓ MQTT Client")
        print("  5. ✓ Transformer NLQ")
        print("  6. ✓ Tutorial System")
        
        db.close()
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
            print(f"\nCleaned up test database")


if __name__ == '__main__':
    main()
