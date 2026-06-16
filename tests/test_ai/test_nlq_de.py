"""Tests for NLQ German."""

import pytest
import sqlite3
import tempfile
import os
from ule.ai.nlq import NaturalLanguageQuery


class TestNLQGerman:
    """Test German NLQ functionality."""

    @pytest.fixture
    def nlq(self):
        """Create test database with NLQ."""
        fd, db_path = tempfile.mkstemp(suffix='.udb')
        os.close(fd)
        
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
        conn.execute("INSERT INTO users VALUES (1, 'Hans', 30), (2, 'Anna', 25)")
        conn.commit()
        
        nlq = NaturalLanguageQuery(conn)
        yield nlq
        
        os.unlink(db_path)

    def test_show_all(self, nlq):
        """Test show all query."""
        sql = nlq.translate("zeige alle benutzer", "de")
        assert sql is not None
        assert "SELECT * FROM" in sql

    def test_show_with_age_condition(self, nlq):
        """Test show with age condition."""
        sql = nlq.translate("zeige benutzer mit alter größer als 20", "de")
        assert sql is not None
        assert "WHERE" in sql
        assert ">" in sql

    def test_count(self, nlq):
        """Test count query."""
        sql = nlq.translate("zähle benutzer", "de")
        assert sql is not None
        assert "COUNT" in sql.upper()

    def test_translate(self, nlq):
        """Test translation returns valid SQL."""
        sql = nlq.translate("zeige tabellen", "de")
        assert sql is not None
        assert "SELECT" in sql.upper()
