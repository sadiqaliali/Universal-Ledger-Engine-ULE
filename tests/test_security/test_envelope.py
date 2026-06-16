"""Tests for Envelope Encryption in ULE."""

import pytest
from ule.core.database import ULEDatabase
from ule.core.exceptions import AuthenticationError

def test_envelope_encryption_persistence(tmp_path):
    """Test that encrypted data persists and is decryptable after re-opening."""
    db_path = tmp_path / "envelope.udb"
    password = "strong_password"
    
    # 1. Create and initialize encrypted DB
    with ULEDatabase(str(db_path), password=password) as db:
        db.push("secrets", {"key": "secret_value"})
        results = db.find("secrets")
        assert results[0]["key"] == "secret_value"
    
    # 2. Re-open with correct password
    with ULEDatabase(str(db_path), password=password) as db:
        results = db.find("secrets")
        assert len(results) == 1
        assert results[0]["key"] == "secret_value"

def test_envelope_encryption_invalid_password(tmp_path):
    """Test that re-opening with wrong password fails."""
    db_path = tmp_path / "envelope_fail.udb"
    password = "correct_password"
    
    with ULEDatabase(str(db_path), password=password) as db:
        db.push("secrets", {"key": "value"})
    
    # Re-open with WRONG password
    with pytest.raises(AuthenticationError):
        with ULEDatabase(str(db_path), password="wrong_password") as db:
            db.find("secrets")

def test_envelope_encryption_missing_password(tmp_path):
    """Test that re-opening encrypted DB without password fails."""
    db_path = tmp_path / "envelope_missing.udb"
    password = "some_password"
    
    with ULEDatabase(str(db_path), password=password) as db:
        db.push("data", {"foo": "bar"})
    
    # Re-open without password
    with pytest.raises(AuthenticationError, match="Password required"):
        with ULEDatabase(str(db_path)) as db:
            db.find("data")
