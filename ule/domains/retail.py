"""Retail Domain Model for ULE.

Retail management data model with:
- Products inventory
- Customers
- Orders
- Order items
- Suppliers
"""

import sqlite3
from datetime import datetime
from typing import Optional, Dict, List, Any


class RetailModel:
    """Retail domain model."""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn
        self._create_tables()

    def _create_tables(self):
        """Create retail tables."""
        tables = [
            """CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                category TEXT,
                price REAL NOT NULL,
                cost REAL,
                stock_quantity INTEGER DEFAULT 0,
                reorder_level INTEGER DEFAULT 10,
                sku TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )""",

            """CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id TEXT UNIQUE NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                address TEXT,
                loyalty_points INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now'))
            )""",

            """CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                contact_person TEXT,
                phone TEXT,
                email TEXT,
                address TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )""",

            """CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT UNIQUE NOT NULL,
                customer_id TEXT NOT NULL,
                order_date TEXT NOT NULL,
                status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'processing', 'shipped', 'delivered', 'cancelled')),
                total_amount REAL DEFAULT 0.0,
                shipping_address TEXT,
                notes TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
            )""",

            """CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id TEXT UNIQUE NOT NULL,
                order_id TEXT NOT NULL,
                product_id TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                total_price REAL NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (order_id) REFERENCES orders(order_id),
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            )""",

            """CREATE TABLE IF NOT EXISTS inventory_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT UNIQUE NOT NULL,
                product_id TEXT NOT NULL,
                transaction_type TEXT CHECK(transaction_type IN ('in', 'out', 'adjustment')),
                quantity INTEGER NOT NULL,
                reference TEXT,
                transaction_date TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            )""",
        ]

        for table_sql in tables:
            self._conn.execute(table_sql)
        self._conn.commit()

    def add_product(self, **kwargs) -> str:
        """Add a new product."""
        import uuid
        product_id = f"PRD-{uuid.uuid4().hex[:8].upper()}"
        
        self._conn.execute(
            """INSERT INTO products (product_id, name, description, category, price,
               cost, stock_quantity, reorder_level, sku)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (product_id, kwargs.get('name'), kwargs.get('description'),
             kwargs.get('category'), kwargs.get('price'), kwargs.get('cost'),
             kwargs.get('stock_quantity', 0), kwargs.get('reorder_level', 10),
             kwargs.get('sku'))
        )
        self._conn.commit()
        return product_id

    def add_customer(self, **kwargs) -> str:
        """Add a new customer."""
        import uuid
        customer_id = f"CUST-{uuid.uuid4().hex[:8].upper()}"
        
        self._conn.execute(
            """INSERT INTO customers (customer_id, first_name, last_name, email, phone, address)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (customer_id, kwargs.get('first_name'), kwargs.get('last_name'),
             kwargs.get('email'), kwargs.get('phone'), kwargs.get('address'))
        )
        self._conn.commit()
        return customer_id

    def add_supplier(self, **kwargs) -> str:
        """Add a new supplier."""
        import uuid
        supplier_id = f"SUP-{uuid.uuid4().hex[:8].upper()}"
        
        self._conn.execute(
            """INSERT INTO suppliers (supplier_id, name, contact_person, phone, email, address)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (supplier_id, kwargs.get('name'), kwargs.get('contact_person'),
             kwargs.get('phone'), kwargs.get('email'), kwargs.get('address'))
        )
        self._conn.commit()
        return supplier_id

    def create_order(self, customer_id: str, items: List[Dict], **kwargs) -> str:
        """Create a new order with items."""
        import uuid
        order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        
        # Create order
        self._conn.execute(
            """INSERT INTO orders (order_id, customer_id, order_date, status, shipping_address, notes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (order_id, customer_id, datetime.now().isoformat(),
             kwargs.get('status', 'pending'), kwargs.get('shipping_address'),
             kwargs.get('notes'))
        )
        
        # Add order items
        total_amount = 0.0
        for item in items:
            item_id = f"ITM-{uuid.uuid4().hex[:8].upper()}"
            quantity = item['quantity']
            unit_price = item['unit_price']
            total_price = quantity * unit_price
            total_amount += total_price
            
            self._conn.execute(
                """INSERT INTO order_items (item_id, order_id, product_id, quantity,
                   unit_price, total_price)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (item_id, order_id, item['product_id'], quantity, unit_price, total_price)
            )
            
            # Update stock
            self._conn.execute(
                "UPDATE products SET stock_quantity = stock_quantity - ?, updated_at = datetime('now') WHERE product_id = ?",
                (quantity, item['product_id'])
            )
        
        # Update order total
        self._conn.execute(
            "UPDATE orders SET total_amount = ? WHERE order_id = ?",
            (total_amount, order_id)
        )
        self._conn.commit()
        return order_id

    def update_stock(self, product_id: str, quantity: int, 
                    trans_type: str = 'in', **kwargs) -> str:
        """Update product stock."""
        import uuid
        transaction_id = f"INV-{uuid.uuid4().hex[:8].upper()}"
        
        self._conn.execute(
            """INSERT INTO inventory_transactions (transaction_id, product_id,
               transaction_type, quantity, reference, transaction_date)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (transaction_id, product_id, trans_type, quantity,
             kwargs.get('reference'), datetime.now().isoformat())
        )
        
        if trans_type == 'in':
            self._conn.execute(
                "UPDATE products SET stock_quantity = stock_quantity + ?, updated_at = datetime('now') WHERE product_id = ?",
                (quantity, product_id)
            )
        else:
            self._conn.execute(
                "UPDATE products SET stock_quantity = stock_quantity - ?, updated_at = datetime('now') WHERE product_id = ?",
                (quantity, product_id)
            )
        self._conn.commit()
        return transaction_id

    def get_low_stock_products(self) -> List[Dict]:
        """Get products below reorder level."""
        cursor = self._conn.execute(
            "SELECT * FROM products WHERE stock_quantity <= reorder_level"
        )
        return [dict(zip([d[0] for d in cursor.description], row)) for row in cursor.fetchall()]

    def get_retail_summary(self) -> Dict[str, Any]:
        """Get retail summary."""
        return {
            'total_products': self._conn.execute("SELECT COUNT(*) FROM products").fetchone()[0],
            'total_customers': self._conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0],
            'total_orders': self._conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0],
            'total_suppliers': self._conn.execute("SELECT COUNT(*) FROM suppliers").fetchone()[0],
            'low_stock_items': self._conn.execute("SELECT COUNT(*) FROM products WHERE stock_quantity <= reorder_level").fetchone()[0],
            'total_revenue': self._conn.execute("SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE status='delivered'").fetchone()[0],
            'generated_at': datetime.now().isoformat()
        }
