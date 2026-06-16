# ULE Security Features Documentation

## 🔐 Overview

ULE (Universal Ledger Engine) provides enterprise-grade security features built on top of SQLite, making it suitable for sensitive applications in healthcare, finance, and other regulated industries.

### 🛡️ Security Highlights
- **Password Hashing:** Uses **Argon2** (via `argon2-cffi`), the modern industry-standard password hashing algorithm, to securely store admin credentials and protect against brute-force attacks.
- **AES-256-GCM** encryption for data at rest
- **RSA-4096 / Ed25519** key pairs for digital signatures
- **SHA-256 hash chain** for tamper-proof audit trail
- **Role-Based Access Control (RBAC)** for permissions
- **Web UI Authentication** - Token-based auth with rate limiting
- **Terminal UI Password** - Password protection for CLI access
- **Input Validation** - SQL injection & XSS protection
- **CORS Protection** - Cross-origin request security
- **Rate Limiting** - DoS protection (60 req/min)

## Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ULE Application                          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              🔐 ULE Security Vault                          │
├─────────────────────────────────────────────────────────────┤
│  • Column-Level Encryption (AES-256-GCM)                    │
│  • Digital Signatures (RSA-4096 / Ed25519)                  │
│  • Row-Level Security (RLS)                                 │
│  • Dynamic Data Masking                                     │
│  • Database Integrity (SHA-256 checksums)                   │
│  • Time-Travel Snapshots                                    │
│  • Blockchain Audit Trail                                   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              📦 SQLite Storage Engine                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 📚 Security Modules

### 1. Column-Level Encryption

**Location:** `ule/security/column_encryption.py`

Encrypt individual columns with per-column keys derived from a master key.

#### Features
- AES-256-GCM encryption per column
- Key derivation from master key + column name
- Authentication tags for integrity
- Multiple encryption strategies

#### Usage

```python
from ule.security.column_encryption import ColumnEncryptionManager

# Initialize with master password
manager = ColumnEncryptionManager("super_secret_password")

# Configure which columns to encrypt
manager.configure_table("users", ["ssn", "credit_card", "password_hash"])
manager.configure_table("patients", ["diagnosis", "medical_history"])

# Encrypt row before insert
row = {"name": "Ali", "ssn": "123-45-6789", "age": 30}
encrypted_row = manager.encrypt_row("users", row)
# {"name": "Ali", "ssn": "ENC:base64...", "age": 30}

# Decrypt row after select
decrypted_row = manager.decrypt_row("users", encrypted_row)
# {"name": "Ali", "ssn": "123-45-6789", "age": 30}
```

#### Encryption Strategies

```python
from ule.security.column_encryption import EncryptionStrategy

# Full encryption - completely hidden
encrypted = EncryptionStrategy.full_encryption("sensitive data")

# Partial encryption - show first/last few characters
masked = EncryptionStrategy.partial_encryption("4111111111111111")
# Returns: "4111********1111"

# Hash only - original not recoverable
hash_value = EncryptionStrategy.hash_only("email@example.com")

# Tokenization - replace with random token
token_map = {}
token = EncryptionStrategy.tokenization("4111111111111111", token_map)
# Returns: "TKN:uuid-here"
```

---

### 2. Digital Signatures

**Location:** `ule/security/signatures.py`

Sign transactions and documents for non-repudiation and authenticity.

#### Features
- RSA-4096 signatures (court-admissible)
- Ed25519 signatures (faster, smaller)
- Key pair generation
- Signature verification

#### Usage

```python
from ule.security.signatures import DigitalSignature

# Initialize with Ed25519 (fast) or RSA (compatible)
signer = DigitalSignature(key_type="ed25519")

# Generate key pair
private_key, public_key = signer.generate_keypair()

# Save keys securely
with open("private.pem", "wb") as f:
    f.write(private_key)
with open("public.pem", "wb") as f:
    f.write(public_key)

# Load private key for signing
signer.load_private_key(private_key)

# Sign a transaction
transaction = {"from": "Alice", "to": "Bob", "amount": 1000}
signature = signer.sign_transaction(transaction)

# Verify signature
is_valid = signer.verify_signature(transaction, signature, public_key)
print(f"Signature valid: {is_valid}")  # True
```

#### Use Cases
- Legal contracts
- Medical orders
- Financial approvals
- Audit trail verification

---

### 3. Row-Level Security (RLS)

**Location:** `ule/security/access_control.py`

Control which rows users can access based on their attributes.

#### Features
- Dynamic policy evaluation
- User attribute-based access
- Role-based filtering
- SQL query modification

#### Usage

```python
from ule.security.access_control import RowLevelSecurity

# Initialize RLS
rls = RowLevelSecurity(db._conn)

# Set current user with attributes
rls.set_current_user("Dr. Smith", {
    "role": "doctor",
    "department": "Cardiology"
})

# Create policy: doctors see only their patients
rls.create_policy(
    table_name="patients",
    policy_name="doctor_patient_policy",
    condition="assigned_doctor = :user_name OR department = :user_department",
    policy_type="SELECT",
    roles=["doctor"]
)

# Apply policy to query
original_sql = "SELECT * FROM patients"
filtered_sql = rls.apply_policies(original_sql)
# Returns: "SELECT * FROM patients WHERE (assigned_doctor = 'Dr. Smith' OR department = 'Cardiology')"

# Check access
has_access = rls.check_access("patients", "SELECT")
```

