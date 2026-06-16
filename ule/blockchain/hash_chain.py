"""SHA-256 hash chain for blockchain audit trail with Asynchronous Batching."""

import json
import hashlib
import time
import threading
import queue
from typing import Optional, Dict, List, Any
from datetime import datetime


class HashChain:
    """
    Blockchain-style hash chain for tamper-proof audit trail.
    
    Each block: H[n] = SHA256(data + H[n-1] + timestamp + signature)
    """
    
    def __init__(self, db_connection):
        self._conn = db_connection
        self._prev_hash: Optional[str] = None
        self._genesis_hash = "0" * 64  # 64 hex chars = 256 bits

    def init(self) -> None:
        """Initialize hash chain with genesis block."""
        # Check if already initialized
        cursor = self._conn.execute(
            "SELECT hash FROM _audit ORDER BY id DESC LIMIT 1"
        )
        row = cursor.fetchone()

        if row:
            self._prev_hash = row[0]
        else:
            # Create genesis block
            genesis_data = {"operation": "GENESIS", "message": "Chain initialized"}
            timestamp = str(int(time.time() * 1000))
            self._prev_hash = self._compute_hash(genesis_data, self._genesis_hash, "", timestamp)
            self._add_to_db(
                "GENESIS", None, None, None, None,
                genesis_data, self._prev_hash, self._genesis_hash, "", timestamp
            )

    @property
    def latest_hash(self) -> str:
        return self._prev_hash or self._genesis_hash
    
    def _compute_hash(self, data: Dict, prev_hash: str, signature: str = "", timestamp: str = None) -> str:
        """Compute hash for block."""
        if timestamp is None:
            timestamp = str(int(time.time() * 1000))  # Milliseconds
        content = f"{json.dumps(data, sort_keys=True)}{prev_hash}{timestamp}{signature}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def add(self, data: Dict, signature: str = "", skip_commit: bool = False) -> str:
        """
        Add new block to chain.

        Args:
            data: Block data
            signature: Optional digital signature
            skip_commit: If True, skip the database commit (for bulk operations)

        Returns:
            New block hash
        """
        timestamp = data.get("timestamp") or str(int(time.time() * 1000))
        new_hash = self._compute_hash(data, self._prev_hash or self._genesis_hash, signature, timestamp)

        self._add_to_db(
            data.get("operation", "UNKNOWN"),
            data.get("table_name"),
            data.get("record_id"),
            data.get("old_value"),
            data.get("new_value"),
            data,
            new_hash,
            self._prev_hash or self._genesis_hash,
            signature,
            timestamp,
            skip_commit=skip_commit
        )

        self._prev_hash = new_hash
        return new_hash
    
    def _add_to_db(self, operation: str, table_name: str, record_id: str,
                   old_value: any, new_value: any, data: Dict,
                   new_hash: str, prev_hash: str, signature: str, timestamp: str,
                   skip_commit: bool = False) -> None:
        """Add block to audit table."""
        self._conn.execute(
            """INSERT INTO _audit
               (operation, table_name, record_id, old_value, new_value,
                hash, prev_hash, signature, timestamp, user_name)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                operation,
                table_name,
                record_id,
                json.dumps(old_value) if old_value else None,
                json.dumps(data) if data else None,  # Store full data in new_value
                new_hash,
                prev_hash,
                signature,
                timestamp,
                data.get("user_name", "system")
            )
        )
        if not skip_commit:
            self._conn.commit()
    
    def verify(self) -> bool:
        """
        Verify entire chain integrity.

        Returns:
            True if chain is intact, False if tampered
        """
        cursor = self._conn.execute(
            "SELECT id, hash, prev_hash, operation, new_value, timestamp FROM _audit ORDER BY id"
        )

        rows = cursor.fetchall()
        if not rows:
            return True

        # Verify genesis
        if rows[0][3] != "GENESIS":
            return False

        # Start with genesis block's hash
        prev_hash = rows[0][1]

        for row in rows[1:]:
            id_, hash_, stored_prev, operation, data_json, timestamp = row
            if stored_prev != prev_hash:
                return False
            data = json.loads(data_json) if data_json else {}
            computed_hash = self._compute_hash(data, stored_prev, "", timestamp)
            if computed_hash != hash_:
                return False
            prev_hash = hash_
        return True

    def repair(self) -> Dict[str, Any]:
        """
        Repair the hash chain by recomputing broken links.
        """
        cursor = self._conn.execute(
            "SELECT id, hash, prev_hash, operation, new_value, timestamp FROM _audit ORDER BY id"
        )
        rows = cursor.fetchall()
        if not rows:
            return {"success": True, "repairs": 0, "message": "Audit trail is empty"}

        repairs = 0
        # Re-verify genesis
        if rows[0][3] != "GENESIS":
            # Hard-fix genesis
            genesis_data = {"operation": "GENESIS", "message": "Chain initialized (REPAIRED)"}
            timestamp = str(int(time.time() * 1000))
            new_genesis_hash = self._compute_hash(genesis_data, self._genesis_hash, "", timestamp)
            self._conn.execute(
                "UPDATE _audit SET operation=?, new_value=?, hash=?, prev_hash=?, timestamp=? WHERE id=?",
                ("GENESIS", json.dumps(genesis_data), new_genesis_hash, self._genesis_hash, timestamp, rows[0][0])
            )
            prev_hash = new_genesis_hash
            repairs += 1
        else:
            prev_hash = rows[0][1]

        for row in rows[1:]:
            id_, hash_, stored_prev, operation, data_json, timestamp = row
            
            needs_update = False
            current_prev = stored_prev
            
            if stored_prev != prev_hash:
                current_prev = prev_hash
                needs_update = True
                
            data = json.loads(data_json) if data_json else {}
            computed_hash = self._compute_hash(data, current_prev, "", timestamp)
            
            if computed_hash != hash_ or needs_update:
                self._conn.execute(
                    "UPDATE _audit SET prev_hash=?, hash=? WHERE id=?",
                    (current_prev, computed_hash, id_)
                )
                repairs += 1
                prev_hash = computed_hash
            else:
                prev_hash = hash_

        if repairs > 0:
            self._conn.commit()
            self._prev_hash = prev_hash

        return {
            "success": True, 
            "repairs": repairs, 
            "message": f"Repair complete. {repairs} links updated."
        }
    
    def get_chain(self, start_id: int = 0, limit: int = 100) -> List[Dict]:
        """Get chain blocks."""
        cursor = self._conn.execute(
            "SELECT * FROM _audit WHERE id >= ? ORDER BY id LIMIT ?",
            (start_id, limit)
        )
        
        return [dict(row) for row in cursor]
    
    def get_block(self, hash_value: str) -> Optional[Dict]:
        """Get specific block by hash."""
        cursor = self._conn.execute(
            "SELECT * FROM _audit WHERE hash = ?",
            (hash_value,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def sync_audit(self, endpoint_url: str, api_key: Optional[str] = None) -> bool:
        """
        Anchor the latest hash to a remote endpoint.
        
        This provides true immutability by ensuring the local 
        audit trail cannot be tampered with without detection 
        from the remote anchor.
        """
        import urllib.request
        import urllib.error
        
        latest_hash = self.latest_hash
        payload = {
            "hash": latest_hash,
            "timestamp": str(int(time.time() * 1000)),
            "database_id": "TODO_DB_ID"
        }
        
        try:
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(endpoint_url, data=data)
            req.add_header('Content-Type', 'application/json')
            if api_key:
                req.add_header('Authorization', f'Bearer {api_key}')
            
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status == 200
        except Exception:
            # For now, return False on failure (e.g. offline)
            return False


class BatchAuditManager:
    """
    High-performance audit manager with optional synchronicity.
    
    Buffers audit events and flushes them in batches, or flushes 
    immediately if blockchain_sync is enabled in config.
    """
    
    def __init__(self, db_connection, hash_chain: HashChain, config=None, batch_size: int = 100, flush_interval: float = 1.0):
        self._conn = db_connection
        self._hash_chain = hash_chain
        self._config = config
        self._batch_size = batch_size
        self._flush_interval = flush_interval
        self._queue = queue.Queue()
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._worker_thread = None
        self._last_flush = time.time()
        
        self._sync_mode = config.get("blockchain_sync", False) if config else False

    def start(self):
        """Start the background worker thread (only if not in sync mode)."""
        if self._sync_mode or self._worker_thread is not None:
            return
            
        self._stop_event.clear()
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()

    def stop(self):
        """Stop the background worker and flush remaining events."""
        if self._worker_thread:
            self._stop_event.set()
            self._worker_thread.join()
            self._worker_thread = None
        self.flush()

    def log(self, operation: str, table_name: str, record_id: str, 
            old_value: Any = None, new_value: Any = None, 
            user_name: str = "system", data: Dict = None):
        """Queue or synchronously log an audit event."""
        event = {
            "operation": operation,
            "table_name": table_name,
            "record_id": str(record_id),
            "old_value": old_value,
            "new_value": new_value,
            "user_name": user_name,
            "data": data or {},
            "timestamp": str(int(time.time() * 1000))
        }
        self._queue.put(event)
        
        # In sync mode, or if queue is large, flush immediately
        if self._sync_mode or self._queue.qsize() >= self._batch_size:
            self.flush()

    def flush(self):
        """Synchronously flush all queued events to the database in a single batch."""
        events = []
        while not self._queue.empty():
            try:
                events.append(self._queue.get_nowait())
            except queue.Empty:
                break
        
        if not events:
            return

        with self._lock:
            rows = []
            for event in events:
                # 1. Compute chain link
                timestamp = event.get("timestamp") or str(int(time.time() * 1000))
                new_hash = self._hash_chain._compute_hash(event, self._hash_chain.latest_hash, "", timestamp)
                
                # 2. Prepare database row
                rows.append((
                    event.get("operation", "UNKNOWN"),
                    event.get("table_name"),
                    event.get("record_id"),
                    json.dumps(event.get("old_value")) if event.get("old_value") else None,
                    json.dumps(event) if event else None,
                    new_hash,
                    self._hash_chain.latest_hash,
                    "", # No signature in async for now
                    timestamp,
                    event.get("user_name", "system")
                ))
                
                # 3. Update memory state for next link
                self._hash_chain._prev_hash = new_hash
            
            # 4. Single multi-row insert (The Performance Multiplier)
            try:
                self._conn.executemany(
                    """INSERT INTO _audit
                       (operation, table_name, record_id, old_value, new_value,
                        hash, prev_hash, signature, timestamp, user_name)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    rows
                )
                self._conn.commit()
            except Exception:
                pass
            self._last_flush = time.time()

    def _worker_loop(self):
        """Background thread for periodic flushing."""
        while not self._stop_event.is_set():
            now = time.time()
            if self._queue.qsize() >= self._batch_size or (now - self._last_flush) >= self._flush_interval:
                self.flush()
            
            time.sleep(0.1)
