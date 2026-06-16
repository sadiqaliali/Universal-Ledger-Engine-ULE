import pytest
import shutil
import tempfile
import time
from pathlib import Path
from ule.core.database import ULEDatabase

@pytest.fixture
def temp_db():
    """Create a completely isolated database for every single test."""
    # Use a unique name per test based on unique ID
    db_name = f"test_{pytest.id() if hasattr(pytest, 'id') else time.time()}.udb"
    db_path = Path(db_name)
    
    db = ULEDatabase(str(db_path))
    db.init()
    
    yield db
    
    db.close()
    if db_path.exists():
        db_path.unlink()
    # Cleanup any WAL/keys/snapshot files
    for f in Path(".").glob(f"{db_path.stem}*"):
        if f.is_file():
            f.unlink(missing_ok=True)
        elif f.is_dir():
            shutil.rmtree(f, ignore_errors=True)

@pytest.fixture
def sample_data(temp_db):
    """Populate with exact, deterministic data."""
    # Ensure tables don't exist yet to avoid pollution
    try:
        temp_db.execute("DROP TABLE IF EXISTS users")
    except:
        pass
        
    temp_db.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
    temp_db.execute("INSERT INTO users VALUES (1, 'Ali', 25)")
    return temp_db
