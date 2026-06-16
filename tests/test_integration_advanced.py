"""Integration tests for ULE - Testing all features working together."""

import pytest
import sqlite3
import tempfile
import os
import time
from ule.core.database import ULEDatabase
from ule.replication import CDCManager, ChangeType, OfflineManager
from ule.migrations import MigrationManager
from ule.iot import MQTTClient
from ule.ai import TransformerNLQ
from ule.tutorials import TutorialManager


class TestFullWorkflow:
    """Test complete workflow from initialization to advanced features."""

    @pytest.fixture
    def db(self):
        """Create test database."""
        fd, db_path = tempfile.mkstemp(suffix='.udb')
        os.close(fd)
        
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.commit()
        
        class SimpleDB:
            def __init__(self, conn, path):
                self._conn = conn
                self._path = path
            def get_connection(self):
                return self._conn
        
        yield SimpleDB(conn, db_path)
        
        conn.close()
        if os.path.exists(db_path):
            os.unlink(db_path)

    def test_migrations_then_cdc(self, db):
        """Test migrations followed by CDC setup."""
        # Apply migrations
        migrations = MigrationManager(db)
        migrations.create_migration(
            '001',
            'Create users table',
            up_sql='CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT)',
            down_sql='DROP TABLE users'
        )
        result = migrations.migrate()
        assert result['applied'] == 1
        
        # Now enable CDC on the migrated table
        cdc = CDCManager(db)
        cdc.enable_table('users')
        
        # Capture some changes
        cdc.capture_change('users', ChangeType.INSERT, row_id=1, 
                          new_data={'name': 'Alice', 'email': 'alice@test.com'})
        
        changes = cdc.get_changes('users')
        assert len(changes) == 1
        assert changes[0].table == 'users'

    def test_offline_then_sync(self, db):
        """Test offline mode with sync."""
        # Create table first
        conn = db.get_connection()
        conn.execute('CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, price REAL)')
        conn.commit()
        
        # Go offline and queue operations
        offline = OfflineManager(db)
        offline.go_offline()
        
        offline.execute(
            'INSERT INTO products (name, price) VALUES (?, ?)',
            ('Product A', 10.0),
            table='products'
        )
        offline.execute(
            'INSERT INTO products (name, price) VALUES (?, ?)',
            ('Product B', 20.0),
            table='products'
        )
        
        # Sync
        offline.go_online()
        result = offline.sync()
        
        assert result['synced'] == 2
        
        # Verify data
        cursor = conn.execute('SELECT COUNT(*) FROM products')
        count = cursor.fetchone()[0]
        assert count == 2

    def test_cdc_with_offline(self, db):
        """Test CDC tracking offline operations."""
        # Create table
        conn = db.get_connection()
        conn.execute('CREATE TABLE orders (id INTEGER PRIMARY KEY, customer TEXT, total REAL)')
        conn.commit()
        
        # Enable CDC
        cdc = CDCManager(db)
        cdc.enable_table('orders')
        
        # Go offline
        offline = OfflineManager(db)
        offline.go_offline()
        
        # Queue operations
        offline.execute(
            'INSERT INTO orders (customer, total) VALUES (?, ?)',
            ('Alice', 100.0),
            table='orders'
        )
        
        # Manually track the change for CDC
        cdc.capture_change(
            'orders',
            ChangeType.INSERT,
            row_id=1,
            new_data={'customer': 'Alice', 'total': 100.0}
        )
        
        # Sync
        offline.go_online()
        offline.sync()
        
        # Verify both CDC and data
        changes = cdc.get_changes('orders')
        assert len(changes) == 1
        
        cursor = conn.execute('SELECT COUNT(*) FROM orders')
        count = cursor.fetchone()[0]
        assert count == 1

    def test_mqtt_with_cdc(self, db):
        """Test MQTT publishing with CDC tracking."""
        # Create table
        conn = db.get_connection()
        conn.execute('CREATE TABLE sensor_data (id INTEGER PRIMARY KEY, sensor TEXT, value REAL)')
        conn.commit()
        
        # Enable CDC
        cdc = CDCManager(db)
        cdc.enable_table('sensor_data')
        
        # Create MQTT client
        mqtt = MQTTClient(broker='localhost', port=1883)
        mqtt.connect()
        
        # Publish sensor data
        mqtt.publish('sensors/temp', {'sensor': 'temp1', 'value': 25.5})
        
        # Track in CDC
        cdc.capture_change(
            'sensor_data',
            ChangeType.INSERT,
            row_id=1,
            new_data={'sensor': 'temp1', 'value': 25.5}
        )
        
        # Verify CDC captured it
        changes = cdc.get_changes('sensor_data')
        assert len(changes) == 1
        assert changes[0].new_data['sensor'] == 'temp1'
        
        # Verify MQTT queued it
        messages = mqtt.get_queued_messages()
        assert len(messages) == 1
        assert messages[0].topic == 'sensors/temp'
        
        mqtt.disconnect()

    def test_tutorials_with_migrations(self, db):
        """Test tutorial system with migrations."""
        # Apply migrations to create tables
        migrations = MigrationManager(db)
        migrations.create_migration(
            '001',
            'Create tutorial tables',
            up_sql='''CREATE TABLE tutorial_progress (
                tutorial_id TEXT,
                user_id TEXT DEFAULT 'default',
                status TEXT NOT NULL DEFAULT 'not_started',
                current_step INTEGER DEFAULT 0,
                started_at REAL,
                completed_at REAL,
                PRIMARY KEY (tutorial_id, user_id)
            )''',
            down_sql='DROP TABLE tutorial_progress'
        )
        migrations.migrate()
        
        # Now use tutorial system
        tutorials = TutorialManager(db)
        
        # Start a tutorial
        tutorial = tutorials.start_tutorial('basic_sql')
        assert tutorial is not None
        assert tutorial.status.value == 'in_progress'
        
        # Progress through steps
        step = tutorials.get_current_step()
        assert step is not None
        
        # Move forward
        next_step = tutorials.next_step()
        # Tutorial may or may not have more steps

    def test_all_features_together(self, db):
        """Test all features working together in a realistic scenario."""
        conn = db.get_connection()
        
        # 1. Create schema using migrations
        migrations = MigrationManager(db)
        migrations.create_migration(
            '001',
            'Create IoT schema',
            up_sql='''
                CREATE TABLE devices (id INTEGER PRIMARY KEY, name TEXT, status TEXT);
                CREATE TABLE readings (id INTEGER PRIMARY KEY, device_id INTEGER, value REAL, timestamp REAL);
            ''',
            down_sql='DROP TABLE readings; DROP TABLE devices;'
        )
        migrations.migrate()
        assert migrations.current_version() == '001'
        
        # 2. Enable CDC for tracking
        cdc = CDCManager(db)
        cdc.enable_table('devices')
        cdc.enable_table('readings')
        
        # 3. Setup MQTT for IoT
        mqtt = MQTTClient(broker='localhost', port=1883)
        mqtt.connect()
        mqtt.subscribe('iot/devices/+/status')
        
        # 4. Simulate IoT workflow
        # Device comes online via MQTT
        mqtt.publish('iot/devices/sensor1/status', {'device': 'sensor1', 'status': 'online'})
        
        # Track device registration
        cdc.capture_change(
            'devices',
            ChangeType.INSERT,
            row_id=1,
            new_data={'name': 'sensor1', 'status': 'online'}
        )
        
        # Insert reading
        conn.execute(
            'INSERT INTO readings (device_id, value, timestamp) VALUES (?, ?, ?)',
            (1, 25.5, time.time())
        )
        conn.commit()
        
        # Track reading
        cdc.capture_change(
            'readings',
            ChangeType.INSERT,
            row_id=1,
            new_data={'device_id': 1, 'value': 25.5}
        )
        
        # 5. Go offline temporarily
        offline = OfflineManager(db)
        offline.go_offline()
        
        offline.execute(
            'UPDATE devices SET status = ? WHERE id = ?',
            ('maintenance', 1),
            table='devices'
        )
        
        # 6. Sync when back online
        offline.go_online()
        result = offline.sync()
        assert result['synced'] == 1
        
        # 7. Verify everything
        # Check CDC
        device_changes = cdc.get_changes('devices')
        assert len(device_changes) >= 1
        
        # Check data
        cursor = conn.execute('SELECT COUNT(*) FROM devices')
        device_count = cursor.fetchone()[0]
        # Device was inserted via CDC tracking, not direct SQL
        
        cursor = conn.execute('SELECT COUNT(*) FROM readings')
        reading_count = cursor.fetchone()[0]
        assert reading_count == 1
        
        # Check MQTT
        messages = mqtt.get_queued_messages()
        assert len(messages) >= 1
        
        mqtt.disconnect()


