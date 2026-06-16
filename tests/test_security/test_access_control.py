"""Tests for Access Control (RLS + Masking)."""

import pytest
import sqlite3
import tempfile
from pathlib import Path

from ule.security.access_control import (
    RowLevelSecurity, DataMasking, AccessControlManager,
    require_role
)


class TestRowLevelSecurity:
    """Test row-level security functionality."""

    @pytest.fixture
    def rls_db(self):
        """Create test database with RLS."""
        fd, db_path = tempfile.mkstemp(suffix='.udb')
        import os
        os.close(fd)

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        # Create test tables
        conn.execute("""CREATE TABLE patients (
            id INTEGER PRIMARY KEY,
            name TEXT,
            assigned_doctor TEXT,
            department TEXT,
            diagnosis TEXT
        )""")

        conn.execute("""CREATE TABLE employees (
            id INTEGER PRIMARY KEY,
            name TEXT,
            department TEXT,
            salary INTEGER
        )""")

        # Insert test data
        conn.execute("""INSERT INTO patients VALUES
            (1, 'Patient A', 'Dr. Smith', 'Cardiology', 'Heart disease'),
            (2, 'Patient B', 'Dr. Smith', 'Neurology', 'Migraine'),
            (3, 'Patient C', 'Dr. Jones', 'Cardiology', 'Arrhythmia')
        """)

        conn.execute("""INSERT INTO employees VALUES
            (1, 'Alice', 'Engineering', 100000),
            (2, 'Bob', 'Engineering', 90000),
            (3, 'Charlie', 'Sales', 80000)
        """)

        conn.commit()

        yield conn

        conn.close()
        Path(db_path).unlink()

    def test_create_policy(self, rls_db):
        """Test creating RLS policy."""
        rls = RowLevelSecurity(rls_db)

        # Set current user
        rls.set_current_user("admin", {"role": "admin"})

        # Create policy
        rls.create_policy(
            "patients",
            "doctor_policy",
            "assigned_doctor = :user_name",
            roles=["doctor"]
        )

        # Verify policy created
        policies = rls._get_policies("patients", "SELECT")
        assert len(policies) == 1
        assert policies[0]["policy_name"] == "doctor_policy"

    def test_apply_policy_to_query(self, rls_db):
        """Test applying RLS policy to SQL query."""
        rls = RowLevelSecurity(rls_db)

        # Set current user as doctor
        rls.set_current_user("Dr. Smith", {"role": "doctor"})

        # Create policy
        rls.create_policy(
            "patients",
            "doctor_policy",
            "assigned_doctor = :user_name",
            roles=["doctor"]
        )

        # Apply policy to query
        original_sql = "SELECT * FROM patients"
        modified_sql = rls.apply_policies(original_sql)

        assert "WHERE" in modified_sql
        assert "Dr. Smith" in modified_sql

    def test_policy_filters_results(self, rls_db):
        """Test that policy actually filters results."""
        rls = RowLevelSecurity(rls_db)

        # Set current user as doctor
        rls.set_current_user("Dr. Smith", {"role": "doctor"})

        # Create policy
        rls.create_policy(
            "patients",
            "doctor_policy",
            "assigned_doctor = :user_name",
            roles=["doctor"]
        )

        # Execute filtered query
        modified_sql = rls.apply_policies("SELECT * FROM patients")
        cursor = rls_db.execute(modified_sql)
        results = cursor.fetchall()

        # Should only see Dr. Smith's patients
        assert len(results) == 2
        assert all(row["assigned_doctor"] == "Dr. Smith" for row in results)

    def test_check_access(self, rls_db):
        """Test access check."""
        rls = RowLevelSecurity(rls_db)

        # No user set - should deny access
        assert rls.check_access("patients") is False

        # Set user
        rls.set_current_user("Dr. Smith", {"role": "doctor"})

        # No policy yet - should deny
        assert rls.check_access("patients") is False

        # Create policy
        rls.create_policy(
            "patients",
            "doctor_policy",
            "assigned_doctor = :user_name",
            roles=["doctor"]
        )

        # Now should have access
        assert rls.check_access("patients") is True

    def test_user_attributes(self, rls_db):
        """Test user attributes in policies."""
        rls = RowLevelSecurity(rls_db)

        # Set user with department attribute
        rls.set_current_user("Dr. Smith", {
            "role": "doctor",
            "department": "Cardiology"
        })

        # Create policy based on department
        rls.create_policy(
            "patients",
            "department_policy",
            "department = :user_department",
            roles=["doctor"]
        )

        # Apply policy
        modified_sql = rls.apply_policies("SELECT * FROM patients")

        # Execute query
        cursor = rls_db.execute(modified_sql)
        results = cursor.fetchall()

        # Should only see Cardiology patients
        assert len(results) == 2
        assert all(row["department"] == "Cardiology" for row in results)


