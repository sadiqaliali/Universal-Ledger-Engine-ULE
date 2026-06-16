from typing import Dict, Optional
from ule.core.database import ULEDatabase

class ConnectionManager:
    """
    Manages active database connections to ensure encapsulation 
    and thread-safe access.
    """
    def __init__(self):
        self._active_dbs: Dict[str, ULEDatabase] = {}

    def add_connection(self, path: str, db: ULEDatabase):
        """Register a new active connection."""
        self._active_dbs[path] = db

    def get_connection(self, path: str) -> Optional[ULEDatabase]:
        """Retrieve an existing connection."""
        return self._active_dbs.get(path)

    def close_connection(self, path: str):
        """Gracefully close and remove a connection."""
        if path in self._active_dbs:
            self._active_dbs[path].close()
            del self._active_dbs[path]

    def has_connection(self, path: str) -> bool:
        """Check if a path has an active connection."""
        return path in self._active_dbs

# Singleton manager for the application
# In a later step, this can be injected via FastAPI's dependency system
connection_manager = ConnectionManager()