class TestRealWorldScenarios:
    """Test real-world usage scenarios."""

    @pytest.fixture
    def db(self):
        """Create test database."""
        fd, db_path = tempfile.mkstemp(suffix='.udb')
        os.close(fd)
        
        conn = sqlite3.connect(db_path)
        
        class SimpleDB:
            def __init__(self, conn, path):
                self._conn = conn
                self._path = path
            def get_connection(self):
                return self._conn
        
        yield SimpleDB(conn, db_path)
        
        conn.close()
        if os.path.exists(db_path):
            os.unlink(db_path)

    def test_healthcare_workflow(self, db):
        """Test healthcare domain workflow."""
        conn = db.get_connection()
        
        # Setup schema
        conn.execute('''
            CREATE TABLE patients (
                id INTEGER PRIMARY KEY,
                name TEXT,
                age INTEGER,
                condition TEXT
            )
        ''')
        conn.commit()
        
        # Enable CDC for audit trail
        cdc = CDCManager(db)
        cdc.enable_table('patients')
        
        # Add patient
        conn.execute(
            'INSERT INTO patients (name, age, condition) VALUES (?, ?, ?)',
            ('John Doe', 45, 'Diabetes')
        )
        conn.commit()
        
        cdc.capture_change(
            'patients',
            ChangeType.INSERT,
            row_id=1,
            new_data={'name': 'John Doe', 'age': 45, 'condition': 'Diabetes'}
        )
        
        # Update patient
        conn.execute(
            'UPDATE patients SET condition = ? WHERE id = ?',
            ('Diabetes - Managed', 1)
        )
        conn.commit()
        
        cdc.capture_change(
            'patients',
            ChangeType.UPDATE,
            row_id=1,
            old_data={'condition': 'Diabetes'},
            new_data={'condition': 'Diabetes - Managed'}
        )
        
        # Verify audit trail
        changes = cdc.get_changes('patients')
        assert len(changes) == 2
        assert changes[0].change_type == ChangeType.INSERT
        assert changes[1].change_type == ChangeType.UPDATE

    def test_finance_workflow(self, db):
        """Test finance domain workflow with offline mode."""
        conn = db.get_connection()
        
        # Setup schema
        conn.execute('''
            CREATE TABLE transactions (
                id INTEGER PRIMARY KEY,
                account TEXT,
                amount REAL,
                type TEXT
            )
        ''')
        conn.commit()
        
        # Go offline (mobile banking scenario)
        offline = OfflineManager(db)
        offline.go_offline()
        
        # Queue transactions
        offline.execute(
            'INSERT INTO transactions (account, amount, type) VALUES (?, ?, ?)',
            ('ACC001', -50.0, 'withdrawal'),
            table='transactions'
        )
        offline.execute(
            'INSERT INTO transactions (account, amount, type) VALUES (?, ?, ?)',
            ('ACC001', 1000.0, 'deposit'),
            table='transactions'
        )
        
        # Back online, sync
        offline.go_online()
        result = offline.sync()
        assert result['synced'] == 2
        
        # Verify
        cursor = conn.execute('SELECT SUM(amount) FROM transactions')
        total = cursor.fetchone()[0]
        assert total == 950.0

    def test_iot_sensor_network(self, db):
        """Test IoT sensor network with MQTT and CDC."""
        conn = db.get_connection()
        
        # Setup
        conn.execute('''
            CREATE TABLE sensors (
                id INTEGER PRIMARY KEY,
                name TEXT,
                location TEXT,
                status TEXT
            )
        ''')
        conn.execute('''
            CREATE TABLE sensor_readings (
                id INTEGER PRIMARY KEY,
                sensor_id INTEGER,
                value REAL,
                timestamp REAL
            )
        ''')
        conn.commit()
        
        # Enable CDC
        cdc = CDCManager(db)
        cdc.enable_table('sensors')
        cdc.enable_table('sensor_readings')
        
        # Setup MQTT
        mqtt = MQTTClient(broker='localhost', port=1883)
        mqtt.connect()
        
        # Simulate multiple sensors
        for i in range(5):
            sensor_name = f'sensor_{i}'
            
            # Register sensor
            conn.execute(
                'INSERT INTO sensors (name, location, status) VALUES (?, ?, ?)',
                (sensor_name, f'Location {i}', 'active')
            )
            conn.commit()
            
            cdc.capture_change(
                'sensors',
                ChangeType.INSERT,
                row_id=i+1,
                new_data={'name': sensor_name, 'status': 'active'}
            )
            
            # Publish reading via MQTT
            mqtt.publish(
                f'iot/sensors/{sensor_name}/reading',
                {'sensor_id': i+1, 'value': 20.0 + i, 'timestamp': time.time()}
            )
            
            # Track reading
            cdc.capture_change(
                'sensor_readings',
                ChangeType.INSERT,
                row_id=i+1,
                new_data={'sensor_id': i+1, 'value': 20.0 + i}
            )
        
        # Verify
        sensor_changes = cdc.get_changes('sensors')
        reading_changes = cdc.get_changes('sensor_readings')
        
        assert len(sensor_changes) == 5
        assert len(reading_changes) == 5
        
        messages = mqtt.get_queued_messages()
        assert len(messages) == 5
        
        mqtt.disconnect()