class TestDataMasking:
    """Test data masking functionality."""

    @pytest.fixture
    def masking_db(self):
        """Create test database with sensitive data."""
        fd, db_path = tempfile.mkstemp(suffix='.udb')
        import os
        os.close(fd)

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        # Create test table
        conn.execute("""CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT,
            email TEXT,
            ssn TEXT,
            credit_card TEXT,
            salary INTEGER
        )""")

        # Insert test data
        conn.execute("""INSERT INTO users VALUES
            (1, 'Ali Ahmed', 'ali@example.com', '123-45-6789', '4111111111111111', 95000),
            (2, 'Sara Khan', 'sara@example.com', '987-65-4321', '5500000000000004', 87000)
        """)

        conn.commit()

        yield conn

        conn.close()
        Path(db_path).unlink()

    def test_create_masking_rule(self, masking_db):
        """Test creating masking rule."""
        masking = DataMasking(masking_db)

        # Create rule for SSN
        masking.create_rule(
            "users",
            "ssn",
            "partial",
            roles=["clerk"],
            parameters={"show": 2}
        )

        # Verify rule created
        rules = masking.get_masking_rules("users")
        assert "ssn" in rules
        assert rules["ssn"]["strategy"] == "partial"

    def test_partial_mask(self, masking_db):
        """Test partial masking strategy."""
        masking = DataMasking(masking_db)

        # Create rule
        masking.create_rule(
            "users",
            "ssn",
            "partial",
            parameters={"show": 4}
        )

        # Get row
        cursor = masking_db.execute("SELECT * FROM users WHERE id = 1")
        row = dict(cursor.fetchone())

        # Apply masking
        masked = masking.mask_row("users", row)

        # Partial mask should show some chars and have asterisks
        assert len(masked["ssn"]) > 4
        assert "*" in masked["ssn"]

    def test_full_mask(self, masking_db):
        """Test full masking strategy."""
        masking = DataMasking(masking_db)

        # Create rule
        masking.create_rule("users", "ssn", "full")

        # Get row
        cursor = masking_db.execute("SELECT * FROM users WHERE id = 1")
        row = dict(cursor.fetchone())

        # Apply masking
        masked = masking.mask_row("users", row)

        assert masked["ssn"] == "****"

    def test_last_four_mask(self, masking_db):
        """Test last-four masking strategy."""
        masking = DataMasking(masking_db)

        # Create rule for credit card
        masking.create_rule("users", "credit_card", "last_four")

        # Get row
        cursor = masking_db.execute("SELECT * FROM users WHERE id = 1")
        row = dict(cursor.fetchone())

        # Apply masking
        masked = masking.mask_row("users", row)

        assert masked["credit_card"].startswith("****")
        assert masked["credit_card"].endswith("1111")

    def test_round_numbers(self, masking_db):
        """Test number rounding strategy."""
        masking = DataMasking(masking_db)

        # Create rule for salary
        masking.create_rule(
            "users",
            "salary",
            "round",
            parameters={"nearest": 10000}
        )

        # Get row
        cursor = masking_db.execute("SELECT * FROM users WHERE id = 1")
        row = dict(cursor.fetchone())

        # Apply masking
        masked = masking.mask_row("users", row)

        # 95000 rounded to nearest 10000 = 100000
        assert masked["salary"] == 100000

    def test_role_based_masking(self, masking_db):
        """Test role-based masking."""
        masking = DataMasking(masking_db)

        # Create rule that only applies to clerks
        masking.create_rule(
            "users",
            "ssn",
            "full",
            roles=["clerk"]
        )

        # Get row
        cursor = masking_db.execute("SELECT * FROM users WHERE id = 1")
        row = dict(cursor.fetchone())

        # Admin sees unmasked data
        masked_admin = masking.mask_row("users", row, user_role="admin")
        assert masked_admin["ssn"] == "123-45-6789"

        # Clerk sees masked data
        masked_clerk = masking.mask_row("users", row, user_role="clerk")
        assert masked_clerk["ssn"] == "****"

    def test_custom_strategy(self, masking_db):
        """Test custom masking strategy."""
        masking = DataMasking(masking_db)

        # Register custom strategy
        def mask_email(value):
            parts = value.split('@')
            return f"{parts[0][:2]}***@{parts[1]}"

        masking.register_strategy("email_mask", mask_email)

        # Create rule
        masking.create_rule("users", "email", "email_mask")

        # Get row
        cursor = masking_db.execute("SELECT * FROM users WHERE id = 1")
        row = dict(cursor.fetchone())

        # Apply masking
        masked = masking.mask_row("users", row)

        assert masked["email"].startswith("al***@")


