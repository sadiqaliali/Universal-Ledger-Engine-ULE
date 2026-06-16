"""Benchmark utility for ULE."""

import time
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Any
import numpy as np
from ule.core.database import ULEDatabase

class ULEBenchmark:
    """Benchmark suite for ULE performance testing."""
    
    def __init__(self, iterations: int = 100):
        self.iterations = iterations
        self.results = {}

    def run_all(self):
        """Run all benchmarks."""
        print(f"🚀 Starting ULE Benchmarks ({self.iterations} iterations)...")
        
        self.benchmark_sql_writes()
        self.benchmark_sql_reads()
        self.benchmark_document_ops()
        self.benchmark_encryption_overhead()
        self.benchmark_blockchain_overhead()
        
        self.report()

    def benchmark_sql_writes(self):
        """Benchmark SQL INSERT performance."""
        fd, db_path = tempfile.mkstemp(suffix='.udb')
        os.close(fd)
        Path(db_path).unlink()
        
        with ULEDatabase(db_path) as db:
            db.create_table("bench", {"id": "INTEGER", "val": "TEXT"})
            
            start = time.perf_counter()
            for i in range(self.iterations):
                db.insert("bench", {"id": i, "val": f"value_{i}"})
            end = time.perf_counter()
            
            self.results['sql_insert_sec'] = (end - start) / self.iterations
        
        Path(db_path).unlink()

    def benchmark_sql_reads(self):
        """Benchmark SQL SELECT performance."""
        fd, db_path = tempfile.mkstemp(suffix='.udb')
        os.close(fd)
        Path(db_path).unlink()
        
        with ULEDatabase(db_path) as db:
            db.create_table("bench", {"id": "INTEGER", "val": "TEXT"})
            for i in range(self.iterations):
                db.insert("bench", {"id": i, "val": f"value_{i}"})
            
            start = time.perf_counter()
            for i in range(self.iterations):
                db.execute("SELECT * FROM bench WHERE id = ?", (i,))
            end = time.perf_counter()
            
            self.results['sql_select_sec'] = (end - start) / self.iterations
            
        Path(db_path).unlink()

    def benchmark_document_ops(self):
        """Benchmark NoSQL document PUSH/FIND performance."""
        fd, db_path = tempfile.mkstemp(suffix='.udb')
        os.close(fd)
        Path(db_path).unlink()
        
        with ULEDatabase(db_path) as db:
            start_push = time.perf_counter()
            for i in range(self.iterations):
                db.push("docs", {"id": i, "data": "x" * 100, "i": i})
            end_push = time.perf_counter()
            
            start_find = time.perf_counter()
            for i in range(self.iterations):
                db.find("docs", query={"id": i})
            end_find = time.perf_counter()
            
            self.results['doc_push_sec'] = (end_push - start_push) / self.iterations
            self.results['doc_find_sec'] = (end_find - start_find) / self.iterations
            
        Path(db_path).unlink()

    def benchmark_encryption_overhead(self):
        """Benchmark overhead of Envelope Encryption."""
        fd1, db_path_plain = tempfile.mkstemp(suffix='.udb')
        os.close(fd1)
        fd2, db_path_enc = tempfile.mkstemp(suffix='.udb')
        os.close(fd2)
        Path(db_path_plain).unlink()
        Path(db_path_enc).unlink()
        
        # Plain
        with ULEDatabase(db_path_plain) as db:
            start = time.perf_counter()
            for i in range(self.iterations):
                db.push("bench", {"data": "test", "i": i})
            self.results['push_plain_sec'] = (time.perf_counter() - start) / self.iterations
            
        # Encrypted
        with ULEDatabase(db_path_enc, password="test") as db:
            start = time.perf_counter()
            for i in range(self.iterations):
                db.push("bench", {"data": "test", "i": i})
            self.results['push_encrypted_sec'] = (time.perf_counter() - start) / self.iterations
            
        Path(db_path_plain).unlink()
        Path(db_path_enc).unlink()

    def benchmark_blockchain_overhead(self):
        """Benchmark overhead of Blockchain Audit Trail."""
        fd1, db_path_off = tempfile.mkstemp(suffix='.udb')
        os.close(fd1)
        fd2, db_path_on = tempfile.mkstemp(suffix='.udb')
        os.close(fd2)
        Path(db_path_off).unlink()
        Path(db_path_on).unlink()
        
        from ule.core.config import Config
        
        # Audit OFF
        cfg_off = Config()
        cfg_off.set("blockchain_enabled", False)
        with ULEDatabase(db_path_off, config=cfg_off) as db:
            db.create_table("t", {"id": "INT"})
            start = time.perf_counter()
            for i in range(self.iterations):
                db.insert("t", {"id": i})
            self.results['insert_audit_off_sec'] = (time.perf_counter() - start) / self.iterations
            
        # Audit ON
        cfg_on = Config()
        cfg_on.set("blockchain_enabled", True)
        with ULEDatabase(db_path_on, config=cfg_on) as db:
            db.create_table("t", {"id": "INT"})
            start = time.perf_counter()
            for i in range(self.iterations):
                db.insert("t", {"id": i})
            self.results['insert_audit_on_sec'] = (time.perf_counter() - start) / self.iterations
            
        Path(db_path_off).unlink()
        Path(db_path_on).unlink()

    def report(self):
        """Print benchmark report."""
        print("\n📊 --- ULE Performance Report ---")
        print(f"{'Operation':<30} | {'Latency (ms)':<15}")
        print("-" * 50)
        for key, val in self.results.items():
            print(f"{key:<30} | {val*1000:>12.4f} ms")
        
        overhead_enc = (self.results['push_encrypted_sec'] / self.results['push_plain_sec'] - 1) * 100
        overhead_audit = (self.results['insert_audit_on_sec'] / self.results['insert_audit_off_sec'] - 1) * 100
        
        print(f"\n🔒 Encryption Overhead: {overhead_enc:.2f}%")
        print(f"🔗 Blockchain Audit Overhead: {overhead_audit:.2f}%")

if __name__ == "__main__":
    bench = ULEBenchmark(iterations=500)
    bench.run_all()
