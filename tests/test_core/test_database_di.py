import pytest
from unittest.mock import MagicMock
from ule.core.database import ULEDatabase
from ule.core.interfaces import ICipher, IAuditManager, IHashChain

def test_ule_database_with_mocked_dependencies():
    """Verify ULEDatabase accepts injected mock dependencies."""
    # 1. Create mocks for interfaces
    mock_cipher = MagicMock(spec=ICipher)
    mock_audit = MagicMock(spec=IAuditManager)
    mock_hash = MagicMock(spec=IHashChain)
    
    # 2. Inject into ULEDatabase
    # We use a path that doesn't exist but since we are mocking init/open
    # this is safe. For a real unit test we should refactor _connect to also be mockable.
    # For now, this proves the __init__ and dependency assignment works.
    db = ULEDatabase(
        db_path="mock_db.udb",
        cipher=mock_cipher,
        hash_chain=mock_hash,
        audit_manager=mock_audit
    )
    
    # 3. Assert dependencies were injected correctly
    assert db._cipher == mock_cipher
    assert db._audit_manager == mock_audit
    assert db._hash_chain == mock_hash

    print("\nSuccessfully verified Dependency Injection in ULEDatabase.")