#### Policy Examples

```python
# Multi-tenant SaaS: each customer sees only their data
rls.create_policy(
    "orders",
    "tenant_isolation",
    "tenant_id = :user_tenant_id",
    roles=["customer"]
)

# Healthcare: doctors see only their department's patients
rls.create_policy(
    "patients",
    "department_policy",
    "department = :user_department",
    roles=["doctor", "nurse"]
)

# Finance: advisors see only their clients
rls.create_policy(
    "accounts",
    "advisor_policy",
    "advisor_id = :user_name",
    roles=["advisor"]
)
```

---

### 4. Data Masking

**Location:** `ule/security/access_control.py`

Dynamically mask sensitive data based on user roles.

#### Features
- Multiple masking strategies
- Role-based masking rules
- Custom strategy support
- Column-level control

#### Usage

```python
from ule.security.access_control import DataMasking

# Initialize masking
masking = DataMasking(db._conn)

# Create masking rules
masking.create_rule(
    table_name="users",
    column_name="ssn",
    strategy="partial",
    roles=["clerk"],  # Only clerks see masked data
    parameters={"show": 4}  # Show first 4 chars
)

masking.create_rule(
    table_name="users",
    column_name="credit_card",
    strategy="last_four",  # Show only last 4 digits
    roles=["support"]
)

masking.create_rule(
    table_name="employees",
    column_name="salary",
    strategy="round",
    parameters={"nearest": 10000}  # Round to nearest 10k
)

# Apply masking to query results
cursor = db.execute("SELECT * FROM users")
rows = [dict(row) for row in cursor.fetchall()]

masked_rows = masking.mask_row("users", rows[0], user_role="clerk")
# {"name": "Ali", "ssn": "123-****6789", ...}
```

#### Built-in Masking Strategies

| Strategy | Description | Example |
|----------|-------------|---------|
| `full` | Complete mask | `****` |
| `partial` | Show first/last N chars | `1234****5678` |
| `last_four` | Show only last 4 | `****1111` |
| `redact` | Replace with [REDACTED] | `[REDACTED]` |
| `hash` | SHA-256 hash | `a1b2c3...` |
| `round` | Round numbers | `95000` → `100000` |

#### Custom Strategy

```python
def mask_email(value):
    parts = value.split('@')
    return f"{parts[0][:2]}***@{parts[1]}"

masking.register_strategy("email_mask", mask_email)
masking.create_rule("users", "email", "email_mask")
```

---

### 5. Database Integrity

**Location:** `ule/storage/integrity.py`

Self-healing database integrity with checksums and redundancy.

#### Features
- SHA-256 checksums for every page
- Triple redundancy for critical data
- Automatic corruption detection
- Self-healing from backup copies
- Quarantine for bad pages

#### Usage

```python
from ule.storage.integrity import IntegrityChecker

# Initialize checker
checker = IntegrityChecker(db_path, redundancy_factor=3)
checker.connect()

# Compute checksum for data
data = b"important data"
checksum = checker.compute_checksum(data)

# Store with redundancy
checker.store_with_redundancy("users", "1", data)

# Verify integrity
is_valid = checker.verify_all_checksums()

# Auto-repair if corruption detected
repair_result = checker.auto_repair()
print(f"Repaired {repair_result['repaired_count']} pages")

# Get quarantine report
quarantine = checker.get_quarantine_report()
```

---

### 6. Time-Travel Snapshots

**Location:** `ule/storage/snapshots.py`

Point-in-time recovery and historical queries.

#### Features
- Automatic snapshots before writes
- Point-in-time recovery
- Historical data queries
- Snapshot retention policies
- Space-efficient storage

#### Usage

```python
from ule.storage.snapshots import SnapshotManager

# Initialize snapshot manager
manager = SnapshotManager(db_path, retention_days=30)
manager.connect()

# Create snapshot before major operation
snapshot_id = manager.create_snapshot(description="Before migration")

# ... perform operations ...

# Restore if needed
restored_count = manager.restore_snapshot(snapshot_id)

# Query historical data
historical_users = manager.query_at_time(
    table_name="users",
    timestamp="2026-03-20T10:00:00"
)

# Get change history for a record
history = manager.get_history("users", "1", limit=10)
for change in history:
    print(f"{change['timestamp']}: {change['operation']} by {change['user_name']}")

# List all snapshots
snapshots = manager.list_snapshots()

# Cleanup old snapshots
manager._cleanup_old_snapshots()
```

#### Use Cases
- Accidental delete recovery
- Compliance auditing
- Historical reporting
- Before/after comparisons

---

## 🔒 Security Best Practices

### 1. Key Management

```python
# ✅ DO: Store keys in environment variables
import os
master_password = os.environ["ULE_MASTER_PASSWORD"]

# ✅ DO: Use key management services (AWS KMS, Azure Key Vault)
# ✅ DO: Rotate keys periodically
# ✅ DO: Use different keys for dev/staging/production

# ❌ DON'T: Hardcode keys in source code
master_password = "super_secret_123"  # NEVER DO THIS
```

