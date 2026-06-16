# ULE CLI Reference

Complete reference for all ULE command-line commands.

## Usage

```bash
ule [COMMAND] [OPTIONS] [ARGS]
```

## Commands

### `ule init` - Professional Setup Wizard

Initialize a new ULE database with a guided security setup.

```bash
# Launch the interactive setup wizard
ule init mydb.udb

# Overwrite an existing database (destructive)
ule init mydb.udb --force
```

**What the wizard configures:**
- **Admin Password:** Mandatory unique password for UI access and encryption.
- **Blockchain:** Toggle the tamper-proof audit trail.
- **WAL Mode:** Enable high-concurrency Write-Ahead Logging.
- **Quantum:** Activate the simulation engine.

**Options:**
- `-f, --force` - Force initialization even if the file exists.

---

### `ule repair` - Fix Audit Trail

Recompute and repair broken hash links in the blockchain audit trail. Use this if system crashes or disk errors caused integrity mismatches.

```bash
# Repair the database chain
ule repair mydb.udb
```

**Options:**
- `-p, --password` - Database admin password.

---

### `ule query` - Execute SQL

Run SQL queries on the database.

```bash
# Create table
ule query mydb.udb "CREATE TABLE users (id INTEGER, name TEXT, age INTEGER)"

# Insert data
ule query mydb.udb "INSERT INTO users VALUES (1, 'Ali', 25)"

# Select data
ule query mydb.udb "SELECT * FROM users WHERE age > 20"

# Update data
ule query mydb.udb "UPDATE users SET age = 26 WHERE name = 'Ali'"

# Delete data
ule query mydb.udb "DELETE FROM users WHERE id = 1"
```

**Options:**
- `-f, --file` - Read SQL from file
- `--format` - Output format (table, json, csv)

---

### `ule ask` - Natural Language Query

Ask questions in natural language (9+ languages).

```bash
# English
ule ask mydb.udb "show all users"
ule ask mydb.udb "count all users"
ule ask mydb.udb "show users older than 25"

# Urdu
ule ask mydb.udb "تمام صارفین دکھائیں" -l ur
ule ask mydb.udb "صارفین کی تعداد دکھائیں" -l ur

# Chinese
ule ask mydb.udb "显示所有用户" -l zh

# Spanish
ule ask mydb.udb "mostrar todos los usuarios" -l es

# French
ule ask mydb.udb "afficher tous les utilisateurs" -l fr

# Russian
ule ask mydb.udb "показать всех пользователей" -l ru

# Japanese
ule ask mydb.udb "すべてのユーザーを表示" -l ja

# Korean
ule ask mydb.udb "모든 사용자 표시" -l ko

# Portuguese
ule ask mydb.udb "mostrar todos os usuários" -l pt
```

**Options:**
- `-l, --language` - Language code (en, ur, zh, es, fr, ru, ja, ko, pt)
- `--show-sql` - Display generated SQL

---

### `ule push` - Push Document

Add a document to a collection.

```bash
# Push JSON document
ule push mydb.udb -c logs -d '{"level":"info","msg":"App started"}'

# Push from file
ule push mydb.udb -c logs -f data.json

# Push with custom ID
ule push mydb.udb -c users -d '{"name":"Ali"}' --id user_001
```

**Options:**
- `-c, --collection` - Collection name
- `-d, --data` - JSON document string
- `-f, --file` - JSON file path
- `--id` - Custom document ID

---

### `ule find` - Find Documents

Search documents in a collection.

```bash
# Find all documents
ule find mydb.udb -c logs

# Find with filter
ule find mydb.udb -c logs --filter '{"level":"error"}'

# Find with limit
ule find mydb.udb -c logs --limit 10
```

**Options:**
- `-c, --collection` - Collection name
- `--filter` - JSON filter object
- `--limit` - Maximum results
- `--format` - Output format (table, json)

---

### `ule link` - Create Graph Relationship

Create a relationship between two nodes.

