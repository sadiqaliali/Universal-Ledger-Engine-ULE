"""Tests for Natural Language Query - Chinese."""

import pytest
from ule.ai.nlq import NaturalLanguageQuery


class TestNLQChinese:
    """Test Chinese NLQ patterns."""
    
    def test_show_all(self, temp_db):
        """Test 'show all' pattern in Chinese."""
        temp_db.execute("CREATE TABLE users (id INT, name TEXT)")
        temp_db.execute("INSERT INTO users VALUES (1, 'Ali')")
        
        nlq = NaturalLanguageQuery(temp_db._conn)
        results = nlq.ask("显示所有 users", language="zh")
        
        assert len(results) == 1
    
    def test_show_with_age_condition(self, temp_db):
        """Test age condition in Chinese."""
        temp_db.execute("CREATE TABLE users (id INT, name TEXT, age INT)")
        temp_db.execute("INSERT INTO users VALUES (1, 'Ali', 25)")
        temp_db.execute("INSERT INTO users VALUES (2, 'Sara', 30)")
        
        nlq = NaturalLanguageQuery(temp_db._conn)
        results = nlq.ask("显示 26 岁以上的 users", language="zh")
        
        assert len(results) == 1
        assert results[0]["name"] == "Sara"
    
    def test_translate(self, temp_db):
        """Test Chinese SQL translation."""
        nlq = NaturalLanguageQuery(temp_db._conn)
        
        sql = nlq.translate("显示所有 users", language="zh")
        
        assert sql is not None
        assert "SELECT" in sql.upper()
