"""Database Integrity Checker for ULE.

This module provides self-healing database integrity with:
- SHA-256 checksums for every page
- Triple redundancy for critical data
- Automatic corruption detection and repair
- Quarantine system for bad pages
"""

import hashlib
import json
import sqlite3
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import shutil


class IntegrityChecker:
    """
    Self-healing database integrity checker.
    
    Features:
    - Compute checksums for all pages
    - Store redundant copies of critical data
    - Detect corruption on read
    - Auto-repair from backup copies
    - Quarantine corrupted pages
    """
    
    def __init__(self, db_path: str, redundancy_factor: int = 3):
        """
        Initialize integrity checker.
        
        Args:
            db_path: Path to database file
            redundancy_factor: Number of redundant copies (default 3)
        """
        self.db_path = Path(db_path)
        self.redundancy_factor = redundancy_factor
        self._conn: Optional[sqlite3.Connection] = None
        self._checksums: Dict[int, str] = {}
        self._quarantine: List[Dict] = []
    
    def connect(self) -> None:
        """Connect to database."""
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        
        # Create integrity tables if not exist
        self._init_integrity_tables()
    
    def _init_integrity_tables(self) -> None:
        """Create tables for integrity metadata."""
        tables = [
            # Checksums table
            """CREATE TABLE IF NOT EXISTS _integrity_checksums (
                page_id INTEGER PRIMARY KEY,
                checksum TEXT NOT NULL,
                computed_at TEXT DEFAULT (datetime('now')),
                verified_at TEXT
            )""",
            
            # Redundant copies table
            """CREATE TABLE IF NOT EXISTS _integrity_redundancy (
                table_name TEXT,
                record_id TEXT,
                copy_number INTEGER,
                data BLOB,
                checksum TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                PRIMARY KEY (table_name, record_id, copy_number)
            )""",
            
            # Quarantine table
            """CREATE TABLE IF NOT EXISTS _integrity_quarantine (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT,
                record_id TEXT,
                reason TEXT,
                detected_at TEXT DEFAULT (datetime('now')),
                repaired INTEGER DEFAULT 0,
                repaired_at TEXT
            )""",
        ]
        
        for sql in tables:
            self._conn.execute(sql)
        self._conn.commit()
    
    def compute_checksum(self, data: bytes) -> str:
        """
        Compute SHA-256 checksum for data.
        
        Args:
            data: Binary data
            
        Returns:
            Hex-encoded SHA-256 checksum
        """
        return hashlib.sha256(data).hexdigest()
    
    def verify_checksum(self, data: bytes, expected_checksum: str) -> bool:
        """
        Verify data against expected checksum.
        
        Args:
            data: Binary data
            expected_checksum: Expected SHA-256 checksum
            
        Returns:
            True if checksum matches
        """
        actual_checksum = self.compute_checksum(data)
        return actual_checksum == expected_checksum
    
    def store_with_redundancy(self, table_name: str, record_id: str,
                              data: Dict[str, Any]) -> List[str]:
        """
        Store data with redundant copies.
        
        Args:
            table_name: Table name
            record_id: Record identifier
            data: Data to store
            
        Returns:
            List of checksums for each copy
        """
        checksums = []
        data_json = json.dumps(data, sort_keys=True).encode('utf-8')
        
        for i in range(self.redundancy_factor):
            # Add copy number to data for variation
            copy_data = data_json + f"_copy{i}".encode()
            checksum = self.compute_checksum(copy_data)
            
            self._conn.execute(
                """INSERT OR REPLACE INTO _integrity_redundancy 
                   (table_name, record_id, copy_number, data, checksum)
                   VALUES (?, ?, ?, ?, ?)""",
                (table_name, record_id, i, copy_data, checksum)
            )
            checksums.append(checksum)
        
        self._conn.commit()
        return checksums
    
    def retrieve_with_verification(self, table_name: str,
                                   record_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve data with integrity verification and auto-repair.
        
        Args:
            table_name: Table name
            record_id: Record identifier
            
        Returns:
            Verified data dictionary, or None if all copies corrupted
        """
        cursor = self._conn.execute(
            """SELECT copy_number, data, checksum 
               FROM _integrity_redundancy 
               WHERE table_name = ? AND record_id = ?
               ORDER BY copy_number""",
            (table_name, record_id)
        )
        
        copies = cursor.fetchall()
        if not copies:
            return None
        
        # Try each copy
        valid_data = None
        valid_checksum = None
        
        for copy in copies:
            copy_number = copy[0]
            data = copy[1]
            stored_checksum = copy[2]
            
            # Verify checksum
            if self.verify_checksum(data, stored_checksum):
                # Remove copy suffix from data
                data_str = data.decode('utf-8')
                if data_str.endswith(f"_copy{copy_number}"):
                    data_str = data_str[:-len(f"_copy{copy_number}")]
                
                valid_data = json.loads(data_str)
                valid_checksum = stored_checksum
                break
        
        # If no valid copy found, try to repair
        if valid_data is None:
            valid_data = self._attempt_repair(table_name, record_id, copies)
        
        return valid_data
    
    def _attempt_repair(self, table_name: str, record_id: str,
                       copies: list) -> Optional[Dict[str, Any]]:
        """
        Attempt to repair corrupted data using majority voting.
        
        Args:
            table_name: Table name
            record_id: Record identifier
            copies: List of (copy_number, data, checksum) tuples
            
        Returns:
            Repaired data or None
        """
        if len(copies) < 2:
            # Not enough copies to repair
            self._quarantine_record(table_name, record_id, 
                                   "Insufficient copies for repair")
            return None
        
        # Try to find consensus among copies
        data_versions = {}
        
        for copy in copies:
            copy_number = copy[0]
            data = copy[1]
            
            # Remove copy suffix
            data_str = data.decode('utf-8')
            if data_str.endswith(f"_copy{copy_number}"):
                data_str = data_str[:-len(f"_copy{copy_number}")]
            
            if data_str in data_versions:
                data_versions[data_str] += 1
            else:
                data_versions[data_str] = 1
        
        # Find majority version
        majority_data = max(data_versions.items(), key=lambda x: x[1])
        
        if majority_data[1] > len(copies) / 2:
            # Majority agrees, use this version
            repaired_data = json.loads(majority_data[0])
            
            # Log repair
            self._log_repair(table_name, record_id, "Majority voting")
            
            # Restore good copies
            self._restore_copies(table_name, record_id, repaired_data)
            
            return repaired_data
        else:
            # No majority, quarantine
            self._quarantine_record(table_name, record_id,
                                   "No consensus among copies")
            return None
    
    def _restore_copies(self, table_name: str, record_id: str,
                       data: Dict[str, Any]) -> None:
        """Restore redundant copies after repair."""
        data_json = json.dumps(data, sort_keys=True).encode('utf-8')
        
        for i in range(self.redundancy_factor):
            copy_data = data_json + f"_copy{i}".encode()
            checksum = self.compute_checksum(copy_data)
            
            self._conn.execute(
                """INSERT OR REPLACE INTO _integrity_redundancy 
                   (table_name, record_id, copy_number, data, checksum)
                   VALUES (?, ?, ?, ?, ?)""",
                (table_name, record_id, i, copy_data, checksum)
            )
        
        self._conn.commit()
    
    def _quarantine_record(self, table_name: str, record_id: str,
                          reason: str) -> None:
        """Add record to quarantine."""
        self._conn.execute(
            """INSERT INTO _integrity_quarantine 
               (table_name, record_id, reason)
               VALUES (?, ?, ?)""",
            (table_name, record_id, reason)
        )
        self._conn.commit()
        
        self._quarantine.append({
            "table_name": table_name,
            "record_id": record_id,
            "reason": reason,
            "detected_at": datetime.utcnow().isoformat()
        })
    
    def _log_repair(self, table_name: str, record_id: str,
                   method: str) -> None:
        """Log successful repair."""
        self._conn.execute(
            """UPDATE _integrity_quarantine 
               SET repaired = 1, repaired_at = datetime('now')
               WHERE table_name = ? AND record_id = ?""",
            (table_name, record_id)
        )
        self._conn.commit()
    
    def verify_table(self, table_name: str) -> Dict[str, Any]:
        """
        Verify integrity of all records in a table.
        
        Args:
            table_name: Table to verify
            
        Returns:
            Verification report
        """
        cursor = self._conn.execute(
            """SELECT DISTINCT record_id FROM _integrity_redundancy 
               WHERE table_name = ?""",
            (table_name,)
        )
        
        record_ids = [row[0] for row in cursor]
        
        report = {
            "table_name": table_name,
            "total_records": len(record_ids),
            "verified": 0,
            "corrupted": 0,
            "repaired": 0,
            "details": []
        }
        
        for record_id in record_ids:
            result = self.retrieve_with_verification(table_name, record_id)
            
            if result is not None:
                report["verified"] += 1
                report["details"].append({
                    "record_id": record_id,
                    "status": "verified"
                })
            else:
                report["corrupted"] += 1
                report["details"].append({
                    "record_id": record_id,
                    "status": "corrupted"
                })
        
        return report
    
    def verify_database(self) -> Dict[str, Any]:
        """
        Verify integrity of entire database.
        
        Returns:
            Complete verification report
        """
        cursor = self._conn.execute(
            """SELECT DISTINCT table_name FROM _integrity_redundancy"""
        )
        
        table_names = [row[0] for row in cursor]
        
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "database": str(self.db_path),
            "tables_verified": len(table_names),
            "summary": {
                "total_records": 0,
                "verified": 0,
                "corrupted": 0,
                "repaired": 0
            },
            "tables": []
        }
        
        for table_name in table_names:
            table_report = self.verify_table(table_name)
            report["tables"].append(table_report)
            
            report["summary"]["total_records"] += table_report["total_records"]
            report["summary"]["verified"] += table_report["verified"]
            report["summary"]["corrupted"] += table_report["corrupted"]
            report["summary"]["repaired"] += table_report["repaired"]
        
        return report
    
    def get_quarantine_report(self) -> List[Dict]:
        """
        Get list of quarantined records.
        
        Returns:
            List of quarantined record details
        """
        cursor = self._conn.execute(
            """SELECT * FROM _integrity_quarantine ORDER BY detected_at DESC"""
        )
        
        return [dict(row) for row in cursor]
    
    def cleanup_quarantine(self, older_than_days: int = 30) -> int:
        """
        Remove old quarantine records.
        
        Args:
            older_than_days: Remove records older than this
            
        Returns:
            Number of records removed
        """
        cursor = self._conn.execute(
            """DELETE FROM _integrity_quarantine 
               WHERE repaired = 1 
               AND datetime(repaired_at) < datetime('now', ?)""",
            (f'-{older_than_days} days',)
        )
        self._conn.commit()
        return cursor.rowcount
    
    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None


class PageChecksumManager:
    """
    Manage checksums for SQLite database pages.
    
    This provides low-level page integrity verification.
    """
    
    def __init__(self, db_path: str):
        """
        Initialize page checksum manager.
        
        Args:
            db_path: Path to database file
        """
        self.db_path = Path(db_path)
        self._page_checksums: Dict[int, str] = {}
    
    def compute_all_page_checksums(self) -> Dict[int, str]:
        """
        Compute checksums for all database pages.
        
        Returns:
            Dictionary mapping page numbers to checksums
        """
        # Read entire database file
        with open(self.db_path, 'rb') as f:
            data = f.read()
        
        # SQLite page size (default 4096 bytes)
        page_size = 4096
        
        # Compute checksum for each page
        checksums = {}
        page_num = 0
        
        for i in range(0, len(data), page_size):
            page_data = data[i:i + page_size]
            checksum = hashlib.sha256(page_data).hexdigest()
            checksums[page_num] = checksum
            page_num += 1
        
        self._page_checksums = checksums
        return checksums
    
    def verify_all_pages(self) -> Tuple[bool, List[int]]:
        """
        Verify all page checksums.
        
        Returns:
            Tuple of (all_valid, list_of_corrupted_page_numbers)
        """
        if not self._page_checksums:
            self.compute_all_page_checksums()
        
        # Read current data
        with open(self.db_path, 'rb') as f:
            data = f.read()
        
        page_size = 4096
        corrupted = []
        
        for page_num, expected_checksum in self._page_checksums.items():
            i = page_num * page_size
            page_data = data[i:i + page_size]
            actual_checksum = hashlib.sha256(page_data).hexdigest()
            
            if actual_checksum != expected_checksum:
                corrupted.append(page_num)
        
        return (len(corrupted) == 0, corrupted)
    
    def save_checksums(self, checksum_path: Optional[str] = None) -> str:
        """
        Save checksums to file.
        
        Args:
            checksum_path: Optional path (default: <db_path>.checksums)
            
        Returns:
            Path to checksum file
        """
        if not self._page_checksums:
            self.compute_all_page_checksums()
        
        if checksum_path is None:
            checksum_path = str(self.db_path) + ".checksums"
        
        with open(checksum_path, 'w') as f:
            json.dump(self._page_checksums, f, indent=2)
        
        return checksum_path
    
    def load_checksums(self, checksum_path: Optional[str] = None) -> Dict[int, str]:
        """
        Load checksums from file.
        
        Args:
            checksum_path: Optional path (default: <db_path>.checksums)
            
        Returns:
            Dictionary of page checksums
        """
        if checksum_path is None:
            checksum_path = str(self.db_path) + ".checksums"
        
        with open(checksum_path, 'r') as f:
            self._page_checksums = json.load(f)
        
        return self._page_checksums


class DatabaseBackupManager:
    """
    Automatic backup manager for ULE databases.
    
    Creates and manages redundant backup copies.
    """
    
    def __init__(self, db_path: str, backup_dir: Optional[str] = None):
        """
        Initialize backup manager.
        
        Args:
            db_path: Path to database file
            backup_dir: Directory for backups (default: <db_path>.backups)
        """
        self.db_path = Path(db_path)
        self.backup_dir = Path(backup_dir or f"{db_path}.backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self) -> str:
        """
        Create a new backup copy.
        
        Returns:
            Path to backup file
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"backup_{timestamp}.udb"
        
        shutil.copy2(str(self.db_path), str(backup_path))
        
        # Also save checksums
        checksum_manager = PageChecksumManager(str(self.db_path))
        checksum_manager.compute_all_page_checksums()
        checksum_manager.save_checksums(str(backup_path) + ".checksums")
        
        return str(backup_path)
    
    def restore_from_backup(self, backup_path: str) -> bool:
        """
        Restore database from backup.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            True if restore successful
        """
        backup = Path(backup_path)
        
        if not backup.exists():
            return False
        
        # Verify backup checksums if available
        checksum_path = str(backup) + ".checksums"
        if Path(checksum_path).exists():
            checksum_manager = PageChecksumManager(str(backup_path))
            checksum_manager.load_checksums(checksum_path)
            
            is_valid, corrupted = checksum_manager.verify_all_pages()
            if not is_valid:
                raise ValueError(
                    f"Backup corrupted: {len(corrupted)} pages failed verification"
                )
        
        # Restore
        shutil.copy2(str(backup), str(self.db_path))
        return True
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """
        List all available backups.
        
        Returns:
            List of backup details
        """
        backups = []
        
        for backup_file in sorted(self.backup_dir.glob("backup_*.udb")):
            stat = backup_file.stat()
            backups.append({
                "path": str(backup_file),
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        
        return backups
    
    def cleanup_old_backups(self, keep_count: int = 10) -> int:
        """
        Remove old backups, keeping only the most recent.
        
        Args:
            keep_count: Number of backups to keep
            
        Returns:
            Number of backups removed
        """
        backups = self.list_backups()
        
        if len(backups) <= keep_count:
            return 0
        
        removed = 0
        for backup in backups[:-keep_count]:
            backup_path = Path(backup["path"])
            backup_path.unlink(missing_ok=True)
            
            checksum_path = str(backup_path) + ".checksums"
            Path(checksum_path).unlink(missing_ok=True)
            
            removed += 1
        
        return removed