```bash
# Basic link
ule link mydb.udb --from users --from-id 1 --to users --to-id 2 --relation FRIEND

# Link with properties
ule link mydb.udb --from users:1 --to orders:99 --relation PURCHASED --props '{"date":"2026-03-12"}'
```

**Options:**
- `--from` - Source table
- `--from-id` - Source node ID
- `--to` - Target table
- `--to-id` - Target node ID
- `--relation` - Relationship type
- `--props` - Relationship properties (JSON)

---

### `ule traverse` - Traverse Graph

Traverse graph relationships from a node.

```bash
# Basic traversal
ule traverse mydb.udb --table users --id 1 --depth 2

# Traverse with relation filter
ule traverse mydb.udb --table users --id 1 --relation FRIEND
```

**Options:**
- `--table` - Starting table
- `--id` - Starting node ID
- `--depth` - Traversal depth (default: 2)
- `--relation` - Filter by relation type

---

### `ule stats` - Show Statistics

Display database statistics.

```bash
ule stats mydb.udb
```

**Output includes:**
- Number of tables
- Number of documents
- Number of graph edges
- Number of vectors
- Audit blocks count
- File size

---

### `ule verify` - Verify Database

Verify database integrity and blockchain chain.

```bash
ule verify mydb.udb
```

**Checks:**
- Hash chain integrity
- Block signatures
- Data consistency

---

### `ule audit` - View Audit Trail

View the blockchain audit trail.

```bash
# View all audit entries
ule audit mydb.udb

# View recent entries
ule audit mydb.udb --limit 20

# View by operation type
ule audit mydb.udb --operation INSERT
```

**Options:**
- `--limit` - Maximum entries to show
- `--operation` - Filter by operation type
- `--format` - Output format (table, json)

---

### `ule serve` - Start REST API Server

Start the REST API server.

```bash
# Start server
ule serve --dbname mydb.udb

# Custom host/port
ule serve --host 0.0.0.0 --port 8000
```

**Options:**
- `--host, -h` - Host to bind (default: 0.0.0.0)
- `--port, -p` - Port to bind (default: 8000)
- `--dbname, -d` - Database file to serve
- `--reload, -r` - Auto-reload on changes

---

### `ule migrate` - Database Migrations

Manage schema changes with version control.

```bash
# Create migration
ule migrate create --dbname mydb.udb \
    --version "001" \
    --description "Create users table" \
    --up-sql "CREATE TABLE users (...)" \
    --down-sql "DROP TABLE users"

# Apply pending migrations
ule migrate up --dbname mydb.udb

# Apply to specific version
ule migrate up --dbname mydb.udb --target "002"

# Dry run (preview)
ule migrate up --dbname mydb.udb --dry-run

# Rollback last migration
ule migrate rollback --dbname mydb.udb --steps 1

# Check migration status
ule migrate status --dbname mydb.udb
```

---

### `ule tutorial` - Interactive Tutorials

Learn ULE features step-by-step.

```bash
# List all tutorials
ule tutorial list

# Filter by category
ule tutorial list --category SQL

# Filter by difficulty
ule tutorial list --difficulty beginner

# Start a tutorial
ule tutorial start basic_sql

# Move to next step
ule tutorial next
```

**Available Tutorials:**
- `basic_sql` - SQL Operations (Beginner, 10 min)
- `nosql_basics` - NoSQL Documents (Beginner, 10 min)
- `nlq_basics` - Natural Language Queries (Beginner, 8 min)
- `security_basics` - Database Security (Intermediate, 12 min)
- `graph_basics` - Graph Database (Intermediate, 15 min)
- `vector_basics` - Vector Search (Intermediate, 12 min)
- `timeseries_basics` - Time-Series Data (Intermediate, 10 min)
- `geospatial_basics` - Geospatial Queries (Intermediate, 10 min)
- `migrations_basics` - Migrations (Beginner, 8 min)
- `offline_basics` - Offline Mode (Advanced, 10 min)

---

### `ule iot` - IoT & MQTT

Manage IoT device connections and messages.

