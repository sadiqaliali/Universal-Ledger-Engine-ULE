"""Tests for NoSQL document engine."""

import pytest
from ule.engines.nosql_engine import NoSQL_Engine as NoSQLEngine


class TestNoSQLEngine:
    """Test NoSQL engine operations."""
    
    def test_push(self, temp_db):
        """Test document push."""
        engine = NoSQLEngine(temp_db._conn)
        
        doc_id = engine.push("logs", {"level": "info", "msg": "Test"})
        
        assert doc_id is not None
    
    def test_find_all(self, temp_db):
        """Test find all documents."""
        engine = NoSQLEngine(temp_db._conn)
        engine.push("logs", {"level": "info", "msg": "Test 1"})
        engine.push("logs", {"level": "error", "msg": "Test 2"})
        
        results = engine.find("logs")
        
        assert len(results) == 2
    
    def test_find_with_query(self, temp_db):
        """Test find with filter."""
        engine = NoSQLEngine(temp_db._conn)
        engine.push("logs", {"level": "info", "msg": "Test 1"})
        engine.push("logs", {"level": "error", "msg": "Test 2"})
        
        results = engine.find("logs", query={"level": "info"})
        
        assert len(results) == 1
        assert results[0]["level"] == "info"
    
    def test_find_with_gt_operator(self, temp_db):
        """Test find with $gt operator."""
        engine = NoSQLEngine(temp_db._conn)
        engine.push("products", {"name": "A", "price": 10})
        engine.push("products", {"name": "B", "price": 20})
        engine.push("products", {"name": "C", "price": 30})
        
        results = engine.find("products", query={"price": {"$gt": 15}})
        
        assert len(results) == 2
    
    def test_find_with_lt_operator(self, temp_db):
        """Test find with $lt operator."""
        engine = NoSQLEngine(temp_db._conn)
        engine.push("products", {"name": "A", "price": 10})
        engine.push("products", {"name": "B", "price": 20})
        
        results = engine.find("products", query={"price": {"$lt": 15}})
        
        assert len(results) == 1
    
    def test_find_with_in_operator(self, temp_db):
        """Test find with $in operator."""
        engine = NoSQLEngine(temp_db._conn)
        engine.push("users", {"name": "Ali", "city": "Lahore"})
        engine.push("users", {"name": "Sara", "city": "Karachi"})
        engine.push("users", {"name": "Ahmed", "city": "Islamabad"})
        
        results = engine.find(
            "users", 
            query={"city": {"$in": ["Lahore", "Karachi"]}}
        )
        
        assert len(results) == 2
    
    def test_update(self, temp_db):
        """Test document update."""
        engine = NoSQLEngine(temp_db._conn)
        engine.push("users", {"name": "Ali", "age": 25})
        
        engine.update(
            "users",
            query={"name": "Ali"},
            update={"$set": {"age": 26}}
        )
        
        results = engine.find("users", query={"name": "Ali"})
        assert results[0]["age"] == 26
    
    def test_delete(self, temp_db):
        """Test document delete."""
        engine = NoSQLEngine(temp_db._conn)
        engine.push("logs", {"level": "info", "msg": "Test 1"})
        engine.push("logs", {"level": "error", "msg": "Test 2"})
        
        count = engine.delete("logs", query={"level": "error"})
        
        assert count == 1
        
        results = engine.find("logs")
        assert len(results) == 1
    
    def test_count(self, temp_db):
        """Test document count."""
        engine = NoSQLEngine(temp_db._conn)
        engine.push("logs", {"level": "info"})
        engine.push("logs", {"level": "error"})
        
        count = engine.count("logs")
        
        assert count == 2
    
    def test_find_one(self, temp_db):
        """Test find single document."""
        engine = NoSQLEngine(temp_db._conn)
        engine.push("users", {"name": "Ali", "age": 25})
        
        doc = engine.find_one("users")
        
        assert doc is not None
        assert doc["name"] == "Ali"
    
    def test_nested_query(self, temp_db):
        """Test nested field query."""
        engine = NoSQLEngine(temp_db._conn)
        engine.push("users", {"name": "Ali", "address": {"city": "Lahore"}})
        engine.push("users", {"name": "Sara", "address": {"city": "Karachi"}})
        
        results = engine.find("users", query={"address.city": "Lahore"})
        
        assert len(results) == 1
