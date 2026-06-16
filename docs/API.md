# ULE Python API Reference

Complete reference for the ULE Python API.

## Connection

### Connect to Database

```python
from ule import connect

# Connect to existing database
db = connect("mydb.udb")

# Create new database if missing
db = connect("mydb.udb", create_if_missing=True)

# Connect with encryption password
db = connect("mydb.udb", password="secret")

# In-memory database
db = connect(":memory:")
```

### Close Connection

```python
db.close()
```

### Context Manager

```python
from ule import connect

with connect("mydb.udb") as db:
    db.execute("SELECT * FROM users")
# Connection automatically closed
```

---

## SQL Operations

### Execute Query

```python
# Create table
db.execute("CREATE TABLE users (id INTEGER, name TEXT, age INTEGER)")

# Insert data
db.execute("INSERT INTO users VALUES (1, 'Ali', 25)")
db.execute("INSERT INTO users VALUES (2, 'Sara', 30)")

# Select data
results = db.execute("SELECT * FROM users")
for row in results:
    print(row['name'], row['age'])

# Update data
db.execute("UPDATE users SET age = 26 WHERE id = 1")

# Delete data
db.execute("DELETE FROM users WHERE id = 2")
```

### Execute with Parameters

```python
# Parameterized insert (safe from SQL injection)
db.execute("INSERT INTO users VALUES (?, ?, ?)", (3, 'Ahmed', 28))

# Named parameters
db.execute("INSERT INTO users VALUES (:id, :name, :age)", 
           {"id": 4, "name": "Fatima", "age": 24})
```

### Fetch Methods

```python
# Fetch all rows
results = db.execute("SELECT * FROM users")

# Fetch one row
row = db.execute("SELECT * FROM users WHERE id = 1").fetchone()

# Fetch many rows
rows = db.execute("SELECT * FROM users").fetchmany(5)
```

---

## Document Operations (NoSQL)

### Push Document

```python
# Push to collection
doc_id = db.push("logs", {"level": "info", "msg": "App started"})
print(f"Document ID: {doc_id}")

# Push multiple documents
db.push("logs", {"level": "error", "msg": "Connection failed"})
db.push("logs", {"level": "warn", "msg": "High memory usage"})
```

### Find Documents

```python
# Find all documents
docs = db.find("logs")

# Find with filter
docs = db.find("logs", {"level": "error"})

# Find with limit
docs = db.find("logs", limit=10)

# Iterate results
for doc in docs:
    print(doc['level'], doc['msg'])
```

---

## Graph Operations

### Create Relationship

```python
# Link two nodes
db.link("users", "1", "users", "2", "FRIEND")

# Link with properties
db.link("users", "1", "orders", "99", "PURCHASED", 
        properties={"date": "2026-03-12", "amount": 100})
```

### Traverse Graph

```python
# Traverse from node
edges = db.traverse("users", "1", depth=2)

for edge in edges:
    print(f"{edge['from']} -> {edge['relation']} -> {edge['to']}")

# Traverse with relation filter
edges = db.traverse("users", "1", relation="FRIEND")
```

---

## Natural Language Query

### Basic Usage

```python
from ule.ai import NaturalLanguageQuery

# Initialize NLQ
nlq = NaturalLanguageQuery(db._conn)

# English query
results = nlq.ask("show all users", language="en")

# Urdu query
results = nlq.ask("تمام صارفین دکھائیں", language="ur")

# Chinese query
results = nlq.ask("显示所有用户", language="zh")
```

### Supported Languages

```python
languages = {
    "en": "English",
    "ur": "Urdu",
    "zh": "Chinese",
    "es": "Spanish",
    "fr": "French",
    "ru": "Russian",
    "ja": "Japanese",
    "ko": "Korean",
    "pt": "Portuguese",
}

for code, name in languages.items():
    print(f"{name}: {nlq.ask('show all users', language=code)}")
```

---

## Vector Operations

### Add Vectors

```python
from ule.engines import VectorEngine

vector_engine = VectorEngine(db._conn)

# Add vector with metadata
vector_engine.add("items", "item1", [0.1, 0.2, 0.3], {"name": "Product A"})
vector_engine.add("items", "item2", [0.1, 0.2, 0.35], {"name": "Product B"})
vector_engine.add("items", "item3", [0.9, 0.8, 0.7], {"name": "Product C"})
```

### Search Similar Vectors