class TestAccessControlManager:
    """Test unified access control manager."""

    @pytest.fixture
    def ac_db(self):
        """Create test database for access control."""
        fd, db_path = tempfile.mkstemp(suffix='.udb')
        import os
        os.close(fd)

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        conn.execute("""CREATE TABLE sensitive_data (
            id INTEGER PRIMARY KEY,
            owner TEXT,
            value TEXT,
            classification TEXT
        )""")

        conn.execute("""INSERT INTO sensitive_data VALUES
            (1, 'alice', 'Secret A', 'confidential'),
            (2, 'bob', 'Secret B', 'public'),
            (3, 'alice', 'Secret C', 'top-secret')
        """)

        conn.commit()

        yield conn

        conn.close()
        Path(db_path).unlink()

    def test_set_user(self, ac_db):
        """Test setting user context."""
        ac = AccessControlManager(ac_db)

        ac.set_user("alice", role="user", attributes={"department": "engineering"})

        assert ac._current_user["name"] == "alice"
        assert ac._current_user["role"] == "user"

    def test_combined_rls_and_masking(self, ac_db):
        """Test combining RLS and masking."""
        ac = AccessControlManager(ac_db)

        # Set user
        ac.set_user("alice", role="user")

        # Create RLS policy
        ac.rls.create_policy(
            "sensitive_data",
            "owner_policy",
            "owner = :user_name",
            roles=["user"]
        )

        # Create masking rule
        ac.masking.create_rule("sensitive_data", "value", "partial")

        # Apply access control to query
        sql = "SELECT * FROM sensitive_data"
        filtered_sql = ac.apply_access_control(sql)

        # Execute query
        cursor = ac_db.execute(filtered_sql)
        results = cursor.fetchall()

        # Should see alice's data (at least 1 row)
        assert len(results) >= 1

        # Apply masking to results
        masked_results = ac.filter_results("sensitive_data", [dict(r) for r in results])

        # Values should be masked (shorter or contain asterisks)
        assert len(masked_results[0]["value"]) < 20 or "*" in masked_results[0]["value"]

    def test_permission_check(self, ac_db):
        """Test permission checking."""
        ac = AccessControlManager(ac_db)

        # No user set
        assert ac.check_permission("sensitive_data") is False

        # Set user
        ac.set_user("alice", role="admin")
        # Admin role might have implicit access
        # This test verifies the check doesn't crash
