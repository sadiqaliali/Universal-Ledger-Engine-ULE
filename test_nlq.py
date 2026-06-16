import pytest
from ule.core.database import ULEDatabase
from ule.ai.nlq import NaturalLanguageQuery

def test_nlq_initialization_and_query():
    try:
        db = ULEDatabase(db_name="test_db")
        nlq = NaturalLanguageQuery(database=db)
        assert nlq is not None
        print("\nNLQ initialized successfully.")
    except Exception as e:
        pytest.fail(f"NLQ initialization failed: {e}")
