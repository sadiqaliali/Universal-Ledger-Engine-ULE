"""Tests for encryption."""

import pytest
from ule.security.encryption import AESCipher


class TestAESCipher:
    """Test AES encryption/decryption."""
    
    def test_encrypt_decrypt(self):
        """Test basic encrypt/decrypt."""
        cipher = AESCipher(password="test_password")
        
        plaintext = "Hello, World!"
        ciphertext = cipher.encrypt(plaintext)
        decrypted = cipher.decrypt(ciphertext)
        
        assert decrypted == plaintext
    
    def test_encrypt_bytes(self):
        """Test bytes encryption."""
        cipher = AESCipher(password="test")
        
        data = b"Binary data \x00\x01\x02"
        encrypted = cipher.encrypt_bytes(data)
        decrypted = cipher.decrypt_bytes(encrypted)
        
        assert decrypted == data
    
    def test_different_passwords(self):
        """Test different passwords produce different ciphertexts."""
        cipher1 = AESCipher(password="pass1")
        cipher2 = AESCipher(password="pass2")
        
        text = "Same text"
        
        enc1 = cipher1.encrypt(text)
        enc2 = cipher2.encrypt(text)
        
        assert enc1 != enc2
    
    def test_decrypt_with_wrong_password(self):
        """Test decryption with wrong password fails."""
        cipher1 = AESCipher(password="pass1")
        cipher2 = AESCipher(password="pass2")
        
        ciphertext = cipher1.encrypt("secret")
        
        with pytest.raises(Exception):
            cipher2.decrypt(ciphertext)
