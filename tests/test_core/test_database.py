"""Tests for core database functionality."""

import pytest
from ule.core.database import ULEDatabase
from ule.core.connection import connect
from ule.core.exceptions import DatabaseError


class TestULEDatabase:
    """Test ULEDatabase class."""
    
    def test_init(self, temp_db):
        """Test database initialization."""
        assert temp_db._initialized is True
    
    def test_create_table(self, temp_db):
        """Test table creation."""
        temp_db.create_table("products", {
            "id": "INTEGER",
            "name": "TEXT",
            "price": "REAL"
        })
        
        results = temp_db.execute("SELECT * FROM products")
        assert results is not None
    
    def test_insert(self, temp_db):
        """Test row insertion."""
        temp_db.create_table("users", {"id": "INTEGER", "name": "TEXT"})
        row_id = temp_db.insert("users", {"id": 1, "name": "Ali"})

        assert row_id > 0  # Row ID should be positive
    
    def test_select(self, temp_db):
        """Test SELECT query."""
        temp_db.create_table("users", {"id": "INTEGER", "name": "TEXT"})
        temp_db.insert("users", {"id": 1, "name": "Ali"})
        temp_db.insert("users", {"id": 2, "name": "Sara"})
        
        results = temp_db.select("users")
        
        assert len(results) == 2
        assert results[0]["name"] == "Ali"
    
    def test_select_with_where(self, temp_db):
        """Test SELECT with WHERE clause."""
        temp_db.create_table("users", {"id": "INTEGER", "name": "TEXT", "age": "INTEGER"})
        temp_db.insert("users", {"id": 1, "name": "Ali", "age": 25})
        temp_db.insert("users", {"id": 2, "name": "Sara", "age": 30})
        
        results = temp_db.select("users", where="age > ?", params=(25,))
        
        assert len(results) == 1
        assert results[0]["name"] == "Sara"
    
    def test_push_document(self, temp_db):
        """Test document push."""
        doc_id = temp_db.push("logs", {"level": "info", "msg": "Test"})
        
        assert doc_id is not None
    
    def test_find_documents(self, temp_db):
        """Test document find."""
        temp_db.push("logs", {"level": "info", "msg": "Test 1"})
        temp_db.push("logs", {"level": "error", "msg": "Test 2"})
        
        results = temp_db.find("logs")
        
        assert len(results) == 2
    
    def test_find_with_query(self, temp_db):
        """Test document find with filter."""
        temp_db.push("logs", {"level": "info", "msg": "Test 1"})
        temp_db.push("logs", {"level": "error", "msg": "Test 2"})
        
        results = temp_db.find("logs", query={"level": "info"})
        
        assert len(results) == 1
        assert results[0]["level"] == "info"
    
    def test_link_nodes(self, temp_db):
        """Test graph linking."""
        temp_db.link("users", "1", "orders", "99", "PURCHASED")
        
        results = temp_db.traverse("users", "1")
        
        assert len(results) == 1
        assert results[0]["to"] == "orders:99"
    
    def test_traverse_graph(self, temp_db):
        """Test graph traversal."""
        temp_db.link("users", "1", "users", "2", "FRIEND")
        temp_db.link("users", "2", "users", "3", "FRIEND")
        
        results = temp_db.traverse("users", "1", depth=2)
        
        assert len(results) >= 1
    
    def test_verify_chain(self, temp_db):
        """Test chain verification."""
        is_valid = temp_db.verify()
        
        assert is_valid is True
    
    def test_audit_trail(self, temp_db):
        """Test audit trail."""
        temp_db.create_table("test", {"id": "INTEGER"})
        
        results = temp_db.audit()
        
        assert len(results) > 0
    
    def test_close(self, temp_db):
        """Test database close."""
        temp_db.close()
        
        assert temp_db._conn is None
    
    def test_context_manager(self, temp_db):
        """Test context manager."""
        with ULEDatabase(temp_db.db_path) as db:
            assert db._initialized is True


class TestConnect:
    """Test connect function."""
    
    def test_connect_create(self, tmp_path):
        """Test connect with create_if_missing."""
        db_path = str(tmp_path / "test.udb")
        
        db = connect(db_path, create_if_missing=True)
        
        assert db._initialized is True
        db.close()
    
    def test_connect_open(self, temp_db):
        """Test connect to existing database."""
        temp_db.close()
        
        db = connect(temp_db.db_path)
        
        assert db._initialized is True
        db.close()
