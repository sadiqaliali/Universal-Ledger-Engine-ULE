"""Connection handling for ULE."""

from pathlib import Path
from typing import Optional
from ule.core.database import ULEDatabase


def connect(db_path: str, password: Optional[str] = None,
            create_if_missing: bool = False) -> ULEDatabase:
    """
    Connect to a ULE database.
    
    Args:
        db_path: Path to .udb file
        password: Optional encryption password
        create_if_missing: Create database if it doesn't exist
    
    Returns:
        ULEDatabase connection
    """
    db = ULEDatabase(db_path)
    
    if create_if_missing and not Path(db_path).exists():
        db.init(password)
    else:
        db.open(password)
    
    return db
