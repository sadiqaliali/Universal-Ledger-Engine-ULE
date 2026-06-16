#!/usr/bin/env python3
"""
ULE Quick Start - 5 minute demo

Run: python examples/01_quickstart.py
"""

from ule import connect

# Create/connect to database
db = connect("quickstart.udb", create_if_missing=True)

print("=" * 50)
print("ULE Quick Start Demo")
print("=" * 50)

# Create table
print("\n1. Creating table...")
db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER, name TEXT, age INTEGER)")
print("   ✓ Table 'users' created")

# Insert data
print("\n2. Inserting data...")
db.execute("INSERT INTO users VALUES (1, 'Ali', 25)")
db.execute("INSERT INTO users VALUES (2, 'Sara', 30)")
db.execute("INSERT INTO users VALUES (3, 'Ahmed', 28)")
print("   ✓ 3 users inserted")

# Query data
print("\n3. Querying data...")
results = db.execute("SELECT * FROM users")
print("   All users:")
for row in results:
    print(f"      {row['id']}: {row['name']} (age {row['age']})")

# Query with condition
print("\n4. Query with condition...")
results = db.execute("SELECT * FROM users WHERE age > 25")
print("   Users older than 25:")
for row in results:
    print(f"      {row['name']} - age {row['age']}")

# Natural language query
print("\n5. Natural language query...")
from ule.ai import NaturalLanguageQuery
nlq = NaturalLanguageQuery(db._conn)

results = nlq.ask("count all users", language="en")
print(f"   'count all users' → {results}")

results = nlq.ask("show all users", language="en")
print(f"   'show all users' → {len(results)} rows")

# Add documents
print("\n6. Document operations...")
db.push("logs", {"level": "info", "msg": "Application started"})
db.push("logs", {"level": "info", "msg": "User logged in"})
db.push("logs", {"level": "error", "msg": "Connection timeout"})

docs = db.find("logs")
print(f"   ✓ {len(docs)} log documents added")

# Graph relationships
print("\n7. Graph operations...")
db.link("users", "1", "users", "2", "FRIEND")
db.link("users", "1", "users", "3", "COLLEAGUE")

connections = db.traverse("users", "1", depth=2)
print(f"   ✓ {len(connections)} connections from user 1")

# Blockchain verify
print("\n8. Blockchain verification...")
is_valid = db.verify()
print(f"   ✓ Database integrity: {'Valid' if is_valid else 'Invalid'}")

# Statistics
print("\n9. Database statistics...")
tables = db.execute("SELECT COUNT(*) as count FROM _tables")[0]['count']
docs = db.execute("SELECT COUNT(*) as count FROM _documents")[0]['count']
edges = db.execute("SELECT COUNT(*) as count FROM _edges")[0]['count']
audit = db.execute("SELECT COUNT(*) as count FROM _audit")[0]['count']
print(f"   Tables: {tables}")
print(f"   Documents: {docs}")
print(f"   Edges: {edges}")
print(f"   Audit blocks: {audit}")

db.close()

print("\n" + "=" * 50)
print("✓ Quick Start Complete!")
print("=" * 50)
