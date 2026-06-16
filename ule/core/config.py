"""Configuration management for ULE."""

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional


class Config:
    """Database configuration."""
    
    DEFAULT_PAGE_SIZE = 4096
    DEFAULT_BUFFER_SIZE = 100
    DEFAULT_ENCRYPTION = True
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self._config: Dict[str, Any] = {
            "page_size": self.DEFAULT_PAGE_SIZE,
            "buffer_size": self.DEFAULT_BUFFER_SIZE,
            "encryption": self.DEFAULT_ENCRYPTION,
            "wal_enabled": False,
            "blockchain_enabled": True,
            "blockchain_sync": False, # If True, flushes are synchronous
        }
        if config_path and os.path.exists(config_path):
            self.load(config_path)
    
    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        self._config[key] = value
    
    def load(self, path: str) -> None:
        with open(path, 'r') as f:
            self._config.update(json.load(f))
    
    def save(self, path: str) -> None:
        with open(path, 'w') as f:
            json.dump(self._config, f, indent=2)
    
    @property
    def page_size(self) -> int:
        return self._config["page_size"]
    
    @property
    def encryption_enabled(self) -> bool:
        return self._config.get("encryption", True)
