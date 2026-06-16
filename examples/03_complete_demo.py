#!/usr/bin/env python3
"""
ULE Complete Demo - All Features

Run: python examples/03_complete_demo.py
"""

from ule import connect
from ule.ai import NaturalLanguageQuery
from ule.engines import VectorEngine

# Create fresh database
db = connect("complete_demo.udb", create_if_missing=True)

print("=" * 60)
print("ULE Complete Demo - All Features")
print("=" * 60)

# ============================================
# 1. SQL OPERATIONS
# ============================================
print("\n" + "=" * 60)
print("1. SQL OPERATIONS")
print("=" * 60)

# Create tables
print("\nCreating tables...")
db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER, name TEXT, age INTEGER, email TEXT)")
db.execute("CREATE TABLE IF NOT EXISTS orders (id INTEGER, user_id INTEGER, product TEXT, amount REAL)")
print("✓ Tables created: users, orders")

# Insert data
print("\nInserting data...")
db.execute("INSERT INTO users VALUES (1, 'Ali', 25, 'ali@example.com')")
db.execute("INSERT INTO users VALUES (2, 'Sara', 30, 'sara@example.com')")
db.execute("INSERT INTO users VALUES (3, 'Ahmed', 28, 'ahmed@example.com')")
db.execute("INSERT INTO users VALUES (4, 'Fatima', 24, 'fatima@example.com')")

db.execute("INSERT INTO orders VALUES (1, 1, 'Laptop', 999.99)")
db.execute("INSERT INTO orders VALUES (2, 1, 'Mouse', 29.99)")
db.execute("INSERT INTO orders VALUES (3, 2, 'Keyboard', 79.99)")
db.execute("INSERT INTO orders VALUES (4, 3, 'Monitor', 299.99)")
print("✓ Data inserted: 4 users, 4 orders")

# Query with JOIN
print("\nQuery with JOIN...")
results = db.execute("""
    SELECT u.name, o.product, o.amount 
    FROM users u 
    JOIN orders o ON u.id = o.user_id
""")
for row in results:
    print(f"   {row['name']}: {row['product']} (${row['amount']})")

# ============================================
# 2. DOCUMENT OPERATIONS (NoSQL)
# ============================================
print("\n" + "=" * 60)
print("2. DOCUMENT OPERATIONS (NoSQL)")
print("=" * 60)

# Push documents
print("\nPushing documents...")
doc1 = db.push("logs", {"level": "info", "msg": "Application started", "timestamp": "2026-03-12T10:00:00"})
doc2 = db.push("logs", {"level": "info", "msg": "User logged in", "user": "ali"})
doc3 = db.push("logs", {"level": "error", "msg": "Database connection timeout", "retry": 3})
doc4 = db.push("logs", {"level": "warn", "msg": "High memory usage", "percent": 85})
print(f"✓ Documents pushed with IDs: {doc1}, {doc2}, {doc3}, {doc4}")

# Find documents
print("\nFinding documents...")
all_logs = db.find("logs")
print(f"   All logs: {len(all_logs)} documents")

error_logs = db.find("logs", {"level": "error"})
print(f"   Error logs: {len(error_logs)} documents")

# ============================================
# 3. GRAPH OPERATIONS
# ============================================
print("\n" + "=" * 60)
print("3. GRAPH OPERATIONS")
print("=" * 60)

# Create relationships
print("\nCreating relationships...")
db.link("users", "1", "users", "2", "FRIEND")
db.link("users", "1", "users", "3", "COLLEAGUE")
db.link("users", "2", "users", "4", "SIBLING")
db.link("users", "1", "orders", "1", "PURCHASED")
db.link("users", "1", "orders", "2", "PURCHASED")
print("✓ 5 relationships created")

# Traverse graph
print("\nTraversing graph from user 1...")
edges = db.traverse("users", "1", depth=2)
for edge in edges:
    print(f"   {edge['from']} → {edge['relation']} → {edge['to']}")

# ============================================
# 4. VECTOR OPERATIONS
# ============================================
print("\n" + "=" * 60)
print("4. VECTOR OPERATIONS")
print("=" * 60)

