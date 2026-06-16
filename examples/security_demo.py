#!/usr/bin/env python3
"""ULE Security Features Demo.

This script demonstrates all security features of ULE:
- Column-level encryption
- Digital signatures
- Row-level security (RLS)
- Data masking
- Database integrity
- Time-travel snapshots

Run: python examples/security_demo.py
"""

import os
import tempfile
from pathlib import Path
from datetime import datetime

from ule.core.database import ULEDatabase
from ule.security.column_encryption import ColumnEncryptionManager
from ule.security.signatures import DigitalSignature
from ule.security.access_control import AccessControlManager
from ule.storage.snapshots import SnapshotManager


def print_header(title: str) -> None:
    """Print formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_subheader(title: str) -> None:
    """Print formatted subheader."""
    print(f"\n▶ {title}")
    print("-" * 50)


def demo_column_encryption(db: ULEDatabase) -> None:
    """Demonstrate column-level encryption."""
    print_header("1. COLUMN-LEVEL ENCRYPTION")

    # Create users table
    db.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT,
        email TEXT,
        ssn TEXT,
        credit_card TEXT
    )""")

    # Initialize encryption manager
    encryption_mgr = ColumnEncryptionManager("SuperSecretPassword123!")

    # Configure which columns to encrypt
    encryption_mgr.configure_table("users", ["ssn", "credit_card"])

    print_subheader("Encrypting Sensitive Data")

    # Insert encrypted data
    users_data = [
        {"name": "Ali Ahmed", "email": "ali@example.com", "ssn": "123-45-6789", "credit_card": "4111111111111111"},
        {"name": "Sara Khan", "email": "sara@example.com", "ssn": "987-65-4321", "credit_card": "5500000000000004"},
        {"name": "Ahmed Hassan", "email": "ahmed@example.com", "ssn": "456-78-9012", "credit_card": "340000000000009"},
    ]

    print("Inserting encrypted user data...")
    for user in users_data:
        encrypted = encryption_mgr.encrypt_row("users", user)
        db.insert("users", encrypted)
        print(f"  ✓ Inserted: {user['name']} (SSN encrypted)")

    # Query and decrypt
    print_subheader("Decrypting Data on Read")

    cursor = db._conn.execute("SELECT * FROM users")
    rows = cursor.fetchall()

    for row in rows:
        user_dict = dict(row)
        decrypted = encryption_mgr.decrypt_row("users", user_dict)
        print(f"  ✓ {decrypted['name']}: SSN={decrypted['ssn']}, Email={decrypted['email']}")

    print("\n✅ Column encryption demo complete!")


def demo_digital_signatures() -> None:
    """Demonstrate digital signatures."""
    print_header("2. DIGITAL SIGNATURES")

    print_subheader("Generating Key Pair")

    # Initialize signer
    signer = DigitalSignature(key_type="ed25519")
    private_key, public_key = signer.generate_keypair()

    print(f"  ✓ Generated Ed25519 key pair")
    print(f"  ✓ Private key size: {len(private_key)} bytes")
    print(f"  ✓ Public key size: {len(public_key)} bytes")

    print_subheader("Signing Transactions")

    # Load private key
    signer.load_private_key(private_key)

    # Sign multiple transactions
    transactions = [
        {"from": "Alice", "to": "Bob", "amount": 1000, "timestamp": "2026-03-23T10:00:00"},
        {"from": "Bob", "to": "Charlie", "amount": 500, "timestamp": "2026-03-23T11:00:00"},
        {"from": "Charlie", "to": "Alice", "amount": 250, "timestamp": "2026-03-23T12:00:00"},
    ]

    signed_transactions = []
    for tx in transactions:
        sig_result = signer.sign(tx)
        signed_transactions.append(sig_result)
        print(f"  ✓ Signed: {tx['from']} → {tx['to']} (${tx['amount']})")

    print_subheader("Verifying Signatures")

    for i, signed_tx in enumerate(signed_transactions):
        is_valid = signer.verify(signed_tx, public_key)
        status = "✓ Valid" if is_valid else "✗ Invalid"
        print(f"  {status}: Transaction {i+1}")

    # Tamper detection
    print_subheader("Tamper Detection")

    tampered_tx = signed_transactions[0].copy()
    tampered_tx["data"]["amount"] = 999999  # Evil hacker tries to change amount

    is_valid = signer.verify(tampered_tx, public_key)
    status = "✓ Valid" if is_valid else "✗ Invalid"
    print(f"  Tampered transaction: {status} (as expected)")

    print("\n✅ Digital signatures demo complete!")


