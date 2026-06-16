"""Tests for NLQ Swedish."""

import pytest
import sqlite3
import tempfile
import os
from ule.ai.nlq import NaturalLanguageQuery


class TestNLQSwedish:
    """Test Swedish NLQ functionality."""

    @pytest.fixture
    def nlq(self):
        """Create test database with NLQ."""
        fd, db_path = tempfile.mkstemp(suffix='.udb')
        os.close(fd)
        
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE anvandare (id INTEGER PRIMARY KEY, namn TEXT, alder INTEGER)")
        conn.execute("INSERT INTO anvandare VALUES (1, 'Erik', 30), (2, 'Anna', 25)")
        conn.commit()
        
        nlq = NaturalLanguageQuery(conn)
        yield nlq
        
        os.unlink(db_path)

    def test_show_all(self, nlq):
        """Test show all query."""
        sql = nlq.translate("visa alla användare", "sv")
        assert sql is not None
        assert "SELECT * FROM" in sql

    def test_show_with_age_condition(self, nlq):
        """Test show with age condition."""
        sql = nlq.translate("visa användare med ålder större än 20", "sv")
        assert sql is not None
        assert "WHERE" in sql
        assert ">" in sql

    def test_count(self, nlq):
        """Test count query."""
        sql = nlq.translate("räkna användare", "sv")
        assert sql is not None
        assert "COUNT" in sql.upper()

    def test_translate(self, nlq):
        """Test translation returns valid SQL."""
        sql = nlq.translate("visa tabeller", "sv")
        assert sql is not None
        assert "SELECT" in sql.upper()
