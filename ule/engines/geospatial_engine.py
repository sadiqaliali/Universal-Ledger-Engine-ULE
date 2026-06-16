"""Geospatial Engine for ULE.

Geospatial data management with:
- Point, line, polygon storage
- Distance calculations
- Radius queries
- Bounding box queries
- Geofencing
"""

import sqlite3
import math
import json
from datetime import datetime
from typing import Optional, Dict, List, Any, Tuple


class GeospatialEngine:
    """Geospatial data engine for ULE."""

    EARTH_RADIUS_KM = 6371.0

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn
        self._create_tables()

    def _create_tables(self):
        """Create geospatial tables."""
        tables = [
            """CREATE TABLE IF NOT EXISTS geo_points (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                point_id TEXT UNIQUE NOT NULL,
                name TEXT,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                altitude REAL,
                tags TEXT,
                metadata TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )""",

            """CREATE TABLE IF NOT EXISTS geo_polygons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                polygon_id TEXT UNIQUE NOT NULL,
                name TEXT,
                coordinates TEXT NOT NULL,
                tags TEXT,
                metadata TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )""",

            """CREATE TABLE IF NOT EXISTS geo_fences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fence_id TEXT UNIQUE NOT NULL,
                name TEXT,
                center_lat REAL NOT NULL,
                center_lon REAL NOT NULL,
                radius_meters REAL NOT NULL,
                tags TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )""",

            """CREATE INDEX IF NOT EXISTS idx_geo_points_lat ON geo_points(latitude)""",
            """CREATE INDEX IF NOT EXISTS idx_geo_points_lon ON geo_points(longitude)""",
        ]

        for table_sql in tables:
            self._conn.execute(table_sql)
        self._conn.commit()

    def add_point(self, latitude: float, longitude: float, **kwargs) -> str:
        """Add a geospatial point."""
        import uuid
        point_id = f"GPT-{uuid.uuid4().hex[:8].upper()}"
        
        self._conn.execute(
            """INSERT INTO geo_points (point_id, name, latitude, longitude, altitude, tags, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (point_id, kwargs.get('name'), latitude, longitude,
             kwargs.get('altitude'), json.dumps(kwargs.get('tags', {})),
             json.dumps(kwargs.get('metadata', {})))
        )
        self._conn.commit()
        return point_id

    def add_polygon(self, coordinates: List[Tuple[float, float]], **kwargs) -> str:
        """Add a polygon (area)."""
        import uuid
        polygon_id = f"PLY-{uuid.uuid4().hex[:8].upper()}"
        
        coords_json = json.dumps(coordinates)
        
        self._conn.execute(
            """INSERT INTO geo_polygons (polygon_id, name, coordinates, tags, metadata)
               VALUES (?, ?, ?, ?, ?)""",
            (polygon_id, kwargs.get('name'), coords_json,
             json.dumps(kwargs.get('tags', {})), json.dumps(kwargs.get('metadata', {})))
        )
        self._conn.commit()
        return polygon_id

    def add_fence(self, center_lat: float, center_lon: float, 
                 radius_meters: float, **kwargs) -> str:
        """Add a geofence."""
        import uuid
        fence_id = f"FNC-{uuid.uuid4().hex[:8].upper()}"
        
        self._conn.execute(
            """INSERT INTO geo_fences (fence_id, name, center_lat, center_lon,
               radius_meters, tags)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (fence_id, kwargs.get('name'), center_lat, center_lon,
             radius_meters, json.dumps(kwargs.get('tags', {})))
        )
        self._conn.commit()
        return fence_id

    def find_nearby(self, latitude: float, longitude: float, 
                   radius_km: float = 10.0, limit: int = 100) -> List[Dict]:
        """Find points within a radius."""
        cursor = self._conn.execute("SELECT * FROM geo_points")
        all_points = [dict(zip([d[0] for d in cursor.description], row)) for row in cursor.fetchall()]

        nearby = []
        for point in all_points:
            distance = self.haversine_distance(latitude, longitude, 
                                              point['latitude'], point['longitude'])
            if distance <= radius_km:
                point['distance_km'] = distance
                nearby.append(point)

        nearby.sort(key=lambda x: x['distance_km'])
        return nearby[:limit]

    def find_in_bbox(self, min_lat: float, min_lon: float, 
                    max_lat: float, max_lon: float) -> List[Dict]:
        """Find points within a bounding box."""
        cursor = self._conn.execute(
            """SELECT * FROM geo_points
               WHERE latitude >= ? AND latitude <= ?
               AND longitude >= ? AND longitude <= ?""",
            (min_lat, max_lat, min_lon, max_lon)
        )
        return [dict(zip([d[0] for d in cursor.description], row)) for row in cursor.fetchall()]

    def check_fence(self, latitude: float, longitude: float) -> List[Dict]:
        """Check which fences contain a point."""
        cursor = self._conn.execute("SELECT * FROM geo_fences")
        fences = [dict(zip([d[0] for d in cursor.description], row)) for row in cursor.fetchall()]

        inside = []
        for fence in fences:
            distance = self.haversine_distance(latitude, longitude,
                                              fence['center_lat'], fence['center_lon'])
            if distance * 1000 <= fence['radius_meters']:  # Convert km to meters
                fence['distance_meters'] = distance * 1000
                inside.append(fence)

        return inside

    def distance_between(self, lat1: float, lon1: float, 
                        lat2: float, lon2: float) -> float:
        """Calculate distance between two points in km."""
        return self.haversine_distance(lat1, lon1, lat2, lon2)

    def haversine_distance(self, lat1: float, lon1: float, 
                          lat2: float, lon2: float) -> float:
        """Calculate the great circle distance between two points on earth (km)."""
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return self.EARTH_RADIUS_KM * c

    def get_point(self, point_id: str) -> Optional[Dict]:
        """Get a specific point."""
        cursor = self._conn.execute(
            "SELECT * FROM geo_points WHERE point_id = ?",
            (point_id,)
        )
        row = cursor.fetchone()
        if row:
            return dict(zip([d[0] for d in cursor.description], row))
        return None

    def update_point(self, point_id: str, **kwargs) -> bool:
        """Update a point's location."""
        updates = []
        values = []
        
        if 'latitude' in kwargs:
            updates.append('latitude = ?')
            values.append(kwargs['latitude'])
        if 'longitude' in kwargs:
            updates.append('longitude = ?')
            values.append(kwargs['longitude'])
        if 'altitude' in kwargs:
            updates.append('altitude = ?')
            values.append(kwargs['altitude'])
        if 'name' in kwargs:
            updates.append('name = ?')
            values.append(kwargs['name'])
        if 'tags' in kwargs:
            updates.append('tags = ?')
            values.append(json.dumps(kwargs['tags']))
        
        if not updates:
            return False
        
        values.append(point_id)
        self._conn.execute(
            f"UPDATE geo_points SET {', '.join(updates)} WHERE point_id = ?",
            values
        )
        self._conn.commit()
        return True

    def delete_point(self, point_id: str) -> bool:
        """Delete a point."""
        cursor = self._conn.execute(
            "DELETE FROM geo_points WHERE point_id = ?",
            (point_id,)
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def get_stats(self) -> Dict[str, Any]:
        """Get geospatial statistics."""
        return {
            'total_points': self._conn.execute("SELECT COUNT(*) FROM geo_points").fetchone()[0],
            'total_polygons': self._conn.execute("SELECT COUNT(*) FROM geo_polygons").fetchone()[0],
            'total_fences': self._conn.execute("SELECT COUNT(*) FROM geo_fences").fetchone()[0],
        }
