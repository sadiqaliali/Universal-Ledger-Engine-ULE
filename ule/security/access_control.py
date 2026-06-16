"""Access Control for ULE.

This module provides row-level security (RLS) and data masking,
enabling fine-grained access control and privacy protection.

Features:
- Row-level security policies
- Dynamic data masking
- Role-based access control integration
- Column-level permissions
- Audit logging for access
"""

import re
import json
import sqlite3
import hashlib
from typing import Any, Dict, List, Optional, Callable, Union
from datetime import datetime
from pathlib import Path
import threading


class RowLevelSecurity:
    """
    Row-level security (RLS) for fine-grained access control.

    Policies determine which rows a user can access based on:
    - User attributes (role, department, clearance level)
    - Row attributes (owner, classification, region)
    - Context (time of day, IP address, location)

    Use cases:
    - Multi-tenant SaaS (each customer sees only their data)
    - Healthcare (doctors see only their patients)
    - Finance (advisors see only their clients)
    - HR (managers see only their department)
    """

    def __init__(self, db_connection: sqlite3.Connection):
        """
        Initialize RLS.

        Args:
            db_connection: SQLite database connection
        """
        self._conn = db_connection
        self._policies: Dict[str, List[Dict]] = {}
        self._current_user: Optional[Dict] = None
        self._enabled = True

        self._init_rls_tables()

    def _init_rls_tables(self) -> None:
        """Create RLS metadata tables."""
        tables = [
            # RLS policies
            """CREATE TABLE IF NOT EXISTS _rls_policies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT NOT NULL,
                policy_name TEXT NOT NULL,
                policy_type TEXT NOT NULL,
                condition TEXT NOT NULL,
                roles TEXT,
                users TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                created_by TEXT,
                UNIQUE(table_name, policy_name)
            )""",

            # User attributes for RLS
            """CREATE TABLE IF NOT EXISTS _rls_user_attributes (
                user_name TEXT PRIMARY KEY,
                attributes TEXT NOT NULL,
                updated_at TEXT DEFAULT (datetime('now'))
            )""",

            # RLS audit log
            """CREATE TABLE IF NOT EXISTS _rls_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT (datetime('now')),
                user_name TEXT,
                table_name TEXT,
                operation TEXT,
                policy_applied TEXT,
                rows_affected INTEGER
            )""",
        ]

        for sql in tables:
            self._conn.execute(sql)

        self._conn.commit()

    def set_current_user(self, user_name: str,
                         attributes: Optional[Dict] = None) -> None:
        """
        Set the current user for RLS evaluation.

        Args:
            user_name: Username
            attributes: Optional user attributes (role, department, etc.)
        """
        self._current_user = {
            "name": user_name,
            "attributes": attributes or {}
        }

    def create_policy(self, table_name: str, policy_name: str,
                      condition: str, policy_type: str = "SELECT",
                      roles: Optional[List[str]] = None,
                      users: Optional[List[str]] = None) -> None:
        """
        Create an RLS policy.

        Args:
            table_name: Table to protect
            policy_name: Unique policy name
            condition: SQL WHERE condition (uses :user_name, :user_role, etc.)
            policy_type: SELECT, INSERT, UPDATE, or DELETE
            roles: Roles this policy applies to (None for all)
            users: Specific users (None for all)

        Example:
            create_policy(
                "patients",
                "doctor_patient_policy",
                "assigned_doctor = :user_name OR department = :user_department",
                roles=["doctor"]
            )
        """
        self._conn.execute(
            """INSERT OR REPLACE INTO _rls_policies 
               (table_name, policy_name, policy_type, condition, roles, users, created_by)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (table_name, policy_name, policy_type, condition,
             json.dumps(roles) if roles else None,
             json.dumps(users) if users else None,
             self._current_user["name"] if self._current_user else None)
        )
        self._conn.commit()

        # Invalidate policy cache
        if table_name in self._policies:
            del self._policies[table_name]

    def drop_policy(self, table_name: str, policy_name: str) -> None:
        """Remove an RLS policy."""
        self._conn.execute(
            "DELETE FROM _rls_policies WHERE table_name = ? AND policy_name = ?",
            (table_name, policy_name)
        )
        self._conn.commit()

        if table_name in self._policies:
            del self._policies[table_name]

    def _get_policies(self, table_name: str,
                      policy_type: str = "SELECT") -> List[Dict]:
        """Get applicable policies for a table."""
        if table_name in self._policies:
            return self._policies[table_name]

        cursor = self._conn.execute(
            "SELECT * FROM _rls_policies WHERE table_name = ? AND policy_type = ?",
            (table_name, policy_type)
        )

        policies = []
        for row in cursor.fetchall():
            policy = dict(row)

            # Parse JSON fields
            if policy.get("roles"):
                policy["roles"] = json.loads(policy["roles"])
            if policy.get("users"):
                policy["users"] = json.loads(policy["users"])

            policies.append(policy)

        self._policies[table_name] = policies
        return policies

    def _evaluate_policy(self, policy: Dict) -> Optional[str]:
        """
        Evaluate if a policy applies to current user.

        Returns:
            SQL condition if policy applies, None otherwise
        """
        if not self._current_user:
            return None

        # Check if policy applies to user's roles
        if policy.get("roles"):
            user_role = self._current_user["attributes"].get("role")
            if user_role not in policy["roles"]:
                return None

        # Check if policy applies to specific users
        if policy.get("users"):
            if self._current_user["name"] not in policy["users"]:
                return None

        # Build condition with user parameters
        condition = policy["condition"]

        # Replace placeholders with actual values
        condition = condition.replace(":user_name", f"'{self._current_user['name']}'")

        for key, value in self._current_user["attributes"].items():
            placeholder = f":user_{key}"
            if isinstance(value, str):
                condition = condition.replace(placeholder, f"'{value}'")
            else:
                condition = condition.replace(placeholder, str(value))

        return condition

    def apply_policies(self, sql: str,
                       policy_type: str = "SELECT") -> str:
        """
        Apply RLS policies to a SQL query.

        Args:
            sql: Original SQL query
            policy_type: Type of operation

        Returns:
            Modified SQL with RLS conditions
        """
        if not self._enabled or not self._current_user:
            return sql

        # Extract table name from SQL (simplified)
        sql_upper = sql.upper()
        table_name = None

        if "FROM" in sql_upper:
            match = re.search(r'FROM\s+(\w+)', sql, re.IGNORECASE)
            if match:
                table_name = match.group(1)

        if not table_name:
            return sql

        # Get applicable policies
        policies = self._get_policies(table_name, policy_type)

        if not policies:
            return sql

        # Build combined WHERE condition
        conditions = []
        for policy in policies:
            condition = self._evaluate_policy(policy)
            if condition:
                conditions.append(f"({condition})")

        if not conditions:
            return sql

        # Add WHERE clause to SQL
        combined = " OR ".join(conditions)

        if "WHERE" in sql.upper():
            sql = f"{sql} AND ({combined})"
        else:
            sql = f"{sql} WHERE ({combined})"

        return sql

    def check_access(self, table_name: str,
                     operation: str = "SELECT") -> bool:
        """
        Check if current user has access to a table.

        Args:
            table_name: Table to check
            operation: SELECT, INSERT, UPDATE, or DELETE

        Returns:
            True if access granted
        """
        if not self._current_user:
            return False

        policies = self._get_policies(table_name, operation)

        # If no policies, access is denied by default
        if not policies:
            return False

        # Check if any policy applies
        for policy in policies:
            if self._evaluate_policy(policy):
                return True

        return False

    def log_access(self, table_name: str, operation: str,
                   rows_affected: int, policy_applied: str) -> None:
        """Log RLS access for audit."""
        self._conn.execute(
            """INSERT INTO _rls_audit 
               (user_name, table_name, operation, policy_applied, rows_affected)
               VALUES (?, ?, ?, ?, ?)""",
            (self._current_user["name"] if self._current_user else None,
             table_name, operation, policy_applied, rows_affected)
        )
        self._conn.commit()

    def enable(self) -> None:
        """Enable RLS enforcement."""
        self._enabled = True

    def disable(self) -> None:
        """Disable RLS enforcement (for admin operations)."""
        self._enabled = False

    def get_user_attributes(self, user_name: str) -> Dict:
        """Get stored user attributes."""
        cursor = self._conn.execute(
            "SELECT attributes FROM _rls_user_attributes WHERE user_name = ?",
            (user_name,)
        )
        row = cursor.fetchone()

        if row:
            return json.loads(row["attributes"])
        return {}

    def set_user_attributes(self, user_name: str,
                            attributes: Dict) -> None:
        """Store user attributes for RLS."""
        self._conn.execute(
            """INSERT OR REPLACE INTO _rls_user_attributes 
               (user_name, attributes, updated_at)
               VALUES (?, ?, datetime('now'))""",
            (user_name, json.dumps(attributes))
        )
        self._conn.commit()


class DataMasking:
    """
    Dynamic data masking for privacy protection.

    Masks sensitive data based on user roles and policies.

    Masking strategies:
    - Full mask: **** (completely hidden)
    - Partial mask: 1234****5678 (show first/last few chars)
    - Hash: SHA256 hash (for comparison only)
    - Redact: Replace with [REDACTED]
    - Round: Round numbers to nearest N
    - Date shift: Shift dates by fixed offset
    """

    MASK_STRATEGIES = {
        "full": lambda x: "****",
        "partial": lambda x, show=4: f"{str(x)[:show]}{'*' * (len(str(x)) - show * 2)}{str(x)[-show:]}" if len(str(x)) > show * 2 else "*" * len(str(x)),
        "redact": lambda x: "[REDACTED]",
        "hash": lambda x: hashlib.sha256(str(x).encode()).hexdigest(),
        "round": lambda x, nearest=100: round(float(x) / nearest) * nearest if x else None,
        "last_four": lambda x: f"****{str(x)[-4:]}" if len(str(x)) >= 4 else "****",
    }

    def __init__(self, db_connection: sqlite3.Connection):
        """
        Initialize data masking.

        Args:
            db_connection: SQLite database connection
        """
        self._conn = db_connection
        self._masking_rules: Dict[str, Dict] = {}
        self._custom_strategies: Dict[str, Callable] = {}

        self._init_masking_tables()

    def _init_masking_tables(self) -> None:
        """Create masking metadata tables."""
        tables = [
            # Masking rules
            """CREATE TABLE IF NOT EXISTS _masking_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT NOT NULL,
                column_name TEXT NOT NULL,
                strategy TEXT NOT NULL,
                roles TEXT,
                parameters TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                UNIQUE(table_name, column_name)
            )""",
        ]

        for sql in tables:
            self._conn.execute(sql)

        self._conn.commit()

    def register_strategy(self, name: str,
                          strategy: Callable[[Any], Any]) -> None:
        """
        Register a custom masking strategy.

        Args:
            name: Strategy name
            strategy: Function that takes value and returns masked value

        Example:
            register_strategy("email", lambda x: x.split('@')[0][:2] + '***@' + x.split('@')[1])
        """
        self._custom_strategies[name] = strategy

    def create_rule(self, table_name: str, column_name: str,
                    strategy: str, roles: Optional[List[str]] = None,
                    parameters: Optional[Dict] = None) -> None:
        """
        Create a masking rule.

        Args:
            table_name: Table name
            column_name: Column to mask
            strategy: Masking strategy name
            roles: Roles that see masked data (None for all except admins)
            parameters: Strategy-specific parameters

        Example:
            create_rule("users", "ssn", "partial", roles=["clerk"], parameters={"show": 2})
        """
        if strategy not in self.MASK_STRATEGIES and strategy not in self._custom_strategies:
            raise ValueError(f"Unknown masking strategy: {strategy}")

        self._conn.execute(
            """INSERT OR REPLACE INTO _masking_rules 
               (table_name, column_name, strategy, roles, parameters)
               VALUES (?, ?, ?, ?, ?)""",
            (table_name, column_name, strategy,
             json.dumps(roles) if roles else None,
             json.dumps(parameters) if parameters else None)
        )
        self._conn.commit()

    def _apply_mask(self, value: Any, strategy: str,
                    parameters: Optional[Dict] = None) -> Any:
        """Apply masking strategy to a value."""
        if value is None:
            return None

        if strategy in self._custom_strategies:
            return self._custom_strategies[strategy](value)

        if strategy in self.MASK_STRATEGIES:
            mask_func = self.MASK_STRATEGIES[strategy]
            if parameters:
                return mask_func(value, **parameters)
            return mask_func(value)

        return value

    def mask_row(self, table_name: str, row: Dict,
                 user_role: Optional[str] = None) -> Dict:
        """
        Apply masking rules to a row.

        Args:
            table_name: Table name
            row: Row data
            user_role: User's role (None for default masking)

        Returns:
            Row with masked columns
        """
        if table_name not in self._masking_rules:
            self._load_rules(table_name)

        if table_name not in self._masking_rules:
            return row

        masked_row = row.copy()

        for column_name, rule in self._masking_rules[table_name].items():
            # Check if rule applies to this role
            if rule.get("roles") and user_role not in rule["roles"]:
                continue

            if column_name in row:
                masked_row[column_name] = self._apply_mask(
                    row[column_name],
                    rule["strategy"],
                    rule.get("parameters")
                )

        return masked_row

    def _load_rules(self, table_name: str) -> None:
        """Load masking rules for a table."""
        cursor = self._conn.execute(
            "SELECT * FROM _masking_rules WHERE table_name = ?",
            (table_name,)
        )

        rules = {}
        for row in cursor.fetchall():
            rule = dict(row)
            if rule.get("roles"):
                rule["roles"] = json.loads(rule["roles"])
            if rule.get("parameters"):
                rule["parameters"] = json.loads(rule["parameters"])

            rules[rule["column_name"]] = rule

        self._masking_rules[table_name] = rules

    def get_masking_rules(self, table_name: str) -> Dict:
        """Get all masking rules for a table."""
        if table_name not in self._masking_rules:
            self._load_rules(table_name)

        return self._masking_rules.get(table_name, {})


class AccessControlManager:
    """
    Unified access control manager combining RLS and masking.
    """

    def __init__(self, db_connection: sqlite3.Connection):
        """
        Initialize access control manager.

        Args:
            db_connection: SQLite database connection
        """
        self._conn = db_connection
        self.rls = RowLevelSecurity(db_connection)
        self.masking = DataMasking(db_connection)
        self._current_user: Optional[Dict] = None

    def set_user(self, user_name: str, role: str = None,
                 attributes: Dict = None) -> None:
        """
        Set current user context.

        Args:
            user_name: Username
            role: User's role
            attributes: Additional attributes
        """
        self._current_user = {
            "name": user_name,
            "role": role,
            "attributes": attributes or {}
        }

        # Set user in RLS
        self.rls.set_current_user(user_name, attributes)

    def apply_access_control(self, sql: str,
                             operation: str = "SELECT") -> str:
        """
        Apply access control to SQL query.

        Args:
            sql: Original SQL
            operation: SELECT, INSERT, UPDATE, or DELETE

        Returns:
            Modified SQL with access control
        """
        return self.rls.apply_policies(sql, operation)

    def filter_results(self, table_name: str,
                       results: List[Dict]) -> List[Dict]:
        """
        Apply masking to query results.

        Args:
            table_name: Table name
            results: Query results

        Returns:
            Masked results
        """
        role = self._current_user.get("role") if self._current_user else None
        return [self.masking.mask_row(table_name, row, role) for row in results]

    def check_permission(self, table_name: str,
                         operation: str = "SELECT") -> bool:
        """
        Check if user has permission.

        Args:
            table_name: Table to check
            operation: Operation type

        Returns:
            True if permitted
        """
        return self.rls.check_access(table_name, operation)


# Convenience decorators

def require_role(allowed_roles: List[str]):
    """
    Decorator to require specific roles.

    Usage:
        @require_role(["admin", "manager"])
        def delete_user(user_id):
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Get access control from args (usually self or first param)
            ac = None
            for arg in args:
                if isinstance(arg, AccessControlManager):
                    ac = arg
                    break

            if not ac:
                raise RuntimeError("AccessControlManager not found")

            user_role = ac._current_user.get("role") if ac._current_user else None

            if user_role not in allowed_roles:
                raise PermissionError(
                    f"Role '{user_role}' not permitted. "
                    f"Required roles: {allowed_roles}"
                )

            return func(*args, **kwargs)
        return wrapper
    return decorator


def audit_access(func):
    """
    Decorator to audit access.

    Usage:
        @audit_access
        def get_sensitive_data(user_id):
            ...
    """
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)

        # Log access (implementation depends on context)
        print(f"Audit: {func.__name__} accessed at {datetime.now().isoformat()}")

        return result
    return wrapper
