"""Tests for Natural Language Query - Arabic."""

import pytest
from ule.ai.nlq import NaturalLanguageQuery


class TestNLQArabic:
    """Test Arabic NLQ patterns."""

    def test_show_all(self, temp_db):
        """Test 'show all' pattern."""
        temp_db.execute("CREATE TABLE users (id INT, name TEXT)")
        temp_db.execute("INSERT INTO users VALUES (1, 'Ali')")

        nlq = NaturalLanguageQuery(temp_db._conn)
        results = nlq.ask("اعرض جميع المستخدمين", language="ar")

        assert len(results) == 1

    def test_show_with_age_condition(self, temp_db):
        """Test age condition pattern."""
        temp_db.execute("CREATE TABLE users (id INT, name TEXT, age INT)")
        temp_db.execute("INSERT INTO users VALUES (1, 'Ali', 25)")
        temp_db.execute("INSERT INTO users VALUES (2, 'Sara', 30)")

        nlq = NaturalLanguageQuery(temp_db._conn)
        results = nlq.ask("اعرض المستخدمين الذين تزيد أعمارهم عن 26", language="ar")

        assert len(results) == 1
        assert results[0]["name"] == "Sara"

    def test_count(self, temp_db):
        """Test count pattern."""
        temp_db.execute("CREATE TABLE users (id INT, name TEXT)")
        temp_db.execute("INSERT INTO users VALUES (1, 'Ali')")
        temp_db.execute("INSERT INTO users VALUES (2, 'Sara')")

        nlq = NaturalLanguageQuery(temp_db._conn)
        results = nlq.ask("كم users", language="ar")

        assert len(results) == 1
        assert list(results[0].values())[0] == 2

    def test_translate(self, temp_db):
        """Test SQL translation."""
        nlq = NaturalLanguageQuery(temp_db._conn)

        sql = nlq.translate("اعرض جميع users", language="ar")

        assert sql is not None
        assert "SELECT" in sql.upper()
        assert "users" in sql.lower()