def demo_row_level_security(db: ULEDatabase) -> None:
    """Demonstrate row-level security."""
    print_header("3. ROW-LEVEL SECURITY (RLS)")

    # Create patients table
    db.execute("""CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY,
        name TEXT,
        assigned_doctor TEXT,
        department TEXT,
        diagnosis TEXT
    )""")

    # Insert sample data
    patients_data = [
        ("Patient A", "Dr. Smith", "Cardiology", "Heart disease"),
        ("Patient B", "Dr. Smith", "Neurology", "Migraine"),
        ("Patient C", "Dr. Jones", "Cardiology", "Arrhythmia"),
        ("Patient D", "Dr. Jones", "Oncology", "Cancer"),
    ]

    for name, doctor, dept, diagnosis in patients_data:
        db.execute(
            "INSERT INTO patients (name, assigned_doctor, department, diagnosis) VALUES (?, ?, ?, ?)",
            (name, doctor, dept, diagnosis)
        )

    print_subheader("Setting Up RLS Policies")

    # Initialize RLS
    rls = AccessControlManager(db._conn)

    # Create policy: doctors see only their patients
    rls.rls.create_policy(
        table_name="patients",
        policy_name="doctor_patient_policy",
        condition="assigned_doctor = :user_name",
        policy_type="SELECT",
        roles=["doctor"]
    )
    print("  ✓ Created policy: doctors see only their assigned patients")

    # Simulate Dr. Smith accessing data
    print_subheader("Dr. Smith's View")

    rls.set_user("Dr. Smith", role="doctor", attributes={"department": "Cardiology"})

    sql = "SELECT * FROM patients"
    filtered_sql = rls.apply_access_control(sql)
    print(f"  Original SQL: {sql}")
    print(f"  Filtered SQL: {filtered_sql}")

    cursor = db._conn.execute(filtered_sql)
    results = cursor.fetchall()

    print(f"\n  Dr. Smith can see {len(results)} patients:")
    for row in results:
        print(f"    - {row[1]} (Dr. {row[2]}, {row[3]})")

    # Simulate Dr. Jones accessing data
    print_subheader("Dr. Jones's View")

    rls.set_user("Dr. Jones", role="doctor", attributes={"department": "Cardiology"})

    filtered_sql = rls.apply_access_control(sql)
    cursor = db._conn.execute(filtered_sql)
    results = cursor.fetchall()

    print(f"  Dr. Jones can see {len(results)} patients:")
    for row in results:
        print(f"    - {row[1]} (Dr. {row[2]}, {row[3]})")

    print("\n✅ Row-level security demo complete!")


def demo_data_masking(db: ULEDatabase) -> None:
    """Demonstrate data masking."""
    print_header("4. DATA MASKING")

    # Create employees table
    db.execute("""CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY,
        name TEXT,
        email TEXT,
        ssn TEXT,
        salary INTEGER
    )""")

    # Insert sample data
    employees_data = [
        ("Ali Ahmed", "ali@example.com", "123-45-6789", 95000),
        ("Sara Khan", "sara@example.com", "987-65-4321", 87000),
        ("Ahmed Hassan", "ahmed@example.com", "456-78-9012", 102000),
    ]

    for name, email, ssn, salary in employees_data:
        db.execute(
            "INSERT INTO employees (name, email, ssn, salary) VALUES (?, ?, ?, ?)",
            (name, email, ssn, salary)
        )

    print_subheader("Creating Masking Rules")

    # Initialize masking
    masking = AccessControlManager(db._conn)

    # Create masking rules
    masking.masking.create_rule("employees", "ssn", "partial", parameters={"show": 4})
    print("  ✓ SSN: Show first 4 characters")

    masking.masking.create_rule("employees", "salary", "round", parameters={"nearest": 10000})
    print("  ✓ Salary: Round to nearest 10,000")

    # Query data
    cursor = db._conn.execute("SELECT * FROM employees")
    rows = [dict(row) for row in cursor.fetchall()]

    print_subheader("Unmasked Data (Admin View)")

    for emp in rows:
        print(f"  {emp['name']}: SSN={emp['ssn']}, Salary=${emp['salary']:,}")

    print_subheader("Masked Data (Clerk View)")

    for emp in rows:
        masked = masking.masking.mask_row("employees", emp, user_role="clerk")
        print(f"  {masked['name']}: SSN={masked['ssn']}, Salary=${masked['salary']:,}")

    print("\n✅ Data masking demo complete!")


