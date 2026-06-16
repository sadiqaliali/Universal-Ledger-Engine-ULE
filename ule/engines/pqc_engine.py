"""
PQCEngine: Post-Quantum Cryptography Engine for ULE.
Exposes NIST-standard PQC primitives via a unified API.
"""

import time
from typing import Dict, Any, Tuple, Optional
from ule.security.pqc import MLKEM_Simulation, Dilithium_Simulation, HybridCrypto

class PQCEngine:
    """
    Engine for managing Post-Quantum Cryptographic operations.
    Supports KEM (Key Encapsulation) and DSA (Digital Signatures).
    """

    def __init__(self):
        self.kem = MLKEM_Simulation()
        self.dsa = Dilithium_Simulation()
        self.hybrid = HybridCrypto()

    def generate_kem_keys(self, security_level: int = 2) -> Dict[str, Any]:
        """Generate ML-KEM key pair."""
        start = time.perf_counter()
        # Use specific level if requested
        kem = MLKEM_Simulation(security_level) if security_level != self.kem.security_level else self.kem
        pk, sk = kem.keygen()
        
        return {
            "public_key": pk.decode(),
            "secret_key": sk.decode(),
            "algorithm": "ML-KEM-SIM",
            "security_level": security_level,
            "elapsed_ms": (time.perf_counter() - start) * 1000
        }

    def generate_signature_keys(self, security_level: int = 2) -> Dict[str, Any]:
        """Generate ML-DSA key pair."""
        start = time.perf_counter()
        dsa = Dilithium_Simulation(security_level)
        vk, sk = dsa.keygen()
        
        return {
            "verification_key": vk.decode(),
            "signing_key": sk.decode(),
            "algorithm": "ML-DSA-SIM",
            "security_level": security_level,
            "elapsed_ms": (time.perf_counter() - start) * 1000
        }

    def sign(self, message: str, signing_key: str) -> Dict[str, Any]:
        """Sign a message string."""
        start = time.perf_counter()
        sig = self.dsa.sign(message.encode(), signing_key.encode())
        
        return {
            "signature": sig.decode(),
            "message": message,
            "elapsed_ms": (time.perf_counter() - start) * 1000
        }

    def verify(self, message: str, signature: str, verification_key: str) -> bool:
        """Verify a signature."""
        return self.dsa.verify(message.encode(), signature.encode(), verification_key.encode())

    def hybrid_encrypt(self, plaintext: str) -> Dict[str, Any]:
        """Encrypt using hybrid (Classical + PQC) approach."""
        return self.hybrid.encrypt(plaintext.encode())

    def get_stats(self) -> Dict[str, Any]:
        """Return engine metadata."""
        return {
            "engine": "PQCEngine",
            "pqc_standards": ["ML-KEM (Kyber)", "ML-DSA (Dilithium)"],
            "status": "Hardened Simulation",
            "provider": "ULE Native",
            "liboqs_detected": False
        }
