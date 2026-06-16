"""Integration tests for ULE."""

import pytest
from ule import connect
from ule.ai.nlq import NaturalLanguageQuery


class TestIntegration:
    """End-to-end integration tests."""
    
    def test_full_workflow(self, tmp_path):
        """Test complete workflow."""
        db_path = str(tmp_path / "test.udb")
        
        # Connect
        db = connect(db_path, create_if_missing=True)
        
        # SQL
        db.execute("CREATE TABLE users (id INT, name TEXT, age INT)")
        db.execute("INSERT INTO users VALUES (1, 'Ali', 25)")
        db.execute("INSERT INTO users VALUES (2, 'Sara', 30)")
        
        # Documents
        db.push("logs", {"level": "info", "msg": "Started"})
        
        # Graph
        db.link("users", "1", "users", "2", "FRIEND")
        
        # Verify
        assert db.verify() is True
        
        # Query
        results = db.select("users", where="age > ?", params=(26,))
        assert len(results) == 1
        assert results[0]["name"] == "Sara"
        
        # Documents
        docs = db.find("logs")
        assert len(docs) == 1
        
        # Graph
        edges = db.traverse("users", "1")
        assert len(edges) == 1
        
        db.close()
    
    def test_multilingual_queries(self, temp_db):
        """Test queries in multiple languages."""
        temp_db.execute("CREATE TABLE users (id INT, name TEXT, age INT)")
        temp_db.execute("INSERT INTO users VALUES (1, 'Ali', 25)")
        temp_db.execute("INSERT INTO users VALUES (2, 'Sara', 30)")
        
        nlq = NaturalLanguageQuery(temp_db._conn)
        
        # English
        en_results = nlq.ask("show all users older than 26", language="en")
        assert len(en_results) == 1
        
        # Urdu
        ur_results = nlq.ask("users دکھائیں جن کی عمر 26 سے زیادہ ہے", language="ur")
        assert len(ur_results) == 1
        
        # Chinese
        zh_results = nlq.ask("显示 26 岁以上的 users", language="zh")
        assert len(zh_results) == 1
