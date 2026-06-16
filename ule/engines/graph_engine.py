"""Graph Engine for ULE - Node relationships and traversals."""

import json
import hashlib
from typing import Any, Dict, List, Optional, Set, Tuple
from datetime import datetime, timezone
from collections import deque


class GraphEngine:
    """
    Graph engine for node relationships and traversals.
    
    Supports: link, traverse, path finding, neighbor queries
    """
    
    def __init__(self, db_connection):
        self._conn = db_connection
    
    def link(self, from_table: str, from_id: str, to_table: str, 
             to_id: str, relation: str, properties: Dict[str, Any] = None) -> str:
        """
        Create relationship between two nodes.
        
        Args:
            from_table: Source table name
            from_id: Source record ID
            to_table: Target table name
            to_id: Target record ID
            relation: Relationship type
            properties: Optional edge properties
        
        Returns:
            Edge hash
        """
        edge_hash = hashlib.sha256(
            f"{from_table}:{from_id}->{to_table}:{to_id}:{relation}:{datetime.now(timezone.utc).isoformat()}".encode()
        ).hexdigest()
        
        props_json = json.dumps(properties) if properties else None
        
        self._conn.execute(
            """INSERT OR REPLACE INTO _edges 
               (from_table, from_id, to_table, to_id, relation, properties, hash, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (from_table, from_id, to_table, to_id, relation, props_json, 
             edge_hash, datetime.now(timezone.utc).isoformat())
        )
        self._conn.commit()
        
        return edge_hash
    
    def unlink(self, from_table: str, from_id: str, to_table: str,
               to_id: str, relation: str = None) -> int:
        """
        Remove relationship.
        
        Args:
            from_table: Source table name
            from_id: Source record ID
            to_table: Target table name
            to_id: Target record ID
            relation: Optional relation filter
        
        Returns:
            Number of edges removed
        """
        sql = "DELETE FROM _edges WHERE from_table = ? AND from_id = ? AND to_table = ? AND to_id = ?"
        params = [from_table, from_id, to_table, to_id]
        
        if relation:
            sql += " AND relation = ?"
            params.append(relation)
        
        cursor = self._conn.execute(sql, tuple(params))
        self._conn.commit()
        
        return cursor.rowcount
    
    def traverse(self, table: str, start_id: str, depth: int = 2,
                 relation_filter: str = None) -> List[Dict]:
        """
        Traverse graph from starting point (BFS).
        
        Args:
            table: Starting table
            start_id: Starting record ID
            depth: Max depth to traverse
            relation_filter: Optional relation type filter
        
        Returns:
            List of edges traversed
        """
        results = []
        visited: Set[str] = set()
        queue = deque([(table, start_id, 0)])
        
        while queue:
            curr_table, curr_id, curr_depth = queue.popleft()
            
            if curr_depth > depth:
                continue
            
            key = f"{curr_table}:{curr_id}"
            if key in visited:
                continue
            visited.add(key)
            
            # Build query
            sql = """SELECT to_table, to_id, relation, properties FROM _edges
                     WHERE from_table = ? AND from_id = ?"""
            params = [curr_table, curr_id]
            
            if relation_filter:
                sql += " AND relation = ?"
                params.append(relation_filter)
            
            cursor = self._conn.execute(sql, tuple(params))
            
            for row in cursor:
                edge = {
                    "from": f"{curr_table}:{curr_id}",
                    "to": f"{row[0]}:{row[1]}",
                    "relation": row[2],
                    "properties": json.loads(row[3]) if row[3] else None,
                    "depth": curr_depth
                }
                results.append(edge)
                queue.append((row[0], row[1], curr_depth + 1))
        
        return results
    
    def find_path(self, from_table: str, from_id: str, 
                  to_table: str, to_id: str, 
                  max_depth: int = 10) -> Optional[List[Dict]]:
        """
        Find shortest path between two nodes (BFS).
        
        Args:
            from_table: Source table
            from_id: Source ID
            to_table: Target table
            to_id: Target ID
            max_depth: Maximum search depth
        
        Returns:
            List of edges in path, or None if no path found
        """
        target = f"{to_table}:{to_id}"
        visited: Set[str] = set()
        queue = deque([(from_table, from_id, [])])
        
        while queue:
            curr_table, curr_id, path = queue.popleft()
            
            if len(path) > max_depth:
                continue
            
            key = f"{curr_table}:{curr_id}"
            if key in visited:
                continue
            visited.add(key)
            
            # Check if target reached
            if key == target:
                return path
            
            # Explore neighbors
            cursor = self._conn.execute(
                """SELECT to_table, to_id, relation, properties FROM _edges
                   WHERE from_table = ? AND from_id = ?""",
                (curr_table, curr_id)
            )
            
            for row in cursor:
                edge = {
                    "from": f"{curr_table}:{curr_id}",
                    "to": f"{row[0]}:{row[1]}",
                    "relation": row[2],
                    "properties": json.loads(row[3]) if row[3] else None
                }
                new_path = path + [edge]
                queue.append((row[0], row[1], new_path))
        
        return None
    
    def neighbors(self, table: str, node_id: str, 
                  direction: str = "out",
                  relation_filter: str = None) -> List[Dict]:
        """
        Get neighboring nodes.
        
        Args:
            table: Table name
            node_id: Node ID
            direction: 'out', 'in', or 'both'
            relation_filter: Optional relation filter
        
        Returns:
            List of neighboring nodes
        """
        results = []
        
        if direction in ("out", "both"):
            sql = """SELECT to_table, to_id, relation, properties FROM _edges
                     WHERE from_table = ? AND from_id = ?"""
            params = [table, node_id]
            
            if relation_filter:
                sql += " AND relation = ?"
                params.append(relation_filter)
            
            cursor = self._conn.execute(sql, tuple(params))
            
            for row in cursor:
                results.append({
                    "table": row[0],
                    "id": row[1],
                    "relation": row[2],
                    "properties": json.loads(row[3]) if row[3] else None,
                    "direction": "out"
                })
        
        if direction in ("in", "both"):
            sql = """SELECT from_table, from_id, relation, properties FROM _edges
                     WHERE to_table = ? AND to_id = ?"""
            params = [table, node_id]
            
            if relation_filter:
                sql += " AND relation = ?"
                params.append(relation_filter)
            
            cursor = self._conn.execute(sql, tuple(params))
            
            for row in cursor:
                results.append({
                    "table": row[0],
                    "id": row[1],
                    "relation": row[2],
                    "properties": json.loads(row[3]) if row[3] else None,
                    "direction": "in"
                })
        
        return results
    
    def get_edges(self, from_table: str = None, from_id: str = None,
                  to_table: str = None, to_id: str = None,
                  relation: str = None) -> List[Dict]:
        """
        Get edges matching criteria.
        
        Args:
            from_table: Filter by source table
            from_id: Filter by source ID
            to_table: Filter by target table
            to_id: Filter by target ID
            relation: Filter by relation type
        
        Returns:
            List of edges
        """
        sql = "SELECT * FROM _edges WHERE 1=1"
        params = []
        
        if from_table:
            sql += " AND from_table = ?"
            params.append(from_table)
        
        if from_id:
            sql += " AND from_id = ?"
            params.append(from_id)
        
        if to_table:
            sql += " AND to_table = ?"
            params.append(to_table)
        
        if to_id:
            sql += " AND to_id = ?"
            params.append(to_id)
        
        if relation:
            sql += " AND relation = ?"
            params.append(relation)
        
        cursor = self._conn.execute(sql, tuple(params))
        
        return [
            {
                "from_table": row[0],
                "from_id": row[1],
                "to_table": row[2],
                "to_id": row[3],
                "relation": row[4],
                "properties": json.loads(row[5]) if row[5] else None,
                "hash": row[6],
                "created_at": row[7]
            }
            for row in cursor
        ]
    
    def get_relations(self, table: str = None) -> List[str]:
        """Get all unique relation types."""
        sql = "SELECT DISTINCT relation FROM _edges"
        params = []
        
        if table:
            sql += " WHERE from_table = ? OR to_table = ?"
            params = [table, table]
        
        cursor = self._conn.execute(sql, tuple(params))
        return [row[0] for row in cursor]
    
    def count_edges(self, table: str = None, node_id: str = None,
                    relation: str = None) -> int:
        """Count edges matching criteria."""
        sql = "SELECT COUNT(*) FROM _edges WHERE 1=1"
        params = []
        
        if table and node_id:
            sql += " AND (from_table = ? AND from_id = ? OR to_table = ? AND to_id = ?)"
            params.extend([table, node_id, table, node_id])
        elif relation:
            sql += " AND relation = ?"
            params.append(relation)
        
        cursor = self._conn.execute(sql, tuple(params))
        return cursor.fetchone()[0]
    
    def get_node_degree(self, table: str, node_id: str) -> Dict[str, int]:
        """
        Get node degree (number of connections).
        
        Args:
            table: Table name
            node_id: Node ID
        
        Returns:
            Dict with in_degree, out_degree, total
        """
        cursor = self._conn.execute(
            """SELECT 
               SUM(CASE WHEN from_table = ? AND from_id = ? THEN 1 ELSE 0 END) as out_degree,
               SUM(CASE WHEN to_table = ? AND to_id = ? THEN 1 ELSE 0 END) as in_degree
               FROM _edges
               WHERE (from_table = ? AND from_id = ?) OR (to_table = ? AND to_id = ?)""",
            (table, node_id, table, node_id, table, node_id, table, node_id)
        )
        
        row = cursor.fetchone()
        out_deg = row[0] or 0
        in_deg = row[1] or 0
        
        return {
            "in_degree": in_deg,
            "out_degree": out_deg,
            "total": in_deg + out_deg
        }
