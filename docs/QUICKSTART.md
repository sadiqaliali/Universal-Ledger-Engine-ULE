# ULE Quick Start Guide

Get up and running with ULE in 5 minutes!

## Installation

```bash
pip install ule-db
```

Or install from source:
```bash
git clone https://github.com/ule-db/ule.git
cd ule
pip install -e .
```

## Create Your First Database

```bash
# Initialize a new database via the Professional Setup Wizard
ule init mydb.udb
```

The **ULE Setup Wizard** will guide you through:
1. Setting a **mandatory** unique admin password (minimum 8 characters).
2. Configuring **Blockchain Audit Trail** (Enabled by default).
3. Enabling **Write-Ahead Logging (WAL)** for concurrency.
4. Optional **Quantum Simulation Engine** activation.

> **Note:** There are no default passwords. Keep your chosen password safe as it is required for all UI access and encryption keys.

## Run Your First Query

```bash
# Create a table
ule query mydb.udb "CREATE TABLE users (id INTEGER, name TEXT, age INTEGER)"

# Insert data
ule query mydb.udb "INSERT INTO users VALUES (1, 'Ali', 25)"
ule query mydb.udb "INSERT INTO users VALUES (2, 'Sara', 30)"

# Query data
ule query mydb.udb "SELECT * FROM users"
```

## Try Natural Language Queries

Ask questions in plain English:

```bash
ule ask mydb.udb "show all users"
ule ask mydb.udb "count all users"
ule ask mydb.udb "show tables"
```

Try other languages:

```bash
# Urdu
ule ask mydb.udb "تمام صارفین دکھائیں" -l ur

# Chinese
ule ask mydb.udb "显示所有用户" -l zh

# Spanish
ule ask mydb.udb "mostrar todos los usuarios" -l es
```

## Store Documents

```bash
# Push a document
ule push mydb.udb -c logs -d '{"level":"info","msg":"App started"}'

# Find documents
ule find mydb.udb -c logs
```

## Create Graph Relationships

```bash
# Link nodes
ule link mydb.udb --from users --from-id 1 --to users --to-id 2 --relation FRIEND

# Traverse graph
ule traverse mydb.udb --table users --id 1 --depth 2
```

## Check Statistics

```bash
ule stats mydb.udb
```

## Verify Database Integrity

```bash
ule verify mydb.udb
ule audit mydb.udb
```

## Next Steps

- Read the full [CLI Reference](CLI.md)
- Learn the [Python API](API.md)
- Check out [examples/](../examples/) for more code samples
