"""RSA/Ed25519 key management for ULE."""

import os
from pathlib import Path
from typing import Optional, Tuple
from cryptography.hazmat.primitives.asymmetric import rsa, ed25519
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend


class KeyManager:
    """Manage RSA and Ed25519 key pairs."""
    
    def __init__(self, key_dir: str = None):
        self.key_dir = Path(key_dir) if key_dir else Path.home() / ".ule" / "keys"
        self.key_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_rsa(self, user: str, key_size: int = 4096) -> Tuple[str, str]:
        """
        Generate RSA key pair.
        
        Returns:
            Tuple of (private_key_path, public_key_path)
        """
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=default_backend()
        )
        
        # Save private key
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        private_path = self.key_dir / f"{user}_rsa_private.pem"
        with open(private_path, 'wb') as f:
            f.write(private_pem)
        
        # Save public key
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        public_path = self.key_dir / f"{user}_rsa_public.pem"
        with open(public_path, 'wb') as f:
            f.write(public_pem)
        
        os.chmod(private_path, 0o600)
        
        return str(private_path), str(public_path)
    
    def generate_ed25519(self, user: str) -> Tuple[str, str]:
        """
        Generate Ed25519 key pair.
        
        Returns:
            Tuple of (private_key_path, public_key_path)
        """
        private_key = ed25519.Ed25519PrivateKey.generate()
        
        # Save private key
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        private_path = self.key_dir / f"{user}_ed25519_private.pem"
        with open(private_path, 'wb') as f:
            f.write(private_pem)
        
        # Save public key
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        public_path = self.key_dir / f"{user}_ed25519_public.pem"
        with open(public_path, 'wb') as f:
            f.write(public_pem)
        
        os.chmod(private_path, 0o600)
        
        return str(private_path), str(public_path)
    
    def load_private_key(self, path: str):
        """Load private key from file."""
        with open(path, 'rb') as f:
            key = serialization.load_pem_private_key(
                f.read(),
                password=None,
                backend=default_backend()
            )
        return key
    
    def load_public_key(self, path: str):
        """Load public key from file."""
        with open(path, 'rb') as f:
            key = serialization.load_pem_public_key(
                f.read(),
                backend=default_backend()
            )
        return key
    
    def get_public_key(self, user: str, key_type: str = "ed25519") -> Optional[str]:
        """Get public key as string."""
        public_path = self.key_dir / f"{user}_{key_type}_public.pem"
        if public_path.exists():
            with open(public_path, 'rb') as f:
                return f.read().decode()
        return None
    
    def list_keys(self) -> list:
        """List all key files."""
        return [f.name for f in self.key_dir.glob("*.pem")]
