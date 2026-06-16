"""IoT Domain Model for ULE.

IoT device management data model with:
- Devices registry
- Sensor readings
- Alerts
- Device groups
- Commands
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import json


class IoTModel:
    """IoT domain model."""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn
        self._create_tables()

    def _create_tables(self):
        """Create IoT tables."""
        tables = [
            """CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                device_type TEXT,
                manufacturer TEXT,
                model TEXT,
                firmware_version TEXT,
                status TEXT DEFAULT 'offline' CHECK(status IN ('online', 'offline', 'maintenance', 'error')),
                last_seen TEXT,
                location TEXT,
                group_id TEXT,
                metadata TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )""",

            """CREATE TABLE IF NOT EXISTS device_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )""",

            """CREATE TABLE IF NOT EXISTS sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reading_id TEXT UNIQUE NOT NULL,
                device_id TEXT NOT NULL,
                sensor_type TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT,
                timestamp TEXT NOT NULL,
                quality TEXT DEFAULT 'good' CHECK(quality IN ('good', 'suspect', 'bad')),
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (device_id) REFERENCES devices(device_id)
            )""",

            """CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id TEXT UNIQUE NOT NULL,
                device_id TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                severity TEXT CHECK(severity IN ('info', 'warning', 'critical')),
                message TEXT,
                value REAL,
                threshold REAL,
                status TEXT DEFAULT 'active' CHECK(status IN ('active', 'acknowledged', 'resolved')),
                created_at TEXT DEFAULT (datetime('now')),
                resolved_at TEXT,
                FOREIGN KEY (device_id) REFERENCES devices(device_id)
            )""",

            """CREATE TABLE IF NOT EXISTS commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command_id TEXT UNIQUE NOT NULL,
                device_id TEXT NOT NULL,
                command TEXT NOT NULL,
                parameters TEXT,
                status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'sent', 'executed', 'failed')),
                sent_at TEXT,
                executed_at TEXT,
                result TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (device_id) REFERENCES devices(device_id)
            )""",

            """CREATE TABLE IF NOT EXISTS device_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                config_key TEXT NOT NULL,
                config_value TEXT,
                updated_at TEXT DEFAULT (datetime('now')),
                UNIQUE(device_id, config_key),
                FOREIGN KEY (device_id) REFERENCES devices(device_id)
            )""",
        ]

        for table_sql in tables:
            self._conn.execute(table_sql)
        self._conn.commit()

    def register_device(self, **kwargs) -> str:
        """Register a new IoT device."""
        import uuid
        device_id = f"DEV-{uuid.uuid4().hex[:8].upper()}"
        
        self._conn.execute(
            """INSERT INTO devices (device_id, name, device_type, manufacturer, model,
               firmware_version, location, group_id, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (device_id, kwargs.get('name'), kwargs.get('device_type'),
             kwargs.get('manufacturer'), kwargs.get('model'),
             kwargs.get('firmware_version'), kwargs.get('location'),
             kwargs.get('group_id'), json.dumps(kwargs.get('metadata', {})))
        )
        self._conn.commit()
        return device_id

    def create_device_group(self, name: str, **kwargs) -> str:
        """Create a device group."""
        import uuid
        group_id = f"GRP-{uuid.uuid4().hex[:8].upper()}"
        
        self._conn.execute(
            """INSERT INTO device_groups (group_id, name, description)
               VALUES (?, ?, ?)""",
            (group_id, name, kwargs.get('description'))
        )
        self._conn.commit()
        return group_id

    def record_sensor_reading(self, device_id: str, sensor_type: str, 
                             value: float, **kwargs) -> str:
        """Record a sensor reading."""
        import uuid
        reading_id = f"RDG-{uuid.uuid4().hex[:8].upper()}"
        
        self._conn.execute(
            """INSERT INTO sensor_readings (reading_id, device_id, sensor_type,
               value, unit, timestamp, quality)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (reading_id, device_id, sensor_type, value,
             kwargs.get('unit'), kwargs.get('timestamp', datetime.now().isoformat()),
             kwargs.get('quality', 'good'))
        )
        
        # Update device last seen
        self._conn.execute(
            "UPDATE devices SET last_seen = ?, updated_at = datetime('now'), status='online' WHERE device_id = ?",
            (datetime.now().isoformat(), device_id)
        )
        self._conn.commit()
        return reading_id

    def create_alert(self, device_id: str, alert_type: str, 
                    severity: str, **kwargs) -> str:
        """Create an alert."""
        import uuid
        alert_id = f"ALT-{uuid.uuid4().hex[:8].upper()}"
        
        self._conn.execute(
            """INSERT INTO alerts (alert_id, device_id, alert_type, severity,
               message, value, threshold)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (alert_id, device_id, alert_type, severity,
             kwargs.get('message'), kwargs.get('value'), kwargs.get('threshold'))
        )
        self._conn.commit()
        return alert_id

    def send_command(self, device_id: str, command: str, **kwargs) -> str:
        """Send a command to a device."""
        import uuid
        command_id = f"CMD-{uuid.uuid4().hex[:8].upper()}"
        
        self._conn.execute(
            """INSERT INTO commands (command_id, device_id, command, parameters)
               VALUES (?, ?, ?, ?)""",
            (command_id, device_id, command, json.dumps(kwargs.get('parameters', {})))
        )
        self._conn.commit()
        return command_id

    def get_device_readings(self, device_id: str, sensor_type: Optional[str] = None,
                           hours: int = 24) -> List[Dict]:
        """Get recent sensor readings for a device."""
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        if sensor_type:
            cursor = self._conn.execute(
                """SELECT * FROM sensor_readings 
                   WHERE device_id = ? AND sensor_type = ? AND timestamp >= ?
                   ORDER BY timestamp DESC""",
                (device_id, sensor_type, since)
            )
        else:
            cursor = self._conn.execute(
                """SELECT * FROM sensor_readings 
                   WHERE device_id = ? AND timestamp >= ?
                   ORDER BY timestamp DESC""",
                (device_id, since)
            )
        return [dict(zip([d[0] for d in cursor.description], row)) for row in cursor.fetchall()]

    def get_active_alerts(self) -> List[Dict]:
        """Get all active alerts."""
        cursor = self._conn.execute(
            """SELECT a.*, d.name as device_name, d.location as device_location
               FROM alerts a
               JOIN devices d ON a.device_id = d.device_id
               WHERE a.status = 'active'
               ORDER BY a.created_at DESC"""
        )
        return [dict(zip([d[0] for d in cursor.description], row)) for row in cursor.fetchall()]

    def get_iot_summary(self) -> Dict[str, Any]:
        """Get IoT summary."""
        return {
            'total_devices': self._conn.execute("SELECT COUNT(*) FROM devices").fetchone()[0],
            'online_devices': self._conn.execute("SELECT COUNT(*) FROM devices WHERE status='online'").fetchone()[0],
            'total_readings': self._conn.execute("SELECT COUNT(*) FROM sensor_readings").fetchone()[0],
            'active_alerts': self._conn.execute("SELECT COUNT(*) FROM alerts WHERE status='active'").fetchone()[0],
            'pending_commands': self._conn.execute("SELECT COUNT(*) FROM commands WHERE status='pending'").fetchone()[0],
            'generated_at': datetime.now().isoformat()
        }
