#!/usr/bin/env python3
"""
ULE Python SDK Examples

Run: python examples/01_basic.py
"""

from ule import connect, ULEDatabase
from ule.ai.nlq import NaturalLanguageQuery

# ============ BASIC USAGE ============

# Create/connect to database
db = connect("demo.udb", create_if_missing=True)

# ============ SQL ============
print("=" * 50)
print("SQL EXAMPLES")
print("=" * 50)

# Create table
db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
print("✓ Table created")

# Insert data
db.execute("INSERT INTO users (name, age) VALUES (?, ?)", ("Ali", 25))
db.execute("INSERT INTO users (name, age) VALUES (?, ?)", ("Sara", 30))
db.execute("INSERT INTO users (name, age) VALUES (?, ?)", ("Ahmed", 22))
print("✓ Data inserted")

# Query data
results = db.execute("SELECT * FROM users")
print(f"\nAll users ({len(results)} rows):")
for row in results:
    print(f"  {row['id']}: {row['name']} (age {row['age']})")

# Query with condition
results = db.execute("SELECT * FROM users WHERE age > ?", (23,))
print(f"\nUsers older than 23 ({len(results)} rows):")
for row in results:
    print(f"  {row['name']} - age {row['age']}")

# ============ DOCUMENTS ============
print("\n" + "=" * 50)
print("DOCUMENT EXAMPLES")
print("=" * 50)

# Push documents
doc_id = db.push("logs", {"level": "info", "msg": "App started"})
print(f"✓ Document pushed: {doc_id}")

db.push("logs", {"level": "error", "msg": "Connection failed"})
db.push("logs", {"level": "warn", "msg": "High memory usage"})

# Find documents
docs = db.find("logs")
print(f"\nAll logs ({len(docs)} documents):")
for doc in docs:
    print(f"  [{doc.get('level')}] {doc.get('msg')}")

# ============ GRAPH ============
print("\n" + "=" * 50)
print("GRAPH EXAMPLES")
print("=" * 50)

# Create relationships
db.link("users", "1", "users", "2", "FRIEND")
db.link("users", "1", "users", "3", "COLLEAGUE")
print("✓ Relationships created")

# Traverse graph
edges = db.traverse("users", "1", depth=2)
print(f"\nConnections from user 1 ({len(edges)} edges):")
for edge in edges:
    print(f"  {edge['from']} → {edge['relation']} → {edge['to']}")

# ============ NATURAL LANGUAGE ============
print("\n" + "=" * 50)
print("NATURAL LANGUAGE EXAMPLES")
print("=" * 50)

nlq = NaturalLanguageQuery(db._conn)

# English
print("\nEnglish: 'show all users'")
results = nlq.ask("show all users", language="en")
for row in results:
    print(f"  {row['name']}")

# Urdu
print("\nUrdu: 'تمام صارفین دکھائیں'")
results = nlq.ask("تمام صارفین دکھائیں", language="ur")
for row in results:
    print(f"  {row['name']}")

# Chinese
print("\nChinese: '显示所有用户'")
results = nlq.ask("显示所有用户", language="zh")
for row in results:
    print(f"  {row['name']}")

# ============ VECTOR ============
print("\n" + "=" * 50)
print("VECTOR EXAMPLES")
print("=" * 50)

from ule.engines.vector_engine import VectorEngine

engine = VectorEngine(db._conn)

# Add vectors
engine.add("items", "item1", [0.1, 0.2, 0.3], {"name": "Product A"})
engine.add("items", "item2", [0.1, 0.2, 0.35], {"name": "Product B"})
engine.add("items", "item3", [0.9, 0.8, 0.7], {"name": "Product C"})
print("✓ Vectors added")

# Search similar vectors
results = engine.search("items", [0.1, 0.2, 0.3], limit=5)
print(f"\nSimilar to [0.1, 0.2, 0.3]:")
for result in results:
    print(f"  {result['vec_id']}: similarity={result['similarity']:.4f}")

# Text embedding
embedding = engine.embed_text("Hello World")
print(f"\nEmbedding for 'Hello World': {len(embedding)} dimensions")
print(f"  First 5 values: {embedding[:5]}")

# ============ BLOCKCHAIN ============
print("\n" + "=" * 50)
print("BLOCKCHAIN EXAMPLES")
print("=" * 50)

# Verify integrity
is_valid = db.verify()
print(f"Database integrity: {'✓ Valid' if is_valid else '✗ Invalid'}")

# View audit trail
audit = db.audit()
print(f"\nAudit trail: {len(audit)} blocks")

# ============ STATS ============
print("\n" + "=" * 50)
print("DATABASE STATS")
print("=" * 50)

tables = db.execute("SELECT COUNT(*) as count FROM _tables")
print(f"Tables: {tables[0]['count']}")

docs = db.execute("SELECT COUNT(*) as count FROM _documents")
print(f"Documents: {docs[0]['count']}")

edges = db.execute("SELECT COUNT(*) as count FROM _edges")
print(f"Graph edges: {edges[0]['count']}")

vectors = db.execute("SELECT COUNT(*) as count FROM _vectors")
print(f"Vectors: {vectors[0]['count']}")

audit = db.execute("SELECT COUNT(*) as count FROM _audit")
print(f"Audit blocks: {audit[0]['count']}")

# Cleanup
db.close()

print("\n" + "=" * 50)
print("✓ All examples completed!")
print("=" * 50)
