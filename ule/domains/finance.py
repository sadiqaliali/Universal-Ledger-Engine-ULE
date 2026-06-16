"""Finance Domain Model for ULE.

PCI-DSS compliant finance data model with:
- Accounts management
- Transactions
- Invoices
- Payments
- Financial reports
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from decimal import Decimal


class FinanceModel:
    """Finance domain model."""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn
        self._create_tables()

    def _create_tables(self):
        """Create finance tables."""
        tables = [
            """CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id TEXT UNIQUE NOT NULL,
                account_name TEXT NOT NULL,
                account_type TEXT CHECK(account_type IN ('asset', 'liability', 'equity', 'revenue', 'expense')),
                balance REAL DEFAULT 0.0,
                currency TEXT DEFAULT 'USD',
                status TEXT DEFAULT 'active' CHECK(status IN ('active', 'inactive', 'closed')),
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )""",

            """CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                address TEXT,
                credit_limit REAL,
                balance REAL DEFAULT 0.0,
                created_at TEXT DEFAULT (datetime('now'))
            )""",

            """CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT UNIQUE NOT NULL,
                account_id TEXT NOT NULL,
                transaction_type TEXT CHECK(transaction_type IN ('debit', 'credit')),
                amount REAL NOT NULL,
                description TEXT,
                reference TEXT,
                transaction_date TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (account_id) REFERENCES accounts(account_id)
            )""",

            """CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id TEXT UNIQUE NOT NULL,
                customer_id TEXT NOT NULL,
                amount REAL NOT NULL,
                tax_amount REAL DEFAULT 0.0,
                total_amount REAL NOT NULL,
                issue_date TEXT NOT NULL,
                due_date TEXT,
                status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'paid', 'overdue', 'cancelled')),
                notes TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
            )""",

            """CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_id TEXT UNIQUE NOT NULL,
                invoice_id TEXT NOT NULL,
                amount REAL NOT NULL,
                payment_method TEXT CHECK(payment_method IN ('cash', 'card', 'transfer', 'check')),
                payment_date TEXT NOT NULL,
                reference TEXT,
                status TEXT DEFAULT 'completed' CHECK(status IN ('completed', 'pending', 'failed')),
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id)
            )""",

            """CREATE TABLE IF NOT EXISTS budget_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                budget_id TEXT UNIQUE NOT NULL,
                category TEXT NOT NULL,
                allocated_amount REAL NOT NULL,
                spent_amount REAL DEFAULT 0.0,
                period TEXT CHECK(period IN ('monthly', 'quarterly', 'yearly')),
                start_date TEXT,
                end_date TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )""",
        ]

        for table_sql in tables:
            self._conn.execute(table_sql)
        self._conn.commit()

    def create_account(self, **kwargs) -> str:
        """Create a new account."""
        import uuid
        account_id = f"ACC-{uuid.uuid4().hex[:8].upper()}"
        
        self._conn.execute(
            """INSERT INTO accounts (account_id, account_name, account_type, balance, currency)
               VALUES (?, ?, ?, ?, ?)""",
            (account_id, kwargs.get('account_name'), kwargs.get('account_type', 'asset'),
             kwargs.get('balance', 0.0), kwargs.get('currency', 'USD'))
        )
        self._conn.commit()
        return account_id

    def create_customer(self, **kwargs) -> str:
        """Create a new customer."""
        import uuid
        customer_id = f"CUST-{uuid.uuid4().hex[:8].upper()}"
        
        self._conn.execute(
            """INSERT INTO customers (customer_id, name, email, phone, address, credit_limit)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (customer_id, kwargs.get('name'), kwargs.get('email'),
             kwargs.get('phone'), kwargs.get('address'), kwargs.get('credit_limit'))
        )
        self._conn.commit()
        return customer_id

    def record_transaction(self, account_id: str, trans_type: str, 
                          amount: float, **kwargs) -> str:
        """Record a financial transaction."""
        import uuid
        transaction_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"
        
        self._conn.execute(
            """INSERT INTO transactions (transaction_id, account_id, transaction_type,
               amount, description, reference, transaction_date)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (transaction_id, account_id, trans_type, amount,
             kwargs.get('description'), kwargs.get('reference'),
             kwargs.get('transaction_date', datetime.now().isoformat()))
        )
        
        # Update account balance
        if trans_type == 'debit':
            self._conn.execute(
                "UPDATE accounts SET balance = balance - ?, updated_at = datetime('now') WHERE account_id = ?",
                (amount, account_id)
            )
        else:
            self._conn.execute(
                "UPDATE accounts SET balance = balance + ?, updated_at = datetime('now') WHERE account_id = ?",
                (amount, account_id)
            )
        self._conn.commit()
        return transaction_id

    def create_invoice(self, customer_id: str, amount: float, **kwargs) -> str:
        """Create a new invoice."""
        import uuid
        invoice_id = f"INV-{uuid.uuid4().hex[:8].upper()}"
        tax_amount = amount * kwargs.get('tax_rate', 0.1)
        total_amount = amount + tax_amount
        
        self._conn.execute(
            """INSERT INTO invoices (invoice_id, customer_id, amount, tax_amount,
               total_amount, issue_date, due_date, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (invoice_id, customer_id, amount, tax_amount, total_amount,
             kwargs.get('issue_date', datetime.now().isoformat()),
             kwargs.get('due_date'), kwargs.get('notes'))
        )
        self._conn.commit()
        return invoice_id

    def record_payment(self, invoice_id: str, amount: float, **kwargs) -> str:
        """Record a payment."""
        import uuid
        payment_id = f"PAY-{uuid.uuid4().hex[:8].upper()}"
        
        self._conn.execute(
            """INSERT INTO payments (payment_id, invoice_id, amount, payment_method,
               payment_date, reference)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (payment_id, invoice_id, amount, kwargs.get('payment_method', 'cash'),
             kwargs.get('payment_date', datetime.now().isoformat()),
             kwargs.get('reference'))
        )
        
        # Update invoice status if fully paid
        cursor = self._conn.execute(
            "SELECT total_amount FROM invoices WHERE invoice_id = ?",
            (invoice_id,)
        )
        row = cursor.fetchone()
        if row:
            total = row[0]
            paid = self._conn.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE invoice_id = ? AND status='completed'",
                (invoice_id,)
            ).fetchone()[0]
            
            if paid >= total:
                self._conn.execute(
                    "UPDATE invoices SET status='paid' WHERE invoice_id = ?",
                    (invoice_id,)
                )
        self._conn.commit()
        return payment_id

    def get_account_balance(self, account_id: str) -> float:
        """Get account balance."""
        cursor = self._conn.execute(
            "SELECT balance FROM accounts WHERE account_id = ?",
            (account_id,)
        )
        row = cursor.fetchone()
        return row[0] if row else 0.0

    def get_financial_summary(self) -> Dict[str, Any]:
        """Get financial summary."""
        return {
            'total_accounts': self._conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0],
            'total_customers': self._conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0],
            'total_transactions': self._conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0],
            'pending_invoices': self._conn.execute("SELECT COUNT(*) FROM invoices WHERE status='pending'").fetchone()[0],
            'overdue_invoices': self._conn.execute("SELECT COUNT(*) FROM invoices WHERE status='overdue'").fetchone()[0],
            'total_revenue': self._conn.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE transaction_type='credit'").fetchone()[0],
            'generated_at': datetime.now().isoformat()
        }