```bash
# Publish MQTT message
ule iot publish \
    --broker localhost \
    --port 1883 \
    --topic "sensors/temperature" \
    --message '{"value": 25.5}'

# Subscribe to MQTT topic
ule iot subscribe \
    --broker localhost \
    --topic "sensors/#"
```

---

### `ule cdc` - Change Data Capture

Track database changes in real-time.

```bash
# Enable CDC for a table
ule cdc enable --dbname mydb.udb --table users

# View recent changes
ule cdc changes --dbname mydb.udb --table users --limit 20
```

---

### `ule offline` - Offline Mode

Queue operations and sync when online.

```bash
# Check queue status
ule offline status --dbname mydb.udb

# Sync queued operations
ule offline sync --dbname mydb.udb --batch-size 100
```

---

### `ule vector` - Vector Operations

Manage vector embeddings and similarity search.

```bash
# Add vector embedding
ule vector-add --dbname mydb.udb \
    --collection embeddings \
    --id "doc1" \
    --vec '[0.1, 0.2, ...]' \
    --metadata '{"text": "Hello"}'

# Search similar vectors
ule vector-search --dbname mydb.udb \
    --collection embeddings \
    --vec '[0.15, 0.18, ...]' \
    --limit 10

# Generate embedding for text
ule vector-embed --dbname mydb.udb \
    --collection embeddings \
    --text "Hello World"
```

---

### `ule ui` - Terminal UI

Launch interactive terminal interface.

```bash
ule ui
```

---

### `ule quantum` - Quantum Computing

Run quantum algorithms and simulate circuits.

```bash
# Initialize quantum register
ule quantum init --qubits 2 --state 00

# Apply quantum gate
ule quantum gate --gate H --target 0
ule quantum gate --gate CNOT --target 1 --control 0

# Create and run circuit
ule quantum circuit --name bell --qubits 2

# Run quantum algorithm
ule quantum algorithm --algorithm grover --params '{"n": 3, "target": 5}'
ule quantum algorithm --algorithm bernstein-vazirani --params '{"n": 4, "secret": 10}'

# List available backends
ule quantum backends

# Visualize quantum state
ule quantum visualize --type bloch

# Show quantum engine info
ule quantum info
```

**Algorithms:**
- `deutsch-jozsa` - Determine if function is constant/balanced
- `grover` - Search unsorted database
- `qft` - Quantum Fourier Transform
- `teleportation` - Quantum teleportation protocol
- `superdense` - Superdense coding
- `bernstein-vazirani` - Find hidden string

---

### `ule keys generate` - Generate Key Pair

Generate RSA/Ed25519 key pair.

```bash
# Generate RSA keys
ule keys generate --user admin

# Generate Ed25519 keys
ule keys generate --user admin --algorithm ed25519
```

**Options:**
- `--user` - User name for keys
- `--algorithm` - Key algorithm (rsa, ed25519)
- `--output` - Output directory

---

## Global Options

- `--version` - Show version
- `--help` - Show help message
- `-v, --verbose` - Verbose output

## Examples

### Complete Workflow

```bash
# 1. Create database
ule init mydb.udb

# 2. Create table
ule query mydb.udb "CREATE TABLE users (id INTEGER, name TEXT, email TEXT)"

# 3. Insert data
ule query mydb.udb "INSERT INTO users VALUES (1, 'Ali', 'ali@example.com')"
ule query mydb.udb "INSERT INTO users VALUES (2, 'Sara', 'sara@example.com')"

# 4. Query with SQL
ule query mydb.udb "SELECT * FROM users"

# 5. Query with natural language
ule ask mydb.udb "show all users"

# 6. Add documents
ule push mydb.udb -c logs -d '{"level":"info","msg":"User logged in"}'

# 7. Create graph relationship
ule link mydb.udb --from users --from-id 1 --to users --to-id 2 --relation FRIEND

# 8. Check stats
ule stats mydb.udb

# 9. Verify integrity
ule verify mydb.udb
```
