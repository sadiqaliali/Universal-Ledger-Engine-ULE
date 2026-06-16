"""Digital Signatures for ULE.

This module provides digital signature functionality using RSA and Ed25519,
allowing users to sign transactions for non-repudiation and authenticity.
"""

import hashlib
import json
import base64
from typing import Any, Dict, Optional, Tuple
from datetime import datetime
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, ed25519, padding
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature
import os


class DigitalSignature:
    """
    Digital signature handler for ULE transactions.
    
    Supports:
    - RSA-4096 (widely compatible, court-admissible)
    - Ed25519 (faster, smaller signatures)
    
    Use cases:
    - Legal contracts (non-repudiation)
    - Medical orders (doctor's signature)
    - Financial approvals (CFO signature)
    - Audit trail verification
    """
    
    def __init__(self, key_type: str = "ed25519"):
        """
        Initialize digital signature handler.
        
        Args:
            key_type: "ed25519" (fast) or "rsa" (compatible)
        """
        self.key_type = key_type
        self._private_key = None
        self._public_key = None
        
        if key_type == "rsa":
            self._key_size = 4096
        elif key_type == "ed25519":
            self._key_size = 256
        else:
            raise ValueError(f"Unsupported key type: {key_type}")
    
    def generate_keypair(self) -> Tuple[bytes, bytes]:
        """
        Generate a new key pair.
        
        Returns:
            Tuple of (private_key_pem, public_key_pem)
        """
        if self.key_type == "rsa":
            # Generate RSA key pair
            self._private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=self._key_size,
                backend=default_backend()
            )
            self._public_key = self._private_key.public_key()
            
            # Serialize to PEM format
            private_pem = self._private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            public_pem = self._public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
        elif self.key_type == "ed25519":
            # Generate Ed25519 key pair
            self._private_key = ed25519.Ed25519PrivateKey.generate()
            self._public_key = self._private_key.public_key()
            
            # Serialize to PEM format
            private_pem = self._private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            public_pem = self._public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
        
        return private_pem, public_pem
    
    def load_private_key(self, private_key_pem: bytes) -> None:
        """
        Load existing private key.
        
        Args:
            private_key_pem: PEM-encoded private key
        """
        if self.key_type == "rsa":
            self._private_key = serialization.load_pem_private_key(
                private_key_pem,
                password=None,
                backend=default_backend()
            )
        elif self.key_type == "ed25519":
            self._private_key = serialization.load_pem_private_key(
                private_key_pem,
                password=None,
                backend=default_backend()
            )
    
    def load_public_key(self, public_key_pem: bytes) -> None:
        """
        Load existing public key.
        
        Args:
            public_key_pem: PEM-encoded public key
        """
        if self.key_type == "rsa":
            self._public_key = serialization.load_pem_public_key(
                public_key_pem,
                backend=default_backend()
            )
        elif self.key_type == "ed25519":
            self._public_key = serialization.load_pem_public_key(
                public_key_pem,
                backend=default_backend()
            )
    
    def sign(self, data: Any, timestamp: Optional[str] = None) -> Dict[str, str]:
        """
        Sign data with private key.
        
        Args:
            data: Data to sign (any JSON-serializable type)
            timestamp: Optional timestamp (auto-generated if not provided)
            
        Returns:
            Dictionary with data, signature, and metadata
        """
        if self._private_key is None:
            raise ValueError("Private key not loaded")
        
        # Serialize data
        data_json = json.dumps(data, sort_keys=True).encode('utf-8')
        
        # Compute hash
        data_hash = hashlib.sha256(data_json).hexdigest()
        
        # Generate timestamp
        if timestamp is None:
            timestamp = datetime.utcnow().isoformat() + "Z"
        
        # Sign the hash
        if self.key_type == "rsa":
            signature = self._private_key.sign(
                data_json,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
        elif self.key_type == "ed25519":
            signature = self._private_key.sign(data_json)
        
        # Encode signature
        signature_b64 = base64.b64encode(signature).decode('utf-8')
        
        return {
            "data": data,
            "data_hash": data_hash,
            "signature": signature_b64,
            "timestamp": timestamp,
            "key_type": self.key_type,
            "algorithm": "RSA-PSS" if self.key_type == "rsa" else "Ed25519"
        }
    
    def verify(self, signed_data: Dict[str, Any], 
               public_key_pem: Optional[bytes] = None) -> bool:
        """
        Verify a signature.
        
        Args:
            signed_data: Dictionary from sign() method
            public_key_pem: Optional public key (uses loaded key if not provided)
            
        Returns:
            True if signature is valid, False otherwise
        """
        # Get public key
        if public_key_pem:
            if self.key_type == "rsa":
                public_key = serialization.load_pem_public_key(
                    public_key_pem,
                    backend=default_backend()
                )
            elif self.key_type == "ed25519":
                public_key = serialization.load_pem_public_key(
                    public_key_pem,
                    backend=default_backend()
                )
        else:
            public_key = self._public_key
        
        if public_key is None:
            raise ValueError("Public key not available")
        
        # Extract data and signature
        data = signed_data["data"]
        signature_b64 = signed_data["signature"]
        signature = base64.b64decode(signature_b64)
        
        # Serialize data
        data_json = json.dumps(data, sort_keys=True).encode('utf-8')
        
        # Verify signature
        try:
            if self.key_type == "rsa":
                public_key.verify(
                    signature,
                    data_json,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    hashes.SHA256()
                )
            elif self.key_type == "ed25519":
                public_key.verify(signature, data_json)
            
            return True
        except InvalidSignature:
            return False
    
    def sign_transaction(self, operation: str, table_name: str,
                        record_id: Any, data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Sign a database transaction.
        
        Args:
            operation: "INSERT", "UPDATE", "DELETE"
            table_name: Name of the table
            record_id: ID of the record
            data: Optional data being written
            
        Returns:
            Signed transaction dictionary
        """
        transaction = {
            "operation": operation,
            "table": table_name,
            "record_id": record_id,
            "data": data,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        return self.sign(transaction)
    
    def get_public_key_info(self) -> Dict[str, Any]:
        """
        Get public key information.
        
        Returns:
            Dictionary with key details
        """
        if self._public_key is None:
            return {}
        
        public_pem = self._public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return {
            "key_type": self.key_type,
            "key_size": self._key_size,
            "public_key": public_pem.decode('utf-8'),
            "fingerprint": self._get_fingerprint()
        }
    
    def _get_fingerprint(self) -> str:
        """Generate key fingerprint (SHA256 hash of public key)."""
        if self._public_key is None:
            return ""
        
        public_bytes = self._public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return hashlib.sha256(public_bytes).hexdigest()[:16]


class SignatureVerifier:
    """
    Verify signatures without having private keys.
    
    Use case: Third-party auditors, regulators, courts
    """
    
    def __init__(self):
        self._stored_public_keys: Dict[str, bytes] = {}
    
    def register_public_key(self, user_id: str, 
                           public_key_pem: bytes) -> None:
        """
        Register a user's public key.
        
        Args:
            user_id: User identifier
            public_key_pem: PEM-encoded public key
        """
        self._stored_public_keys[user_id] = public_key_pem
    
    def verify_signed_data(self, signed_data: Dict[str, Any],
                          user_id: str) -> bool:
        """
        Verify data signed by a specific user.
        
        Args:
            signed_data: Signed data dictionary
            user_id: ID of the supposed signer
            
        Returns:
            True if signature is valid
        """
        if user_id not in self._stored_public_keys:
            raise ValueError(f"Public key not found for user: {user_id}")
        
        # Create temporary signature handler
        key_type = signed_data.get("key_type", "ed25519")
        verifier = DigitalSignature(key_type)
        verifier.load_public_key(self._stored_public_keys[user_id])
        
        return verifier.verify(signed_data)
    
    def verify_transaction_chain(self, transactions: list) -> Dict[str, Any]:
        """
        Verify a chain of transactions.
        
        Args:
            transactions: List of signed transactions
            
        Returns:
            Verification report
        """
        report = {
            "total": len(transactions),
            "valid": 0,
            "invalid": 0,
            "details": []
        }
        
        for tx in transactions:
            user_id = tx.get("user_id")
            if not user_id:
                report["details"].append({
                    "status": "invalid",
                    "reason": "No user_id"
                })
                report["invalid"] += 1
                continue
            
            try:
                is_valid = self.verify_signed_data(tx, user_id)
                if is_valid:
                    report["valid"] += 1
                    report["details"].append({
                        "status": "valid",
                        "user": user_id,
                        "timestamp": tx.get("timestamp")
                    })
                else:
                    report["invalid"] += 1
                    report["details"].append({
                        "status": "invalid",
                        "reason": "Signature mismatch",
                        "user": user_id
                    })
            except Exception as e:
                report["invalid"] += 1
                report["details"].append({
                    "status": "invalid",
                    "reason": str(e),
                    "user": user_id
                })
        
        return report


class TransactionSigner:
    """
    High-level transaction signing for ULE database.
    
    Integrates with ULEDatabase to sign all transactions.
    """
    
    def __init__(self, db_path: str, user_id: str,
                 private_key_pem: Optional[bytes] = None):
        """
        Initialize transaction signer.
        
        Args:
            db_path: Path to database
            user_id: User identifier
            private_key_pem: Optional private key (generated if not provided)
        """
        self.db_path = db_path
        self.user_id = user_id
        self.signature_handler = DigitalSignature(key_type="ed25519")
        
        if private_key_pem:
            self.signature_handler.load_private_key(private_key_pem)
        else:
            # Generate new key pair
            private_pem, public_pem = self.signature_handler.generate_keypair()
            self.signature_handler.load_private_key(private_pem)
    
    def sign_and_store(self, operation: str, table_name: str,
                       record_id: Any, data: Optional[Dict] = None) -> Dict:
        """
        Sign a transaction and prepare for storage.
        
        Args:
            operation: "INSERT", "UPDATE", "DELETE"
            table_name: Table name
            record_id: Record ID
            data: Optional data
            
        Returns:
            Signed transaction ready for storage
        """
        signed_tx = self.signature_handler.sign_transaction(
            operation, table_name, record_id, data
        )
        
        # Add user ID
        signed_tx["user_id"] = self.user_id
        
        return signed_tx
    
    def get_user_credentials(self) -> Dict[str, Any]:
        """
        Get user credentials for registration.
        
        Returns:
            Dictionary with user ID and public key
        """
        key_info = self.signature_handler.get_public_key_info()
        
        return {
            "user_id": self.user_id,
            "public_key": key_info.get("public_key"),
            "fingerprint": key_info.get("fingerprint"),
            "algorithm": key_info.get("algorithm", "Ed25519")
        }


# Convenience functions

def generate_user_keys(user_id: str, 
                       key_type: str = "ed25519") -> Dict[str, Any]:
    """
    Generate keys for a new user.
    
    Args:
        user_id: User identifier
        key_type: "ed25519" or "rsa"
        
    Returns:
        User credentials dictionary
    """
    signer = DigitalSignature(key_type)
    private_pem, public_pem = signer.generate_keypair()
    
    signer.load_private_key(private_pem)
    key_info = signer.get_public_key_info()
    
    return {
        "user_id": user_id,
        "private_key": private_pem.decode('utf-8'),
        "public_key": public_pem.decode('utf-8'),
        "fingerprint": key_info["fingerprint"],
        "algorithm": key_info["algorithm"]
    }


def verify_signature_quick(signed_data: Dict[str, Any],
                          public_key_pem: str) -> bool:
    """
    Quick signature verification.
    
    Args:
        signed_data: Signed data dictionary
        public_key_pem: PEM-encoded public key as string
        
    Returns:
        True if valid
    """
    verifier = DigitalSignature(
        key_type=signed_data.get("key_type", "ed25519")
    )
    verifier.load_public_key(public_key_pem.encode('utf-8'))
    return verifier.verify(signed_data)
