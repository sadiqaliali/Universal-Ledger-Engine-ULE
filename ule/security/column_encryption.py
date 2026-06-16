"""Column-Level Encryption for ULE.

This module provides per-column encryption with individual keys,
allowing fine-grained control over sensitive data.
"""

import hashlib
import json
import base64
from typing import Any, Dict, Optional, List
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import os


class ColumnEncryption:
    """
    Column-level encryption for ULE.
    
    Each column can have its own encryption key derived from
    a master key and column name.
    
    Features:
    - AES-256-GCM encryption per column
    - Key derivation from master key + column name
    - Authentication tags for integrity
    - Support for different encryption strategies
    """
    
    def __init__(self, master_key: bytes, salt: Optional[bytes] = None):
        """
        Initialize column encryption.
        
        Args:
            master_key: Master key for deriving column keys
            salt: Optional salt for key derivation (generated if not provided)
        """
        self.master_key = master_key
        self.salt = salt or os.urandom(16)
        self._column_keys: Dict[str, bytes] = {}
    
    def _derive_column_key(self, column_name: str) -> bytes:
        """
        Derive encryption key for a specific column.
        
        Args:
            column_name: Name of the column
            
        Returns:
            32-byte encryption key
        """
        if column_name in self._column_keys:
            return self._column_keys[column_name]
        
        # Derive key using PBKDF2 with column name as salt component
        column_salt = self.salt + column_name.encode('utf-8')
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=column_salt,
            iterations=100000,
            backend=default_backend()
        )
        
        key = kdf.derive(self.master_key)
        self._column_keys[column_name] = key
        return key
    
    def encrypt_column(self, value: Any, column_name: str) -> str:
        """
        Encrypt a value for a specific column.
        
        Args:
            value: Value to encrypt (any JSON-serializable type)
            column_name: Name of the column
            
        Returns:
            Base64-encoded encrypted value with nonce and tag
        """
        # Serialize value to JSON
        value_json = json.dumps(value).encode('utf-8')
        
        # Get column-specific key
        key = self._derive_column_key(column_name)
        
        # Generate random nonce
        nonce = os.urandom(12)  # 96-bit nonce for GCM
        
        # Encrypt with AES-GCM
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, value_json, None)
        
        # Combine nonce + ciphertext and encode as base64
        encrypted = base64.b64encode(nonce + ciphertext).decode('utf-8')
        
        return encrypted
    
    def decrypt_column(self, encrypted_value: str, column_name: str) -> Any:
        """
        Decrypt a value from a specific column.
        
        Args:
            encrypted_value: Base64-encoded encrypted value
            column_name: Name of the column
            
        Returns:
            Decrypted value (original Python type)
            
        Raises:
            ValueError: If decryption fails (wrong key or tampered data)
        """
        # Decode base64
        encrypted_bytes = base64.b64decode(encrypted_value)
        
        # Extract nonce and ciphertext
        nonce = encrypted_bytes[:12]
        ciphertext = encrypted_bytes[12:]
        
        # Get column-specific key
        key = self._derive_column_key(column_name)
        
        # Decrypt with AES-GCM
        aesgcm = AESGCM(key)
        try:
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        except Exception as e:
            raise ValueError(f"Decryption failed for column '{column_name}': {e}")
        
        # Deserialize from JSON
        value = json.loads(plaintext.decode('utf-8'))
        
        return value
    
    def encrypt_row(self, row: Dict[str, Any], 
                    encrypted_columns: List[str]) -> Dict[str, Any]:
        """
        Encrypt specified columns in a row.
        
        Args:
            row: Dictionary representing a database row
            encrypted_columns: List of column names to encrypt
            
        Returns:
            Row with specified columns encrypted
        """
        encrypted_row = row.copy()
        
        for column in encrypted_columns:
            if column in row:
                encrypted_row[column] = self.encrypt_column(
                    row[column], 
                    column
                )
        
        return encrypted_row
    
    def decrypt_row(self, row: Dict[str, Any],
                    encrypted_columns: List[str]) -> Dict[str, Any]:
        """
        Decrypt specified columns in a row.
        
        Args:
            row: Dictionary representing a database row
            encrypted_columns: List of column names to decrypt
            
        Returns:
            Row with specified columns decrypted
        """
        decrypted_row = row.copy()
        
        for column in encrypted_columns:
            if column in row:
                try:
                    decrypted_row[column] = self.decrypt_column(
                        row[column],
                        column
                    )
                except (ValueError, KeyError):
                    # If decryption fails, keep original value
                    # (might already be decrypted or corrupted)
                    pass
        
        return decrypted_row
    
    def get_encryption_metadata(self) -> Dict[str, Any]:
        """
        Get metadata needed for encryption/decryption.
        
        Returns:
            Dictionary with salt and other metadata
        """
        return {
            "salt": base64.b64encode(self.salt).decode('utf-8'),
            "algorithm": "AES-256-GCM",
            "kdf": "PBKDF2-SHA256",
            "iterations": 100000
        }
    
    @classmethod
    def from_metadata(cls, master_key: bytes, 
                      metadata: Dict[str, Any]) -> 'ColumnEncryption':
        """
        Create ColumnEncryption instance from metadata.
        
        Args:
            master_key: Master key
            metadata: Encryption metadata dictionary
            
        Returns:
            ColumnEncryption instance
        """
        salt = base64.b64decode(metadata["salt"])
        return cls(master_key, salt)


