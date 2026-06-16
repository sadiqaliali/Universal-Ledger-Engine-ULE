"""Write-Ahead Logging for crash recovery."""

import json
import os
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime


class WriteAheadLog:
    """
    WAL for durability and crash recovery.
    
    All writes are first logged before being applied to the database.
    """
    
    def __init__(self, wal_path: str):
        self.wal_path = Path(wal_path)
        self._file = None
        self._buffer: List[Dict] = []
        self._checkpoint_interval = 100
        self._write_count = 0
    
    def init(self) -> None:
        """Initialize WAL file."""
        if not self.wal_path.exists():
            with open(self.wal_path, 'w') as f:
                json.dump({"version": 1, "entries": []}, f)
        try:
            self._file = open(self.wal_path, 'r+')
        except Exception:
            self._file = None

    def write(self, operation: str, data: any, params: tuple = None) -> None:
        """
        Write entry to WAL.

        Args:
            operation: Operation type (SQL, PUSH, LINK, etc.)
            data: Operation data
            params: Optional parameters
        """
        if self._file is None:
            return  # WAL not initialized, skip logging
        
        entry = {
            "lsn": self._write_count,
            "timestamp": datetime.utcnow().isoformat(),
            "operation": operation,
            "data": data,
            "params": list(params) if params else None,
            "committed": False
        }
        
        self._buffer.append(entry)
        self._write_count += 1
        
        # Checkpoint if buffer is full
        if len(self._buffer) >= self._checkpoint_interval:
            self.checkpoint()
    
    def checkpoint(self) -> None:
        """Flush buffer to disk."""
        if not self._buffer:
            return
        
        # Read existing WAL
        self._file.seek(0)
        wal_data = json.load(self._file)
        
        # Mark entries as committed and append
        for entry in self._buffer:
            entry["committed"] = True
            wal_data["entries"].append(entry)
        
        # Write back
        self._file.seek(0)
        self._file.truncate()
        json.dump(wal_data, self._file, indent=2)
        self._file.flush()
        os.fsync(self._file.fileno())
        
        self._buffer.clear()
    
    def replay(self) -> List[Dict]:
        """
        Replay WAL for recovery.
        
        Returns:
            List of uncommitted entries to replay
        """
        if not self.wal_path.exists():
            return []
        
        with open(self.wal_path, 'r') as f:
            wal_data = json.load(f)
        
        # Return only committed entries that need replay
        return [e for e in wal_data.get("entries", []) if e.get("committed")]
    
    def truncate(self, up_to_lsn: int) -> None:
        """Remove entries up to LSN."""
        self._file.seek(0)
        wal_data = json.load(self._file)
        
        wal_data["entries"] = [e for e in wal_data.get("entries", []) 
                               if e.get("lsn", 0) > up_to_lsn]
        
        self._file.seek(0)
        self._file.truncate()
        json.dump(wal_data, self._file, indent=2)
        self._file.flush()
    
    def close(self) -> None:
        """Close WAL file."""
        if self._buffer:
            self.checkpoint()
        
        if self._file:
            self._file.close()
            self._file = None
