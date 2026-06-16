# ULE New Features Documentation

## Overview

This document covers the latest features added to ULE (Universal Ledger Engine).

**Test Status:** 292/292 tests passing (100% pass rate)

---

## 1. IoT & MQTT Integration

### MQTT Client

The MQTT client enables real-time communication with IoT devices and message brokers.

#### Features
- **Publish/Subscribe**: Full MQTT publish/subscribe support
- **Topic Routing**: Route MQTT messages to database tables automatically
- **Wildcard Support**: Supports MQTT wildcards (+, #) in topic patterns
- **Simulated Mode**: Works without MQTT broker for testing
- **Database Integration**: Automatically store messages in ULE tables

#### Usage

```python
from ule.iot import MQTTClient, QoS

# Create client
client = MQTTClient(broker='localhost', port=1883, db=db)

# Connect
client.connect()

# Publish message
client.publish('sensors/temperature', {'value': 25.5, 'unit': 'C'})

# Subscribe to topic
def handle_temp(client, userdata, msg):
    print(f"Temperature: {msg.payload}")

client.subscribe('sensors/temperature', handle_temp)

# Route to database table
client.route_to_table(
    'sensors/#',
    'sensor_data',
    column_mapping={'value': 'reading', 'unit': 'unit'}
)

# Disconnect
client.disconnect()
```

#### CLI Commands

```bash
# Publish MQTT message
ule iot publish --topic "sensors/temp" --message "25.5"

# Subscribe to topic
ule iot subscribe --topic "sensors/#"
```

---

## 2. Change Data Capture (CDC)

Track all data changes in your database with real-time streaming capabilities.

### Features
- **Automatic Tracking**: Track INSERT, UPDATE, DELETE operations
- **Real-time Streaming**: Stream changes as they happen
- **Event Listeners**: Add custom callbacks for change events
- **Persistent Log**: All changes stored in database
- **Filtering**: Filter changes by table, type, or timestamp

### Usage

```python
from ule.replication import CDCManager, ChangeType

# Create CDC manager
cdc = CDCManager(db)

# Enable tracking for a table
cdc.enable_table('users')

# Add a listener
def on_user_change(event):
    print(f"User changed: {event.change_type}")
    print(f"Old data: {event.old_data}")
    print(f"New data: {event.new_data}")

cdc.add_listener('users', on_user_change)

# Capture a change
cdc.capture_change(
    table='users',
    change_type=ChangeType.UPDATE,
    row_id=1,
    old_data={'name': 'Alice'},
    new_data={'name': 'Alice Updated'}
)

# Get recent changes
changes = cdc.get_changes('users', limit=10)

# Get changes by type
inserts = cdc.get_changes('users', change_type=ChangeType.INSERT)

# Get statistics
stats = cdc.get_stats()
print(f"Total changes: {stats['total_changes']}")
print(f"Changes by table: {stats['changes_by_table']}")
```

### CLI Commands

```bash
# Enable CDC for a table
ule cdc enable --dbname mydb.udb --table users

# View recent changes
ule cdc changes --dbname mydb.udb --table users --limit 20
```

---

## 3. Offline Mode

Enable ULE to operate offline by queuing operations and synchronizing when connection is restored.

### Features
- **Operation Queueing**: Queue all database operations while offline
- **Automatic Sync**: Sync queued operations when going online
- **Conflict Detection**: Detect and handle sync conflicts
- **Retry Logic**: Automatic retry for failed operations
- **Persistent Queue**: Queue survives application restarts

### Usage

```python
from ule.replication import OfflineManager, OperationType

# Create offline manager
offline = OfflineManager(db)

# Go offline
offline.go_offline()

# Execute operations (they'll be queued)
offline.execute(
    "INSERT INTO users (name) VALUES (?)",
    ("Alice",),
    table="users"
)

offline.execute(
    "UPDATE users SET name = ? WHERE id = ?",
    ("Bob", 1),
    table="users"
)

# Check queue status
status = offline.get_queue_status()
print(f"Queued: {status['total_queued']}")

# Go online and sync
offline.go_online()
result = offline.sync()

print(f"Synced: {result['synced']}")
print(f"Failed: {result['failed']}")
print(f"Remaining: {result['remaining']}")
```

### CLI Commands

```bash
# Check offline queue status
ule offline status --dbname mydb.udb

# Sync queued operations
ule offline sync --dbname mydb.udb --batch-size 100
```

---

## 4. Database Migrations

Manage schema changes with version control, supporting forward and backward migrations.

### Features
- **Version Control**: Track schema versions
- **Up/Down Migrations**: Support for applying and rolling back migrations
- **Dependencies**: Define migration dependencies
- **Python Functions**: Support complex migrations with Python functions
- **Dry Run**: Preview what migrations would do without applying them
- **File-based**: Save migrations to JSON files

### Usage

```python
from ule.migrations import MigrationManager

# Create migration manager
migrations = MigrationManager(db, migrations_dir='migrations')

# Create a migration
migrations.create_migration(
    version='001',
    description='Create users table',
    up_sql='''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''',
    down_sql='DROP TABLE users'
)

# Create migration with dependencies
migrations.create_migration(
    version='002',
    description='Add profile table',
    up_sql='''
        CREATE TABLE profiles (
            id INTEGER PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            bio TEXT
        )
    ''',
    down_sql='DROP TABLE profiles',
    dependencies=['001']
)

# Apply all pending migrations
result = migrations.migrate()
print(f"Applied: {result['applied']}")
print(f"Failed: {result['failed']}")

# Migrate to specific version
migrations.migrate(target='002')

# Dry run (preview)
result = migrations.migrate(dry_run=True)
for m in result['migrations']:
    print(f"Would apply: {m['version']} - {m['description']}")

# Rollback last migration
result = migrations.rollback(steps=1)
print(f"Rolled back: {result['rolled_back']}")

# Check migration status
status = migrations.get_status()
for s in status:
    print(f"{s['version']}: {s['status']}")

# Get current version
version = migrations.current_version()
print(f"Current version: {version}")
```

### CLI Commands

```bash
# Create a migration
ule migrate create --dbname mydb.udb \
    --version "001" \
    --description "Create users table" \
    --up-sql "CREATE TABLE users (...)" \
    --down-sql "DROP TABLE users"

# Apply pending migrations
ule migrate up --dbname mydb.udb

# Apply to specific version
ule migrate up --dbname mydb.udb --target "002"

# Dry run
ule migrate up --dbname mydb.udb --dry-run

# Rollback last migration
ule migrate rollback --dbname mydb.udb --steps 1

# Check migration status
ule migrate status --dbname mydb.udb
```

---

## 5. Transformer NLQ (HuggingFace)

Enhanced natural language query understanding using HuggingFace transformer models.

### Features
- **Transformer Models**: Use T5 and other HuggingFace models for NLQ
- **Automatic Fallback**: Falls back to pattern matching if transformers unavailable
- **Schema Awareness**: Provide schema context for better accuracy
- **Confidence Scoring**: Get confidence scores for generated SQL
- **Batch Processing**: Process multiple queries at once

### Usage

```python
from ule.ai import TransformerNLQ

# Create transformer NLQ (uses pattern matching if transformers unavailable)
nlq = TransformerNLQ(model_name='t5-small')

# Check if transformer is available
if nlq.has_transformer:
    print("Using transformer model")
else:
    print("Using pattern matching fallback")

# Convert natural language to SQL
result = nlq.query_to_sql("show me all users older than 25")

print(f"SQL: {result['sql']}")
print(f"Params: {result['params']}")
print(f"Confidence: {result['confidence']}")
print(f"Method: {result['method']}")

# Batch processing
queries = [
    "show all users",
    "count products",
    "find orders over 100"
]

results = nlq.batch_query(queries)
for query, result in zip(queries, results):
    print(f"Query: {query}")
    print(f"  SQL: {result['sql']}")
    print(f"  Confidence: {result['confidence']}")
```

### Supported Patterns (Fallback Mode)

The fallback pattern matcher supports:
- SELECT all: "show all users"
- SELECT with conditions: "find users older than 25"
- COUNT: "how many users"
- INSERT: "add user name=Alice age=30"
- UPDATE: "update user set name=Bob"
- DELETE: "delete user where name=Alice"

---

## 6. Tutorial System

Interactive tutorials for learning all ULE features with step-by-step guidance.

### Features
- **10 Built-in Tutorials**: Cover all major features
- **Progress Tracking**: Track tutorial completion
- **Interactive Steps**: Execute code and see results
- **Hints**: Get help when stuck
- **Multiple Categories**: SQL, NoSQL, AI, Security, Graph, Vector, Time-Series, Geospatial, DevTools, Replication
- **Difficulty Levels**: Beginner, Intermediate, Advanced

### Available Tutorials

| ID | Title | Category | Difficulty | Time |
|----|-------|----------|------------|------|
| basic_sql | Basic SQL Operations | SQL | Beginner | 10 min |
| nosql_basics | NoSQL Document Operations | NoSQL | Beginner | 10 min |
| nlq_basics | Natural Language Queries | AI | Beginner | 8 min |
| security_basics | Database Security | Security | Intermediate | 12 min |
| graph_basics | Graph Database Operations | Graph | Intermediate | 15 min |
| vector_basics | Vector Similarity Search | Vector | Intermediate | 12 min |
| timeseries_basics | Time-Series Data | Time-Series | Intermediate | 10 min |
| geospatial_basics | Geospatial Queries | Geospatial | Intermediate | 10 min |
| migrations_basics | Database Migrations | DevTools | Beginner | 8 min |
| offline_basics | Offline Mode | Replication | Advanced | 10 min |

### Usage

```python
from ule.tutorials import TutorialManager

# Create tutorial manager
tutorials = TutorialManager(db)

# List all tutorials
all_tutorials = tutorials.list_tutorials()
for t in all_tutorials:
    print(f"{t.id}: {t.title} ({t.difficulty})")

# Filter by category
sql_tutorials = tutorials.list_tutorials(category='SQL')

# Filter by difficulty
beginner_tutorials = tutorials.list_tutorials(difficulty='beginner')

# Start a tutorial
tutorial = tutorials.start_tutorial('basic_sql')
print(f"Started: {tutorial.title}")
print(f"Steps: {len(tutorial.steps)}")
print(f"Estimated time: {tutorial.estimated_time} minutes")

# Get current step
step = tutorials.get_current_step()
print(f"Step {step.id}: {step.title}")
print(f"Description: {step.description}")
print(f"Code:\n{step.code}")
if step.hint:
    print(f"Hint: {step.hint}")

# Execute step
result = tutorials.execute_step()
print(result['code'])

# Move to next step
next_step = tutorials.next_step()

# Go back to previous step
prev_step = tutorials.previous_step()

# Check progress
progress = tutorials.get_progress('basic_sql')
print(f"Status: {progress['status']}")
print(f"Current step: {progress['current_step']}")
print(f"Progress: {progress['progress'] * 100:.0f}%")

# Reset tutorial and start over
tutorials.reset_tutorial('basic_sql')
```

### CLI Commands

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

---

## Complete Feature List

### Core Features
- ✅ SQL Engine
- ✅ NoSQL Document Engine
- ✅ Graph Engine
- ✅ Vector Engine
- ✅ Time-Series Engine
- ✅ Geospatial Engine
- ✅ Full-Text Search Engine

### Security
- ✅ AES-256-GCM Column Encryption
- ✅ Digital Signatures (RSA/Ed25519)
- ✅ Row-Level Security (RLS)
- ✅ Data Masking
- ✅ Post-Quantum Cryptography (ML-KEM + Dilithium)
- ✅ Time-Travel Snapshots
- ✅ Database Integrity Verification

### IoT & Replication
- ✅ MQTT Client
- ✅ Change Data Capture (CDC)
- ✅ Offline Mode with Sync

### DevTools
- ✅ Database Migrations
- ✅ Tutorial System

### AI
- ✅ Natural Language Queries (20 languages)
- ✅ Transformer NLQ (HuggingFace)

### Languages (20 Total)
English, Urdu, Chinese, French, Russian, Japanese, Korean, Spanish, Portuguese, Hindi, Arabic, Bengali, Turkish, Indonesian, Vietnamese, Thai, German, Italian, Polish, Swedish

---

## Getting Started

```python
from ule import ULEDatabase

# Create database
db = ULEDatabase('mydb.udb')
db.init()

# Create table
db.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE,
        age INTEGER
    )
''')

# Insert data
db.execute("INSERT INTO users (name, email, age) VALUES (?, ?, ?)",
          ("Alice", "alice@example.com", 30))
db.commit()

# Query
results = db.execute("SELECT * FROM users WHERE age > ?", (25,))
for row in results:
    print(row)

# Close
db.close()
```

---

## Testing

All features are fully tested with 292 tests passing:

```bash
# Run all tests
PYTHONPATH=. .venv/bin/pytest tests/ -v

# Run specific module tests
PYTHONPATH=. .venv/bin/pytest tests/test_replication/ -v
PYTHONPATH=. .venv/bin/pytest tests/test_migrations/ -v
PYTHONPATH=. .venv/bin/pytest tests/test_tutorials/ -v
```

---

## Next Steps

- [ ] MQTT Client with real broker integration
- [ ] CDC streaming with WebSocket
- [ ] Migration auto-generation from schema diff
- [ ] Transformer model fine-tuning
- [ ] More tutorial scenarios
- [ ] Web-based tutorial UI

---

**Version:** 0.1.0-alpha++  
**Last Updated:** April 4, 2026  
**Tests:** 292/292 passing (100%)