```python
# Search by vector
results = vector_engine.search("items", [0.1, 0.2, 0.3], limit=5)

for result in results:
    print(f"ID: {result['vec_id']}, Similarity: {result['similarity']:.4f}")
```

### Generate Embeddings

```python
# Generate embedding for text
embedding = vector_engine.embed_text("Hello World")
print(f"Embedding dimensions: {len(embedding)}")
print(f"First 5 values: {embedding[:5]}")
```

---

## Blockchain Operations

### Verify Integrity

```python
# Verify database integrity
is_valid = db.verify()
print(f"Database valid: {is_valid}")
```

### View Audit Trail

```python
# Get audit trail
audit = db.audit()

for block in audit:
    print(f"Block {block['id']}: {block['operation']} at {block['timestamp']}")
```

---

## Statistics

### Get Database Stats

```python
# Get statistics
stats = db.stats()

print(f"Tables: {stats['tables']}")
print(f"Documents: {stats['documents']}")
print(f"Edges: {stats['edges']}")
print(f"Vectors: {stats['vectors']}")
print(f"Audit blocks: {stats['audit_blocks']}")
print(f"File size: {stats['size_bytes']} bytes")
```

---

## Security

### Digital Signatures

```python
from ule.security.signatures import DigitalSignature

# Create signature manager
sig = DigitalSignature(key_type="ed25519")

# Generate key pair
public_key, private_key = sig.generate_keypair()

# Sign a message
signature = sig.sign(b"Hello World", private_key)

# Verify signature
is_valid = sig.verify(b"Hello World", signature, public_key)
print(f"Signature valid: {is_valid}")
```

### Column Encryption

```python
from ule.security.column_encryption import ColumnEncryption

# Create encryption manager
enc = ColumnEncryption(db_path="mydb.udb")

# Enable encryption on a column
enc.enable_encryption("users", "ssn")

# Insert encrypted data
db.execute("INSERT INTO users (name, ssn) VALUES (?, ?)", 
          ("Alice", "123-45-6789"))
# SSN is automatically encrypted before storage

# Query encrypted data
results = db.execute("SELECT * FROM users WHERE name = 'Alice'")
# SSN is automatically decrypted when retrieved
```

### Access Control & Data Masking

```python
from ule.security.access_control import AccessControlManager, RowLevelSecurity, DataMasking

# Row-Level Security
rls = RowLevelSecurity(db._conn)
rls.create_policy("users", "department = ?", ("sales",))

# Apply policy to query
filtered = rls.apply_policy("SELECT * FROM users", "sales")

# Data Masking
masking = DataMasking()
masking.create_masking_rule("users", "email", "partial")
masked_data = masking.apply_mask("users", "email", "user@example.com")
print(masked_data)  # u***@example.com
```

---

## Complete Example

```python
#!/usr/bin/env python3
"""Complete ULE Demo"""

from ule import connect
from ule.ai import NaturalLanguageQuery
from ule.engines import VectorEngine

# Connect
db = connect("demo.udb", create_if_missing=True)

# SQL
db.execute("CREATE TABLE users (id INTEGER, name TEXT, age INTEGER)")
db.execute("INSERT INTO users VALUES (1, 'Ali', 25)")
db.execute("INSERT INTO users VALUES (2, 'Sara', 30)")
print("Users:", db.execute("SELECT * FROM users"))

# Documents
db.push("logs", {"level": "info", "msg": "App started"})
print("Logs:", db.find("logs"))

# Graph
db.link("users", "1", "users", "2", "FRIEND")
print("Connections:", db.traverse("users", "1"))

# Natural Language
nlq = NaturalLanguageQuery(db._conn)
print("NLQ:", nlq.ask("count all users", language="en"))

# Vectors
ve = VectorEngine(db._conn)
ve.add("items", "item1", [0.1, 0.2, 0.3], {"name": "Product A"})
print("Similar:", ve.search("items", [0.1, 0.2, 0.3]))

# Blockchain
print("Verify:", db.verify())
print("Audit blocks:", len(db.audit()))

# Stats
print("Stats:", db.stats())

db.close()
```

---

## Error Handling

```python
from ule import connect
from ule.core.exceptions import (
    DatabaseError,
    AuthenticationError,
)

try:
    db = connect("mydb.udb")
    db.execute("INVALID SQL QUERY")
except DatabaseError as e:
    print(f"Database error: {e}")
except AuthenticationError as e:
    print(f"Authentication error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
finally:
    db.close()
```
