"""Tests for hash chain."""

import pytest
from ule.blockchain.hash_chain import HashChain


class TestHashChain:
    """Test blockchain hash chain."""
    
    def test_init(self, temp_db):
        """Test chain initialization."""
        chain = HashChain(temp_db._conn)
        chain.init()
        
        assert chain.latest_hash is not None
    
    def test_add_block(self, temp_db):
        """Test adding blocks."""
        chain = HashChain(temp_db._conn)
        chain.init()
        
        prev_hash = chain.latest_hash
        
        new_hash = chain.add({"operation": "TEST", "data": "test1"})
        
        assert new_hash != prev_hash
        assert len(new_hash) == 64  # SHA-256 hex
    
    def test_verify_chain(self, temp_db):
        """Test chain verification."""
        chain = HashChain(temp_db._conn)
        chain.init()
        
        chain.add({"operation": "TEST", "data": "test1"})
        chain.add({"operation": "TEST", "data": "test2"})
        
        is_valid = chain.verify()
        
        assert is_valid is True
    
    def test_get_chain(self, temp_db):
        """Test getting chain."""
        chain = HashChain(temp_db._conn)
        chain.init()
        
        chain.add({"operation": "INSERT", "table": "users"})
        chain.add({"operation": "UPDATE", "table": "users"})
        
        blocks = chain.get_chain(limit=10)
        
        assert len(blocks) >= 2
