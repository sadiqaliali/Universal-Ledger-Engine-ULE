"""AES-256-GCM encryption for ULE."""

import os
import base64
from typing import Optional, Tuple, Union
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend


class AESCipher:
    """AES-256-GCM encryption/decryption."""
    
    KEY_SIZE = 32  # 256 bits
    NONCE_SIZE = 12
    SALT_SIZE = 16
    
    def __init__(self, password: str = None, key: bytes = None, salt: bytes = None):
        """
        Initialize cipher with password or key.
        
        Args:
            password: Password for key derivation
            key: Direct encryption key (32 bytes)
            salt: Salt for key derivation
        """
        if password:
            self.salt = salt or os.urandom(self.SALT_SIZE)
            self.key = self._derive_key(password, self.salt)
        elif key:
            if len(key) != self.KEY_SIZE:
                raise ValueError("Key must be 32 bytes")
            self.key = key
            self.salt = None
        else:
            raise ValueError("Either password or key must be provided")
        
        self.aesgcm = AESGCM(self.key)
    
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive 256-bit key from password using PBKDF2."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.KEY_SIZE,
            salt=salt,
            iterations=100_000,
            backend=default_backend()
        )
        return kdf.derive(password.encode())
    
    def encrypt(self, plaintext: str) -> bytes:
        """
        Encrypt plaintext string.
        
        Returns:
            Encrypted data (nonce + ciphertext + tag)
        """
        nonce = os.urandom(self.NONCE_SIZE)
        ciphertext = self.aesgcm.encrypt(nonce, plaintext.encode(), None)
        
        # Prepend salt if available, then nonce
        result = self.salt + nonce + ciphertext if self.salt else nonce + ciphertext
        return base64.b64encode(result)
    
    def decrypt(self, ciphertext: bytes) -> str:
        """
        Decrypt ciphertext.
        
        Args:
            ciphertext: Encrypted data (base64 encoded)
        
        Returns:
            Decrypted plaintext string
        """
        data = base64.b64decode(ciphertext)
        
        # Extract salt, nonce, and ciphertext
        if self.salt:
            # data structure: salt (SALT_SIZE) + nonce (NONCE_SIZE) + encrypted_data
            nonce_start = self.SALT_SIZE
            nonce_end = nonce_start + self.NONCE_SIZE
            nonce = data[nonce_start:nonce_end]
            encrypted = data[nonce_end:]
        else:
            nonce = data[:self.NONCE_SIZE]
            encrypted = data[self.NONCE_SIZE:]
        
        plaintext = self.aesgcm.decrypt(nonce, encrypted, None)
        return plaintext.decode()
    
    def encrypt_bytes(self, data: bytes) -> bytes:
        """Encrypt raw bytes."""
        nonce = os.urandom(self.NONCE_SIZE)
        ciphertext = self.aesgcm.encrypt(nonce, data, None)
        result = (self.salt + nonce + ciphertext) if self.salt else (nonce + ciphertext)
        return base64.b64encode(result)
    
    def decrypt_bytes(self, ciphertext: bytes) -> bytes:
        """Decrypt raw bytes."""
        data = base64.b64decode(ciphertext)
        
        # If salt was used, it is at the beginning, followed by nonce, then encrypted data
        if self.salt:
            # data structure: salt (SALT_SIZE) + nonce (NONCE_SIZE) + encrypted_data
            nonce_start = self.SALT_SIZE
            nonce_end = nonce_start + self.NONCE_SIZE
            nonce = data[nonce_start:nonce_end]
            encrypted = data[nonce_end:]
        else:
            nonce = data[:self.NONCE_SIZE]
            encrypted = data[self.NONCE_SIZE:]
        
        return self.aesgcm.decrypt(nonce, encrypted, None)


class EnvelopeEncryption:
    """
    Envelope encryption (Master Key vs. Data Key).
    
    The Data Key (DK) is used to encrypt actual data.
    The Master Key (MK) is derived from a password and used to encrypt the DK.
    """
    
    def __init__(self, password: str):
        self.password = password
        self.mk_cipher = AESCipher(password=password)
        self.dk: Optional[bytes] = None
    
    def generate_data_key(self) -> Tuple[bytes, bytes]:
        """
        Generate a new random Data Key and its encrypted version.
        
        Returns:
            Tuple of (data_key, encrypted_data_key)
        """
        self.dk = os.urandom(32)
        encrypted_dk = self.mk_cipher.encrypt_bytes(self.dk)
        return self.dk, encrypted_dk
    
    def load_data_key(self, encrypted_dk: bytes, mk_salt: bytes) -> bytes:
        """
        Decrypt and load the Data Key using the Master Key.
        
        Args:
            encrypted_dk: Encrypted Data Key (base64)
            mk_salt: Salt used to derive the Master Key
            
        Returns:
            Decrypted data_key
        """
        # Re-derive MK with the original salt
        self.mk_cipher = AESCipher(password=self.password, salt=mk_salt)
        self.dk = self.mk_cipher.decrypt_bytes(encrypted_dk)
        return self.dk
    
    def get_cipher(self) -> AESCipher:
        """Get AESCipher initialized with the Data Key."""
        if self.dk is None:
            raise ValueError("Data Key not loaded or generated")
        return AESCipher(key=self.dk)
