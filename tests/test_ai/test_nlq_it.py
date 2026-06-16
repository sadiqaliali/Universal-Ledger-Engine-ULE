"""Tests for NLQ Italian."""

import pytest
import sqlite3
import tempfile
import os
from ule.ai.nlq import NaturalLanguageQuery


class TestNLQItalian:
    """Test Italian NLQ functionality."""

    @pytest.fixture
    def nlq(self):
        """Create test database with NLQ."""
        fd, db_path = tempfile.mkstemp(suffix='.udb')
        os.close(fd)
        
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE utenti (id INTEGER PRIMARY KEY, nome TEXT, eta INTEGER)")
        conn.execute("INSERT INTO utenti VALUES (1, 'Marco', 30), (2, 'Giulia', 25)")
        conn.commit()
        
        nlq = NaturalLanguageQuery(conn)
        yield nlq
        
        os.unlink(db_path)

    def test_show_all(self, nlq):
        """Test show all query."""
        sql = nlq.translate("mostra tutti gli utenti", "it")
        assert sql is not None
        assert "SELECT * FROM" in sql

    def test_show_with_age_condition(self, nlq):
        """Test show with age condition."""
        sql = nlq.translate("mostra utenti con eta maggiore di 20", "it")
        assert sql is not None
        assert "WHERE" in sql
        assert ">" in sql

    def test_count(self, nlq):
        """Test count query."""
        sql = nlq.translate("conta utenti", "it")
        assert sql is not None
        assert "COUNT" in sql.upper()

    def test_translate(self, nlq):
        """Test translation returns valid SQL."""
        sql = nlq.translate("mostra tabelle", "it")
        assert sql is not None
        assert "SELECT" in sql.upper()
