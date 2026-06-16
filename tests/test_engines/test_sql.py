"""Tests for SQL engine."""

import pytest
from ule.engines.sql_engine import SQLEngine


class TestSQLEngine:
    """Test SQL engine operations."""
    
    def test_create_table(self, temp_db):
        """Test CREATE TABLE."""
        engine = SQLEngine(temp_db._conn)
        engine.create_table("products", {
            "id": "INTEGER",
            "name": "TEXT",
            "price": "REAL"
        })
        
        tables = engine.get_tables()
        assert "products" in tables
    
    def test_insert_row(self, temp_db):
        """Test INSERT."""
        engine = SQLEngine(temp_db._conn)
        engine.create_table("users", {"id": "INTEGER", "name": "TEXT"})
        
        row_id = engine.insert_row("users", {"id": 1, "name": "Ali"})
        
        assert row_id == 1
    
    def test_select_rows(self, temp_db):
        """Test SELECT."""
        engine = SQLEngine(temp_db._conn)
        engine.create_table("users", {"id": "INTEGER", "name": "TEXT"})
        engine.insert_row("users", {"id": 1, "name": "Ali"})
        engine.insert_row("users", {"id": 2, "name": "Sara"})
        
        results = engine.select_rows("users")
        
        assert len(results) == 2
    
    def test_select_with_where(self, temp_db):
        """Test SELECT with WHERE."""
        engine = SQLEngine(temp_db._conn)
        engine.create_table("users", {"id": "INTEGER", "name": "TEXT", "age": "INTEGER"})
        engine.insert_row("users", {"id": 1, "name": "Ali", "age": 25})
        engine.insert_row("users", {"id": 2, "name": "Sara", "age": 30})
        
        results = engine.select_rows(
            "users", 
            where="age > ?", 
            params=(25,)
        )
        
        assert len(results) == 1
        assert results[0]["name"] == "Sara"
    
    def test_update_rows(self, temp_db):
        """Test UPDATE."""
        engine = SQLEngine(temp_db._conn)
        engine.create_table("users", {"id": "INTEGER", "name": "TEXT"})
        engine.insert_row("users", {"id": 1, "name": "Ali"})
        
        count = engine.update_rows(
            "users",
            {"name": "Ahmed"},
            where="id = ?",
            params=(1,)
        )
        
        assert count == 1
        
        results = engine.select_rows("users")
        assert results[0]["name"] == "Ahmed"
    
    def test_delete_rows(self, temp_db):
        """Test DELETE."""
        engine = SQLEngine(temp_db._conn)
        engine.create_table("users", {"id": "INTEGER", "name": "TEXT"})
        engine.insert_row("users", {"id": 1, "name": "Ali"})
        engine.insert_row("users", {"id": 2, "name": "Sara"})
        
        count = engine.delete_rows("users", where="id = ?", params=(1,))
        
        assert count == 1
        
        results = engine.select_rows("users")
        assert len(results) == 1
    
    def test_count(self, temp_db):
        """Test COUNT."""
        engine = SQLEngine(temp_db._conn)
        engine.create_table("users", {"id": "INTEGER", "name": "TEXT"})
        engine.insert_row("users", {"id": 1, "name": "Ali"})
        engine.insert_row("users", {"id": 2, "name": "Sara"})
        
        count = engine.count("users")
        
        assert count == 2
    
    def test_exists(self, temp_db):
        """Test EXISTS."""
        engine = SQLEngine(temp_db._conn)
        engine.create_table("users", {"id": "INTEGER", "name": "TEXT"})
        engine.insert_row("users", {"id": 1, "name": "Ali"})
        
        exists = engine.exists("users", where="id = ?", params=(1,))
        not_exists = engine.exists("users", where="id = ?", params=(99,))
        
        assert exists is True
        assert not_exists is False
    
    def test_drop_table(self, temp_db):
        """Test DROP TABLE."""
        engine = SQLEngine(temp_db._conn)
        engine.create_table("test", {"id": "INTEGER"})
        engine.drop_table("test")
        
        tables = engine.get_tables()
        assert "test" not in tables
    
    def test_get_schema(self, temp_db):
        """Test schema introspection."""
        engine = SQLEngine(temp_db._conn)
        engine.create_table("users", {
            "id": "INTEGER",
            "name": "TEXT NOT NULL",
            "age": "INTEGER DEFAULT 0"
        })
        
        schema = engine.get_schema("users")
        
        assert len(schema) == 3
        assert schema[0]["name"] == "id"
        assert schema[1]["name"] == "name"
