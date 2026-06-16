"""Tests for Natural Language Query - Urdu."""

import pytest
from ule.ai.nlq import NaturalLanguageQuery


class TestNLQUrdu:
    """Test Urdu NLQ patterns."""
    
    def test_show_all(self, temp_db):
        """Test 'show all' pattern in Urdu."""
        temp_db.execute("CREATE TABLE users (id INT, name TEXT)")
        temp_db.execute("INSERT INTO users VALUES (1, 'Ali')")
        
        nlq = NaturalLanguageQuery(temp_db._conn)
        results = nlq.ask("تمام users دکھائیں", language="ur")
        
        assert len(results) == 1
    
    def test_show_with_age_condition(self, temp_db):
        """Test age condition in Urdu."""
        temp_db.execute("CREATE TABLE users (id INT, name TEXT, age INT)")
        temp_db.execute("INSERT INTO users VALUES (1, 'Ali', 25)")
        temp_db.execute("INSERT INTO users VALUES (2, 'Sara', 30)")
        
        nlq = NaturalLanguageQuery(temp_db._conn)
        results = nlq.ask("users دکھائیں جن کی عمر 26 سے زیادہ ہے", language="ur")
        
        assert len(results) == 1
        assert results[0]["name"] == "Sara"
    
    def test_count(self, temp_db):
        """Test count in Urdu."""
        temp_db.execute("CREATE TABLE users (id INT, name TEXT)")
        temp_db.execute("INSERT INTO users VALUES (1, 'Ali')")
        temp_db.execute("INSERT INTO users VALUES (2, 'Sara')")
        
        nlq = NaturalLanguageQuery(temp_db._conn)
        results = nlq.ask("کل users گنیں", language="ur")
        
        assert len(results) == 1
    
    def test_translate(self, temp_db):
        """Test Urdu SQL translation."""
        nlq = NaturalLanguageQuery(temp_db._conn)
        
        sql = nlq.translate("تمام users دکھائیں", language="ur")
        
        assert sql is not None
        assert "SELECT" in sql.upper()
