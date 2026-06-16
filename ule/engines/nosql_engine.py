"""NoSQL Document Engine for ULE."""

import json
import hashlib
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone


class NoSQL_Engine:
    """
    Document store engine with MongoDB-like queries.
    
    Supports: push, find, update, delete, schema enforcement
    """
    
    def __init__(self, db_connection):
        self._conn = db_connection
    
    def push(self, collection: str, data: Dict[str, Any], 
             encrypt_fn=None) -> str:
        """
        Push document to collection.
        
        Args:
            collection: Collection name
            data: Document data
            encrypt_fn: Optional encryption function
        
        Returns:
            Document ID
        """
        # Generate ID
        doc_id = data.get("_id")
        if not doc_id:
            doc_id = hashlib.sha256(
                f"{collection}{json.dumps(data, sort_keys=True)}{datetime.now(timezone.utc).isoformat()}".encode()
            ).hexdigest()[:16]
        
        # Serialize
        data_json = json.dumps(data)
        
        # Encrypt if provided
        if encrypt_fn:
            data_json = encrypt_fn(data_json)
        
        # Compute hash
        doc_hash = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
        
        # Insert
        self._conn.execute(
            """INSERT OR REPLACE INTO _documents 
               (collection, doc_id, data, hash, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (collection, doc_id, data_json, doc_hash, datetime.now(timezone.utc).isoformat())
        )
        self._conn.commit()
        
        return doc_id
    
    def find(self, collection: str, query: Dict[str, Any] = None,
             limit: int = 100, decrypt_fn=None) -> List[Dict]:
        """
        Find documents in collection.
        
        Args:
            collection: Collection name
            query: Query filter (MongoDB-style)
            limit: Max results
            decrypt_fn: Optional decryption function
        
        Returns:
            List of matching documents
        """
        sql = "SELECT doc_id, data, hash FROM _documents WHERE collection = ?"
        params = [collection]

        # Optimize: If not encrypted, use SQLite JSON1 extension for filtering
        if query and not decrypt_fn:
            where_clause, query_params = self._build_where_clause(query)
            if where_clause:
                sql += " AND " + where_clause
                params.extend(query_params)

        sql += " LIMIT ?"
        params.append(limit)

        cursor = self._conn.execute(sql, tuple(params))
        results = []
        
        for row in cursor:
            doc_id = row[0]
            data = row[1]
            
            # Decrypt if needed
            if decrypt_fn:
                try:
                    data = decrypt_fn(data)
                except Exception:
                    continue # Skip if decryption fails
            
            doc = json.loads(data)
            
            # If we couldn't filter in SQL (e.g. complex operators or encrypted), filter in Python
            if query and decrypt_fn and not self._matches(doc, query):
                continue
            
            doc["_id"] = doc_id
            results.append(doc)
        
        return results

    def _build_where_clause(self, query: Dict) -> Tuple[str, List]:
        """Build SQL WHERE clause using SQLite JSON1 functions."""
        filters = []
        params = []
        
        for key, value in query.items():
            # Ensure path is just the key name for json_extract
            json_path = f"$.{key}"
            
            if isinstance(value, dict):
                for op, op_value in value.items():
                    if op == "$eq":
                        filters.append(f"json_extract(data, ?) = ?")
                        params.extend([json_path, op_value])
                    elif op == "$gt":
                        filters.append(f"json_extract(data, ?) > ?")
                        params.extend([json_path, op_value])
                    elif op == "$lt":
                        filters.append(f"json_extract(data, ?) < ?")
                        params.extend([json_path, op_value])
                    elif op == "$in" and isinstance(op_value, list):
                        placeholders = ", ".join("?" * len(op_value))
                        filters.append(f"json_extract(data, ?) IN ({placeholders})")
                        params.append(json_path)
                        params.extend(op_value)
            else:
                filters.append(f"json_extract(data, ?) = ?")
                params.extend([json_path, value])
        
        return " AND ".join(filters), params
    
    def find_one(self, collection: str, query: Dict[str, Any] = None,
                 decrypt_fn=None) -> Optional[Dict]:
        """Find single document."""
        results = self.find(collection, query, limit=1, decrypt_fn=decrypt_fn)
        return results[0] if results else None
    
    def update(self, collection: str, query: Dict[str, Any],
               update: Dict[str, Any], upsert: bool = False) -> int:
        """
        Update documents.

        Args:
            collection: Collection name
            query: Query filter
            update: Update operations
            upsert: Insert if not found

        Returns:
            Number of documents updated
        """
        # Find matching documents
        docs = self.find(collection, query)

        if not docs:
            if upsert:
                # Create new document
                new_doc = query.copy()
                self._apply_update(new_doc, update)
                self.push(collection, new_doc)
                return 1
            return 0

        count = 0
        for doc in docs:
            doc_id = doc.get("_id")
            # Apply update to the document
            self._apply_update(doc, update)
            
            # Update existing document with same ID
            data_json = json.dumps(doc)
            doc_hash = hashlib.sha256(json.dumps(doc, sort_keys=True).encode()).hexdigest()
            
            self._conn.execute(
                """UPDATE _documents SET data = ?, hash = ? 
                   WHERE collection = ? AND doc_id = ?""",
                (data_json, doc_hash, collection, doc_id)
            )
            self._conn.commit()
            count += 1

        return count
    
    def delete(self, collection: str, query: Dict[str, Any] = None) -> int:
        """
        Delete documents.
        
        Args:
            collection: Collection name
            query: Query filter (None for all)
        
        Returns:
            Number of documents deleted
        """
        if query is None:
            # Delete all in collection
            cursor = self._conn.execute(
                "DELETE FROM _documents WHERE collection = ?",
                (collection,)
            )
        else:
            # Find and delete matching
            docs = self.find(collection, query)
            for doc in docs:
                self._conn.execute(
                    "DELETE FROM _documents WHERE collection = ? AND doc_id = ?",
                    (collection, doc["_id"])
                )
            cursor = type('obj', (object,), {'rowcount': len(docs)})
        
        self._conn.commit()
        return cursor.rowcount
    
    def _matches(self, doc: Dict, query: Dict) -> bool:
        """Check if document matches query."""
        for key, value in query.items():
            doc_value = self._get_nested_value(doc, key)
            
            # Handle operators
            if isinstance(value, dict):
                for op, op_value in value.items():
                    if not self._apply_operator(doc_value, op, op_value):
                        return False
            else:
                if doc_value != value:
                    return False
        
        return True
    
    def _get_nested_value(self, doc: Dict, key: str) -> Any:
        """Get nested value using dot notation."""
        if "." not in key:
            return doc.get(key)
        
        parts = key.split(".")
        value = doc
        
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
        
        return value
    
    def _apply_operator(self, value: Any, op: str, op_value: Any) -> bool:
        """Apply MongoDB-style operator."""
        if op == "$eq":
            return value == op_value
        elif op == "$ne":
            return value != op_value
        elif op == "$gt":
            return value is not None and value > op_value
        elif op == "$gte":
            return value is not None and value >= op_value
        elif op == "$lt":
            return value is not None and value < op_value
        elif op == "$lte":
            return value is not None and value <= op_value
        elif op == "$in":
            return value in op_value
        elif op == "$nin":
            return value not in op_value
        elif op == "$exists":
            return (value is not None) == op_value
        elif op == "$regex":
            import re
            return bool(re.search(op_value, str(value)))
        elif op == "$all":
            if not isinstance(value, list):
                return False
            return all(v in value for v in op_value)
        elif op == "$elemMatch":
            if not isinstance(value, list):
                return False
            return any(self._matches(elem, op_value) for elem in value)
        
        return True
    
    def _apply_update(self, doc: Dict, update: Dict) -> None:
        """Apply update operations to document."""
        for op, fields in update.items():
            if op == "$set":
                for key, value in fields.items():
                    self._set_nested_value(doc, key, value)
            elif op == "$unset":
                for key in fields:
                    self._remove_nested_value(doc, key)
            elif op == "$inc":
                for key, value in fields.items():
                    current = self._get_nested_value(doc, key) or 0
                    self._set_nested_value(doc, key, current + value)
            elif op == "$push":
                for key, value in fields.items():
                    arr = self._get_nested_value(doc, key) or []
                    arr.append(value)
                    self._set_nested_value(doc, key, arr)
            elif op == "$pull":
                for key, value in fields.items():
                    arr = self._get_nested_value(doc, key) or []
                    arr = [v for v in arr if v != value]
                    self._set_nested_value(doc, key, arr)
    
    def _set_nested_value(self, doc: Dict, key: str, value: Any) -> None:
        """Set nested value using dot notation."""
        if "." not in key:
            doc[key] = value
            return
        
        parts = key.split(".")
        current = doc
        
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        current[parts[-1]] = value
    
    def _remove_nested_value(self, doc: Dict, key: str) -> None:
        """Remove nested value using dot notation."""
        if "." not in key:
            doc.pop(key, None)
            return
        
        parts = key.split(".")
        current = doc
        
        for part in parts[:-1]:
            if part not in current:
                return
            current = current[part]
        
        current.pop(parts[-1], None)
    
    def count(self, collection: str, query: Dict[str, Any] = None) -> int:
        """Count documents in collection."""
        docs = self.find(collection, query, limit=10000)
        return len(docs)
    
    def create_index(self, collection: str, fields: List[str]) -> None:
        """Create index on collection (future implementation)."""
        # TODO: Implement indexing
        pass
    
    def aggregate(self, collection: str, pipeline: List[Dict]) -> List[Dict]:
        """
        Aggregate documents (basic implementation).
        
        Supports: $match, $project, $limit, $sort, $group
        """
        results = self.find(collection)
        
        for stage in pipeline:
            if "$match" in stage:
                results = [d for d in results if self._matches(d, stage["$match"])]
            elif "$limit" in stage:
                results = results[:stage["$limit"]]
            elif "$sort" in stage:
                for key, order in reversed(stage["$sort"].items()):
                    results.sort(key=lambda x: x.get(key, ""), reverse=(order < 0))
            elif "$project" in stage:
                projected = []
                for doc in results:
                    new_doc = {}
                    for key, include in stage["$project"].items():
                        if include:
                            new_doc[key] = doc.get(key)
                    projected.append(new_doc)
                results = projected
        
        return results
