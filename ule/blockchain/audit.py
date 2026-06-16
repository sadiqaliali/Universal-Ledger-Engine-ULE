"""Audit trail queries for ULE."""

import json
from typing import Optional, List, Dict
from datetime import datetime


class AuditTrail:
    """Query and analyze audit trail."""
    
    def __init__(self, db_connection):
        self._conn = db_connection
    
    def get_history(self, table_name: str, record_id: str) -> List[Dict]:
        """
        Get complete history of a record.
        
        Args:
            table_name: Table name
            record_id: Record identifier
        
        Returns:
            List of audit entries
        """
        cursor = self._conn.execute(
            """SELECT operation, old_value, new_value, hash, prev_hash, 
                      timestamp, user_name, signature
               FROM _audit 
               WHERE table_name = ? AND record_id = ?
               ORDER BY timestamp ASC""",
            (table_name, record_id)
        )
        
        return [dict(row) for row in cursor]
    
    def get_changes_by_user(self, username: str, 
                           start_time: str = None,
                           end_time: str = None) -> List[Dict]:
        """Get all changes made by a user."""
        sql = """SELECT operation, table_name, record_id, new_value, hash, timestamp
                 FROM _audit WHERE user_name = ?"""
        params = [username]
        
        if start_time:
            sql += " AND timestamp >= ?"
            params.append(start_time)
        
        if end_time:
            sql += " AND timestamp <= ?"
            params.append(end_time)
        
        sql += " ORDER BY timestamp DESC"
        
        cursor = self._conn.execute(sql, tuple(params))
        return [dict(row) for row in cursor]
    
    def get_changes_in_range(self, start_time: str, end_time: str) -> List[Dict]:
        """Get all changes in time range."""
        cursor = self._conn.execute(
            """SELECT * FROM _audit 
               WHERE timestamp BETWEEN ? AND ?
               ORDER BY timestamp ASC""",
            (start_time, end_time)
        )
        
        return [dict(row) for row in cursor]
    
    def get_operations_by_type(self, operation: str) -> List[Dict]:
        """Get all operations of a specific type."""
        cursor = self._conn.execute(
            "SELECT * FROM _audit WHERE operation = ? ORDER BY timestamp DESC",
            (operation,)
        )
        
        return [dict(row) for row in cursor]
    
    def get_statistics(self) -> Dict:
        """Get audit statistics."""
        cursor = self._conn.execute(
            """SELECT operation, COUNT(*) as count
               FROM _audit
               GROUP BY operation"""
        )
        
        stats = {"total": 0, "by_operation": {}}
        
        for row in cursor:
            stats["by_operation"][row[0]] = row[1]
            stats["total"] += row[1]
        
        return stats
    
    def time_travel_query(self, table_name: str, as_of: str) -> List[Dict]:
        """
        Query table state at a specific point in time.
        
        Args:
            table_name: Table to query
            as_of: ISO timestamp
        
        Returns:
            Table state at that time
        """
        # Get all operations up to as_of time
        cursor = self._conn.execute(
            """SELECT record_id, operation, new_value, old_value
               FROM _audit
               WHERE table_name = ? AND timestamp <= ?
               ORDER BY timestamp ASC""",
            (table_name, as_of)
        )
        
        # Reconstruct state
        state = {}
        
        for row in cursor:
            record_id = row[0]
            operation = row[1]
            
            if operation == "INSERT":
                state[record_id] = json.loads(row[2]) if row[2] else {}
            elif operation == "UPDATE":
                if record_id in state:
                    state[record_id].update(json.loads(row[2]) if row[2] else {})
            elif operation == "DELETE":
                state.pop(record_id, None)
        
        return list(state.values())