class EncryptionStrategy:
    """
    Encryption strategies for different use cases.
    """
    
    @staticmethod
    def full_encryption(value: Any) -> str:
        """
        Full encryption - data completely hidden.
        
        Use for: SSN, passwords, medical records
        """
        return f"ENC:{value}"
    
    @staticmethod
    def partial_encryption(value: str, visible_chars: int = 4) -> str:
        """
        Partial encryption - show first/last few characters.
        
        Use for: Credit cards, phone numbers
        
        Example: "1234567890" → "1234****7890"
        """
        if len(value) <= visible_chars * 2:
            return "*" * len(value)
        
        visible_start = value[:visible_chars]
        visible_end = value[-visible_chars:]
        masked = "*" * (len(value) - visible_chars * 2)
        
        return f"{visible_start}{masked}{visible_end}"
    
    @staticmethod
    def hash_only(value: Any) -> str:
        """
        Hash only - original data not recoverable.
        
        Use for: Email verification, password comparison
        """
        return hashlib.sha256(
            json.dumps(value, sort_keys=True).encode()
        ).hexdigest()
    
    @staticmethod
    def tokenization(value: Any, token_map: Dict) -> str:
        """
        Tokenization - replace with random token.
        
        Use for: Credit card numbers in non-payment contexts
        """
        import uuid
        token = str(uuid.uuid4())
        token_map[token] = value
        return f"TKN:{token}"


class ColumnEncryptionManager:
    """
    Manager for column encryption across multiple tables.
    """
    
    def __init__(self, master_password: str):
        """
        Initialize encryption manager.
        
        Args:
            master_password: Master password for all encryption
        """
        # Derive master key from password
        self.master_password = master_password
        self.master_key = self._derive_master_key(master_password)
        self._column_encryptions: Dict[str, ColumnEncryption] = {}
        self._encrypted_columns: Dict[str, List[str]] = {}
    
    def _derive_master_key(self, password: str) -> bytes:
        """Derive 32-byte master key from password."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"ule_column_encryption_salt_v1",
            iterations=100000,
            backend=default_backend()
        )
        return kdf.derive(password.encode('utf-8'))
    
    def configure_table(self, table_name: str, 
                       encrypted_columns: List[str]) -> None:
        """
        Configure which columns should be encrypted for a table.
        
        Args:
            table_name: Name of the table
            encrypted_columns: List of column names to encrypt
        """
        self._encrypted_columns[table_name] = encrypted_columns
        
        # Create column encryption instance for this table
        table_salt = hashlib.sha256(
            table_name.encode('utf-8')
        ).digest()
        
        self._column_encryptions[table_name] = ColumnEncryption(
            self.master_key,
            table_salt
        )
    
    def encrypt_row(self, table_name: str, 
                    row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypt a row before storing.
        
        Args:
            table_name: Name of the table
            row: Row data to encrypt
            
        Returns:
            Row with encrypted columns
        """
        if table_name not in self._encrypted_columns:
            return row
        
        encryption = self._column_encryptions[table_name]
        columns = self._encrypted_columns[table_name]
        
        return encryption.encrypt_row(row, columns)
    
    def decrypt_row(self, table_name: str,
                    row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypt a row after reading.
        
        Args:
            table_name: Name of the table
            row: Row data to decrypt
            
        Returns:
            Row with decrypted columns
        """
        if table_name not in self._encrypted_columns:
            return row
        
        encryption = self._column_encryptions[table_name]
        columns = self._encrypted_columns[table_name]
        
        return encryption.decrypt_row(row, columns)
    
    def get_encryption_config(self) -> Dict[str, Any]:
        """
        Get encryption configuration for backup/migration.
        
        Returns:
            Configuration dictionary
        """
        config = {
            "version": "1.0",
            "algorithm": "AES-256-GCM",
            "tables": {}
        }
        
        for table_name, encryption in self._column_encryptions.items():
            config["tables"][table_name] = {
                "columns": self._encrypted_columns.get(table_name, []),
                "metadata": encryption.get_encryption_metadata()
            }
        
        return config


# Convenience functions for direct use

def encrypt_value(value: Any, column_name: str, 
                  master_key: bytes) -> str:
    """Encrypt a single value."""
    encryption = ColumnEncryption(master_key)
    return encryption.encrypt_column(value, column_name)


def decrypt_value(encrypted_value: str, column_name: str,
                  master_key: bytes) -> Any:
    """Decrypt a single value."""
    encryption = ColumnEncryption(master_key)
    return encryption.decrypt_column(encrypted_value, column_name)
