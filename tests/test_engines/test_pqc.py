"""Tests for PQC engine."""

import pytest
from ule.engines.pqc_engine import PQCEngine

class TestPQCEngine:
    """Test Post-Quantum Cryptography engine operations."""
    
    def test_kem_keys(self):
        """Test ML-KEM key generation."""
        engine = PQCEngine()
        result = engine.generate_kem_keys(security_level=2)
        
        assert "public_key" in result
        assert "secret_key" in result
        assert result["algorithm"] == "ML-KEM-SIM"
        assert result["security_level"] == 2

    def test_encapsulate_decapsulate(self):
        """Test KEM flow."""
        engine = PQCEngine()
        keys = engine.generate_kem_keys()
        pk = keys["public_key"].encode()
        sk = keys["secret_key"].encode()
        
        ciphertext, shared_secret_enc = engine.kem.encapsulate(pk)
        shared_secret_dec = engine.kem.decapsulate(ciphertext, sk)
        
        assert shared_secret_enc == shared_secret_dec
        assert len(shared_secret_enc) == 32

    def test_signature_flow(self):
        """Test ML-DSA signing and verification."""
        engine = PQCEngine()
        keys = engine.generate_signature_keys()
        vk = keys["verification_key"]
        sk = keys["signing_key"]
        
        message = "Post-quantum security is mandatory."
        sig_result = engine.sign(message, sk)
        signature = sig_result["signature"]
        
        # Verify valid signature
        is_valid = engine.verify(message, signature, vk)
        assert is_valid is True
        
        # Verify invalid message
        assert engine.verify("Tampered message", signature, vk) is False

    def test_hybrid_encryption(self):
        """Test Hybrid encryption flow."""
        engine = PQCEngine()
        plaintext = "Confidential financial records."
        
        encrypted = engine.hybrid_encrypt(plaintext)
        assert "ciphertext" in encrypted
        assert "pq_ciphertext" in encrypted
        
        # Test decryption (simulation always returns a fixed value for now)
        decrypted = engine.hybrid.decrypt(encrypted, encrypted["pq_secret_key"].encode())
        assert decrypted == b"decrypted_data_simulation"

    def test_database_integration(self, temp_db):
        """Test integration via ULEDatabase property."""
        assert hasattr(temp_db, "pqc")
        stats = temp_db.pqc.get_stats()
        assert stats["engine"] == "PQCEngine"
        assert "ML-KEM (Kyber)" in stats["pqc_standards"]
