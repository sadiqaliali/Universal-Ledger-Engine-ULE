"""Tests for NLQ Polish."""

import pytest
import sqlite3
import tempfile
import os
from ule.ai.nlq import NaturalLanguageQuery


class TestNLQPolish:
    """Test Polish NLQ functionality."""

    @pytest.fixture
    def nlq(self):
        """Create test database with NLQ."""
        fd, db_path = tempfile.mkstemp(suffix='.udb')
        os.close(fd)
        
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE uzytkownicy (id INTEGER PRIMARY KEY, imie TEXT, wiek INTEGER)")
        conn.execute("INSERT INTO uzytkownicy VALUES (1, 'Jan', 30), (2, 'Anna', 25)")
        conn.commit()
        
        nlq = NaturalLanguageQuery(conn)
        yield nlq
        
        os.unlink(db_path)

    def test_show_all(self, nlq):
        """Test show all query."""
        sql = nlq.translate("pokaż wszystkich użytkowników", "pl")
        assert sql is not None
        assert "SELECT * FROM" in sql

    def test_show_with_age_condition(self, nlq):
        """Test show with age condition."""
        sql = nlq.translate("pokaż użytkowników z wiek większe niż 20", "pl")
        assert sql is not None
        assert "WHERE" in sql
        assert ">" in sql

    def test_count(self, nlq):
        """Test count query."""
        sql = nlq.translate("policz użytkowników", "pl")
        assert sql is not None
        assert "COUNT" in sql.upper()

    def test_translate(self, nlq):
        """Test translation returns valid SQL."""
        sql = nlq.translate("pokaż tabele", "pl")
        assert sql is not None
        assert "SELECT" in sql.upper()
