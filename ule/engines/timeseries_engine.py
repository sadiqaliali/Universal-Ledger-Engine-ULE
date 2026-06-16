"""Time-Series Engine for ULE.

High-performance time-series data storage and querying with:
- Automatic time partitioning
- Downsampling and aggregation
- Retention policies
- Range queries
- Continuous queries
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple
from collections import defaultdict


class TimeSeriesEngine:
    """Time-series data engine for ULE."""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn
        self._create_tables()

    def _create_tables(self):
        """Create time-series tables."""
        tables = [
            """CREATE TABLE IF NOT EXISTS ts_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT NOT NULL,
                tags TEXT,
                timestamp TEXT NOT NULL,
                value REAL NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            )""",

            """CREATE TABLE IF NOT EXISTS ts_downsampled (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT NOT NULL,
                tags TEXT,
                interval_start TEXT NOT NULL,
                interval_end TEXT NOT NULL,
                aggregation TEXT CHECK(aggregation IN ('avg', 'sum', 'min', 'max', 'count')),
                value REAL NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            )""",

            """CREATE TABLE IF NOT EXISTS ts_retention_policies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                policy_name TEXT UNIQUE NOT NULL,
                metric_pattern TEXT NOT NULL,
                retention_days INTEGER NOT NULL,
                downsample_interval TEXT,
                downsample_aggregation TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )""",

            """CREATE INDEX IF NOT EXISTS idx_ts_metrics_name ON ts_metrics(metric_name)""",
            """CREATE INDEX IF NOT EXISTS idx_ts_metrics_timestamp ON ts_metrics(timestamp)""",
            """CREATE INDEX IF NOT EXISTS idx_ts_metrics_name_ts ON ts_metrics(metric_name, timestamp)""",
        ]

        for table_sql in tables:
            self._conn.execute(table_sql)
        self._conn.commit()

    def insert(self, metric_name: str, value: float, 
               tags: Optional[Dict] = None, timestamp: Optional[str] = None) -> int:
        """Insert a time-series data point."""
        ts = timestamp or datetime.now().isoformat()
        tags_json = json.dumps(tags) if tags else '{}'
        
        cursor = self._conn.execute(
            """INSERT INTO ts_metrics (metric_name, tags, timestamp, value)
               VALUES (?, ?, ?, ?)""",
            (metric_name, tags_json, ts, value)
        )
        self._conn.commit()
        return cursor.lastrowid

    def insert_batch(self, points: List[Dict]) -> int:
        """Insert multiple time-series data points."""
        count = 0
        for point in points:
            ts = point.get('timestamp', datetime.now().isoformat())
            tags_json = json.dumps(point.get('tags', {}))
            
            self._conn.execute(
                """INSERT INTO ts_metrics (metric_name, tags, timestamp, value)
                   VALUES (?, ?, ?, ?)""",
                (point['metric_name'], tags_json, ts, point['value'])
            )
            count += 1
        self._conn.commit()
        return count

    def query_range(self, metric_name: str, start: str, end: str,
                   tags: Optional[Dict] = None, limit: int = 1000) -> List[Dict]:
        """Query time-series data in a time range."""
        if tags:
            # Build tag filter
            tag_filters = []
            for key, value in tags.items():
                tag_filters.append(f'"{key}":"{value}"')
            tag_filter = " AND tags LIKE ?"
            tag_param = f"%{tag_filters[0]}%"
        else:
            tag_filter = ""
            tag_param = None

        query = f"""SELECT metric_name, tags, timestamp, value
                    FROM ts_metrics
                    WHERE metric_name = ? AND timestamp >= ? AND timestamp <= ?{tag_filter}
                    ORDER BY timestamp ASC
                    LIMIT ?"""
        
        if tag_param:
            cursor = self._conn.execute(query, (metric_name, start, end, tag_param, limit))
        else:
            cursor = self._conn.execute(query, (metric_name, start, end, limit))
        
        return [dict(zip([d[0] for d in cursor.description], row)) for row in cursor.fetchall()]

    def query_latest(self, metric_name: str, count: int = 1,
                    tags: Optional[Dict] = None) -> List[Dict]:
        """Query the latest time-series data points."""
        query = """SELECT metric_name, tags, timestamp, value
                   FROM ts_metrics
                   WHERE metric_name = ?
                   ORDER BY timestamp DESC
                   LIMIT ?"""
        
        cursor = self._conn.execute(query, (metric_name, count))
        return [dict(zip([d[0] for d in cursor.description], row)) for row in cursor.fetchall()]

    def downsample(self, metric_name: str, interval: str = '1h',
                  aggregation: str = 'avg', start: Optional[str] = None,
                  end: Optional[str] = None) -> int:
        """Downsample time-series data."""
        if start is None:
            start = (datetime.now() - timedelta(days=7)).isoformat()
        if end is None:
            end = datetime.now().isoformat()

        # Get raw data
        cursor = self._conn.execute(
            """SELECT timestamp, value FROM ts_metrics
               WHERE metric_name = ? AND timestamp >= ? AND timestamp <= ?
               ORDER BY timestamp""",
            (metric_name, start, end)
        )
        rows = cursor.fetchall()

        if not rows:
            return 0

        # Parse interval
        interval_seconds = self._parse_interval(interval)
        
        # Group by interval
        buckets = defaultdict(list)
        for ts, value in rows:
            dt = datetime.fromisoformat(ts)
            bucket_start = dt.replace(second=0, microsecond=0)
            bucket_start = bucket_start.replace(
                minute=(bucket_start.minute // (interval_seconds // 60)) * (interval_seconds // 60)
            )
            buckets[bucket_start.isoformat()].append(value)

        # Calculate aggregations
        count = 0
        for bucket_start, values in buckets.items():
            bucket_end = (datetime.fromisoformat(bucket_start) + timedelta(seconds=interval_seconds)).isoformat()
            
            if aggregation == 'avg':
                agg_value = sum(values) / len(values)
            elif aggregation == 'sum':
                agg_value = sum(values)
            elif aggregation == 'min':
                agg_value = min(values)
            elif aggregation == 'max':
                agg_value = max(values)
            elif aggregation == 'count':
                agg_value = len(values)
            else:
                agg_value = sum(values) / len(values)

            self._conn.execute(
                """INSERT INTO ts_downsampled (metric_name, tags, interval_start, interval_end,
                   aggregation, value)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (metric_name, '{}', bucket_start, bucket_end, aggregation, agg_value)
            )
            count += 1

        self._conn.commit()
        return count

    def add_retention_policy(self, policy_name: str, metric_pattern: str,
                            retention_days: int, **kwargs) -> str:
        """Add a retention policy."""
        self._conn.execute(
            """INSERT INTO ts_retention_policies (policy_name, metric_pattern,
               retention_days, downsample_interval, downsample_aggregation)
               VALUES (?, ?, ?, ?, ?)""",
            (policy_name, metric_pattern, retention_days,
             kwargs.get('downsample_interval'), kwargs.get('downsample_aggregation', 'avg'))
        )
        self._conn.commit()
        return policy_name

    def apply_retention(self) -> int:
        """Apply retention policies and delete old data."""
        cursor = self._conn.execute("SELECT * FROM ts_retention_policies")
        policies = [dict(zip([d[0] for d in cursor.description], row)) for row in cursor.fetchall()]

        deleted = 0
        for policy in policies:
            cutoff = (datetime.now() - timedelta(days=policy['retention_days'])).isoformat()
            
            cursor = self._conn.execute(
                "DELETE FROM ts_metrics WHERE metric_name LIKE ? AND timestamp < ?",
                (policy['metric_pattern'].replace('*', '%'), cutoff)
            )
            deleted += cursor.rowcount

        self._conn.commit()
        return deleted

    def get_stats(self, metric_name: str) -> Dict[str, Any]:
        """Get statistics for a metric."""
        cursor = self._conn.execute(
            """SELECT COUNT(*) as count, MIN(value) as min_val, MAX(value) as max_val,
                      AVG(value) as avg_val, SUM(value) as sum_val
               FROM ts_metrics WHERE metric_name = ?""",
            (metric_name,)
        )
        row = cursor.fetchone()
        
        return {
            'metric_name': metric_name,
            'count': row[0],
            'min': row[1],
            'max': row[2],
            'avg': row[3],
            'sum': row[4]
        }

    def _parse_interval(self, interval: str) -> int:
        """Parse interval string to seconds."""
        if interval.endswith('s'):
            return int(interval[:-1])
        elif interval.endswith('m'):
            return int(interval[:-1]) * 60
        elif interval.endswith('h'):
            return int(interval[:-1]) * 3600
        elif interval.endswith('d'):
            return int(interval[:-1]) * 86400
        else:
            return 3600  # Default 1 hour