### 2. Access Control

```python
# ✅ DO: Set user context for every request
ac.set_user(request.user.username, request.user.role)

# ✅ DO: Use least privilege principle
rls.create_policy("salary_data", "admin_only", "1=0", roles=["admin"])

# ✅ DO: Log all access
rls.log_access("patients", "SELECT", len(results), "doctor_policy")

# ❌ DON'T: Skip user context
ac.apply_access_control("SELECT * FROM users")  # No user set!
```

### 3. Encryption

```python
# ✅ DO: Encrypt sensitive columns
manager.configure_table("patients", ["ssn", "diagnosis", "medical_history"])

# ✅ DO: Use strong passwords (16+ chars, mixed case, numbers, symbols)
# ✅ DO: Enable encryption at rest

# ❌ DON'T: Encrypt everything (performance impact)
# ❌ DON'T: Store encrypted data with key in same location
```

### 4. Audit Trail

```python
# ✅ DO: Enable blockchain audit for compliance
config = Config(blockchain_enabled=True)

# ✅ DO: Review audit logs regularly
audit_entries = db.audit(table_name="users")

# ✅ DO: Sign critical transactions
signature = signer.sign_transaction(transaction)

# ❌ DON'T: Disable audit logging in production
```

---

## 📊 Compliance Mapping

| Regulation | ULE Feature | Implementation |
|------------|-------------|----------------|
| **HIPAA** | Column encryption, RLS, Audit | Encrypt PHI, limit access, log all access |
| **GDPR** | Data masking, Right to erasure | Mask PII, snapshot deletion |
| **PCI-DSS** | Column encryption, Masking | Encrypt card data, mask in UI |
| **SOX** | Digital signatures, Audit trail | Sign approvals, immutable logs |
| **FedRAMP** | AES-256, RLS, Integrity | FIPS-validated encryption, access control |

---

## 🧪 Testing Security Features

```python
import pytest
from ule.security.access_control import AccessControlManager

def test_rls_policy():
    ac = AccessControlManager(db._conn)
    ac.set_user("doctor1", role="doctor")
    
    ac.rls.create_policy(
        "patients",
        "doctor_policy",
        "assigned_doctor = :user_name"
    )
    
    sql = ac.apply_access_control("SELECT * FROM patients")
    assert "doctor1" in sql

def test_data_masking():
    masking = DataMasking(db._conn)
    masking.create_rule("users", "ssn", "full")
    
    row = {"name": "Ali", "ssn": "123-45-6789"}
    masked = masking.mask_row("users", row)
    
    assert masked["ssn"] == "****"
```

---

## 📈 Performance Considerations

| Feature | Overhead | Mitigation |
|---------|----------|------------|
| Column Encryption | 5-10% per encrypted column | Encrypt only sensitive columns |
| RLS | 2-5% per query | Index policy columns |
| Data Masking | 1-3% per row | Cache masked results |
| Integrity Checks | 10-15% on write | Run verification asynchronously |
| Snapshots | 5-10% on create | Schedule during low-traffic |
| Digital Signatures | 50-100ms per sign | Batch signing for bulk operations |

---

## 🆘 Troubleshooting

### Issue: RLS policy not applying

**Solution:** Ensure user context is set before query:
```python
ac.set_user(username, role)  # Must be called first
sql = ac.apply_access_control(query)
```

### Issue: Decryption fails

**Solution:** Verify master password and salt match:
```python
metadata = encryption.get_encryption_metadata()
# Store metadata securely with backup
```

### Issue: Snapshot restore returns 0 rows

**Solution:** Check snapshot file exists and is readable:
```python
snapshots = manager.list_snapshots()
print(snapshots[0]["file_path"])  # Verify path
```

---

## 📞 Security Support

For security issues or questions:
1. Review this documentation
2. Check test files for examples
3. Report vulnerabilities responsibly

---

**Version:** 0.1.0
**Last Updated:** April 9, 2026

## 🛡️ Production Hardening (New in 0.1.0)

ULE has been significantly hardened for production use with the following professional features:

### 1. "Secure by Default" Initialization
The `ule init` command now launches a mandatory **Setup Wizard**. You must set a unique admin password upon creation. There are no hardcoded default credentials in the system.

### 2. Parameterized NLQ Engine
All Natural Language Query (NLQ) translations now use **parameterized SQL**. User input is never directly interpolated into query strings, providing robust protection against SQL injection across all 20 supported languages.

### 3. REST API Fortification
- **Mandatory Auth:** All sensitive API endpoints now require Bearer token or Basic authentication.
- **Path Validation:** Robust prevention of directory traversal attacks.
- **Connection Pooling:** Thread-safe LRU connection pool for high-concurrency environments.

### 4. Per-Document Integrity (D-Hash)
Every document in the NoSQL engine is stored with a SHA-256 hash. Upon retrieval, ULE automatically verifies the hash to detect silent data corruption or unauthorized manual database modifications.