def demo_time_travel_snapshots(db: ULEDatabase) -> None:
    """Demonstrate time-travel snapshots."""
    print_header("5. TIME-TRAVEL SNAPSHOTS")

    # Create accounts table
    db.execute("""CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY,
        owner TEXT,
        balance REAL
    )""")

    # Insert initial data
    db.execute("INSERT INTO accounts (owner, balance) VALUES ('Alice', 10000)")
    db.execute("INSERT INTO accounts (owner, balance) VALUES ('Bob', 5000)")

    print_subheader("Initial State")

    cursor = db._conn.execute("SELECT * FROM accounts")
    for row in cursor:
        print(f"  {row[1]}: ${row[2]:,.2f}")

    # Initialize snapshot manager
    snapshot_mgr = SnapshotManager(db.db_path)
    snapshot_mgr.connect()

    print_subheader("Creating Snapshot")

    snapshot_id = snapshot_mgr.create_snapshot(description="Before transfers")
    print(f"  ✓ Created snapshot: {snapshot_id}")

    # Simulate transactions
    print_subheader("Performing Transactions")

    db.execute("UPDATE accounts SET balance = balance - 1000 WHERE owner = 'Alice'")
    db.execute("UPDATE accounts SET balance = balance + 1000 WHERE owner = 'Bob'")
    db._conn.commit()

    print("  ✓ Alice transferred $1,000 to Bob")

    print_subheader("After Transactions")

    cursor = db._conn.execute("SELECT * FROM accounts")
    for row in cursor:
        print(f"  {row[1]}: ${row[2]:,.2f}")

    print_subheader("Restoring from Snapshot")

    restored_count = snapshot_mgr.restore_snapshot(snapshot_id)
    print(f"  ✓ Restored {restored_count} records")

    print_subheader("After Restore")

    cursor = db._conn.execute("SELECT * FROM accounts")
    for row in cursor:
        print(f"  {row[1]}: ${row[2]:,.2f}")

    snapshot_mgr.close()

    print("\n✅ Time-travel snapshots demo complete!")


def main() -> None:
    """Run all security demos."""
    print_header("🔐 ULE SECURITY FEATURES DEMO")
    print("Universal Ledger Engine - Enterprise Security Edition")
    print(f"Demo started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Create temporary database path
    import tempfile
    db_path = tempfile.mktemp(suffix='.udb')

    try:
        # Initialize database
        db = ULEDatabase(db_path)
        db.init()

        print(f"\n✓ Created temporary database: {db_path}")

        # Run demos
        demo_column_encryption(db)
        demo_digital_signatures()
        demo_row_level_security(db)
        demo_data_masking(db)
        demo_time_travel_snapshots(db)

        # Cleanup
        db.close()

        print_header("🎉 ALL DEMOS COMPLETE")
        print("\nSecurity features demonstrated:")
        print("  ✓ Column-level encryption (AES-256-GCM)")
        print("  ✓ Digital signatures (Ed25519)")
        print("  ✓ Row-level security (RLS)")
        print("  ✓ Dynamic data masking")
        print("  ✓ Time-travel snapshots")
        print("\nFor more information, see docs/SECURITY_FEATURES.md")

    finally:
        # Clean up temp file
        Path(db_path).unlink(missing_ok=True)


if __name__ == "__main__":
    main()
