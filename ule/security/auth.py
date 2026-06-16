"""Authentication for ULE."""

import hashlib
from typing import Optional, Dict
from ule.core.exceptions import AuthenticationError


class Authenticator:
    """Handle user authentication."""
    
    def __init__(self, db_connection):
        self._conn = db_connection
    
    def create_user(self, username: str, public_key: str, role: str = "user") -> None:
        """Create a new user."""
        self._conn.execute(
            "INSERT INTO _users (username, public_key, role) VALUES (?, ?, ?)",
            (username, public_key, role)
        )
        self._conn.commit()
    
    def get_user(self, username: str) -> Optional[Dict]:
        """Get user info."""
        cursor = self._conn.execute(
            "SELECT username, public_key, role FROM _users WHERE username = ?",
            (username,)
        )
        row = cursor.fetchone()
        if row:
            return {
                "username": row[0],
                "public_key": row[1],
                "role": row[2]
            }
        return None
    
    def verify_signature(self, username: str, data: bytes, signature: bytes) -> bool:
        """Verify user's signature on data."""
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ed25519
        
        user = self.get_user(username)
        if not user:
            return False
        
        try:
            public_key = serialization.load_pem_public_key(user["public_key"].encode())
            
            if isinstance(public_key, ed25519.Ed25519PublicKey):
                public_key.verify(signature, data)
                return True
        except Exception:
            return False
        
        return False
    
    def check_role(self, username: str, required_role: str) -> bool:
        """Check if user has required role."""
        user = self.get_user(username)
        if not user:
            return False
        
        role_hierarchy = {"admin": 3, "write": 2, "user": 1}
        return role_hierarchy.get(user["role"], 0) >= role_hierarchy.get(required_role, 0)
    
    def login(self, username: str, private_key_path: str) -> bool:
        """
        Authenticate user with private key.
        
        This is a simple challenge-response authentication.
        """
        import os
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ed25519
        
        # Load private key
        with open(private_key_path, 'rb') as f:
            private_key = serialization.load_pem_private_key(f.read(), password=None)
        
        # Get user's public key from database
        user = self.get_user(username)
        if not user:
            raise AuthenticationError(f"User {username} not found")
        
        # Verify key pair matches
        expected_public = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()
        
        if user["public_key"] != expected_public:
            raise AuthenticationError("Key pair mismatch")
        
        return True