# Initialize vector engine
vector_engine = VectorEngine(db._conn)

# Add vectors
print("\nAdding vectors...")
vector_engine.add("products", "p1", [0.1, 0.2, 0.3], {"name": "Laptop", "category": "Electronics"})
vector_engine.add("products", "p2", [0.1, 0.2, 0.35], {"name": "Mouse", "category": "Electronics"})
vector_engine.add("products", "p3", [0.9, 0.8, 0.7], {"name": "Desk Chair", "category": "Furniture"})
vector_engine.add("products", "p4", [0.85, 0.8, 0.75], {"name": "Desk", "category": "Furniture"})
print("✓ 4 product vectors added")

# Search similar vectors
print("\nSearching for products similar to [0.1, 0.2, 0.3]...")
results = vector_engine.search("products", [0.1, 0.2, 0.3], limit=3)
for result in results:
    print(f"   {result['vec_id']}: similarity={result['similarity']:.4f}")

# Generate text embedding
print("\nGenerating text embedding...")
embedding = vector_engine.embed_text("Hello World")
print(f"✓ Embedding generated: {len(embedding)} dimensions")
print(f"   First 5 values: {embedding[:5]}")

# ============================================
# 5. NATURAL LANGUAGE QUERIES
# ============================================
print("\n" + "=" * 60)
print("5. NATURAL LANGUAGE QUERIES")
print("=" * 60)

nlq = NaturalLanguageQuery(db._conn)

# English
print("\nEnglish queries:")
queries_en = [
    "show all users",
    "count all users",
    "show tables",
]
for q in queries_en:
    print(f"   '{q}'")
    results = nlq.ask(q, language="en")
    if isinstance(results, list):
        print(f"      → {len(results)} rows")
    else:
        print(f"      → {results}")

# Urdu
print("\nUrdu queries:")
queries_ur = [
    "تمام صارفین دکھائیں",
    "صارفین کی تعداد دکھائیں",
]
for q in queries_ur:
    print(f"   '{q}'")
    results = nlq.ask(q, language="ur")
    if isinstance(results, list):
        print(f"      → {len(results)} rows")
    else:
        print(f"      → {results}")

# Chinese
print("\nChinese queries:")
print("   '显示所有用户'")
results = nlq.ask("显示所有用户", language="zh")
print(f"      → {len(results)} rows")

# ============================================
# 6. BLOCKCHAIN OPERATIONS
# ============================================
print("\n" + "=" * 60)
print("6. BLOCKCHAIN OPERATIONS")
print("=" * 60)

# Verify integrity
print("\nVerifying database integrity...")
is_valid = db.verify()
print(f"✓ Integrity check: {'PASSED' if is_valid else 'FAILED'}")

# View audit trail
print("\nRecent audit trail:")
audit = db.audit()
print(f"   Total audit blocks: {len(audit)}")
print("   Last 5 operations:")
for block in audit[-5:]:
    print(f"      [{block['id']}] {block['operation']} at {block['timestamp']}")

# ============================================
# 7. STATISTICS
# ============================================
print("\n" + "=" * 60)
print("7. DATABASE STATISTICS")
print("=" * 60)

tables = db.execute("SELECT COUNT(*) as count FROM _tables")[0]['count']
docs = db.execute("SELECT COUNT(*) as count FROM _documents")[0]['count']
edges = db.execute("SELECT COUNT(*) as count FROM _edges")[0]['count']
vectors = db.execute("SELECT COUNT(*) as count FROM _vectors")[0]['count']
audit = db.execute("SELECT COUNT(*) as count FROM _audit")[0]['count']

import os
file_size = os.path.getsize("complete_demo.udb")

print(f"""
   Tables:         {tables}
   Documents:      {docs}
   Graph Edges:    {edges}
   Vectors:        {vectors}
   Audit Blocks:   {audit}
   File Size:      {file_size:,} bytes
""")

# ============================================
# CLEANUP
# ============================================
db.close()

print("=" * 60)
print("✓ COMPLETE DEMO FINISHED!")
print("=" * 60)
