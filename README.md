# 🌌 Universal Ledger Engine (ULE)

**The People's Database** - Free, Open Source, Multi-Model

[![PyPI](https://img.shields.io/pypi/v/ule-db.svg)](https://pypi.org/project/ule-db/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Alpha](https://img.shields.io/badge/status-alpha-orange)](https://github.com/ule-db/ule)
[![Quantum Ready](https://img.shields.io/badge/quantum-ready-v0.1.0-purple)](https://github.com/ule-db/ule)

---

## What is ULE?

**ULE (Universal Ledger Engine)** is a unified database that combines **SQL + NoSQL + Graph + Vector + Quantum** in a single `.udb` file with:

- 🔐 **Blockchain audit trail** - Tamper-proof history with SHA-256 hash chain
- 🌍 **20 languages** - Natural language queries in English, Urdu, Chinese, Spanish, French, Russian, Japanese, Korean, Portuguese, Hindi, Arabic, Bengali, Turkish, Indonesian, Vietnamese, Thai, German, Italian, Polish, Swedish
- 🤖 **AI-powered** - Ask questions in plain language, get SQL automatically
- 📦 **Single file** - Entire database in one portable `.udb` file
- 💚 **100% free** - MIT License, free forever, no paid tiers
- ⚛️ **Quantum computing** - Run quantum algorithms, simulate circuits, connect to IBM Quantum
- 📡 **IoT & MQTT** - Real-time sensor data streaming
- 🔄 **CDC & Offline** - Change tracking and disconnected operation

### Tagline

> **ULE = SQLite + PostgreSQL + MongoDB + BigchainDB + Pinecone + Quantum — All in One `.udb` File, Free Forever**

---

## Quick Start

### Installation

```bash
# Install from PyPI
pip install ule-db

# Or install from source
git clone https://github.com/ule-db/ule.git
cd ule
pip install -e .
```

### Create Database

```bash
# Initialize new database
ule init mydata.udb

# With encryption
ule init mydata.udb --password
```

### Run Queries

```bash
# SQL
ule query mydata.udb "CREATE TABLE users (id INT, name TEXT, age INT)"
ule query mydata.udb "INSERT INTO users VALUES (1, 'Ali', 25)"
ule query mydata.udb "SELECT * FROM users"

# Natural Language (English)
ule ask mydata.udb "show all users"
ule ask mydata.udb "count all users"
ule ask mydata.udb "show users older than 25"

# Natural Language (Urdu)
ule ask mydata.udb "تمام صارفین دکھائیں" -l ur

# Natural Language (Chinese)
ule ask mydata.udb "显示所有用户" -l zh
```

### Python API

```python
from ule import connect
from ule.ai import NaturalLanguageQuery

# Connect to database
db = connect("mydata.udb", create_if_missing=True)

# SQL
db.execute("CREATE TABLE users (id INT, name TEXT, age INT)")
db.execute("INSERT INTO users VALUES (1, 'Ali', 25)")
results = db.execute("SELECT * FROM users")

# Documents (NoSQL)
db.push("logs", {"level": "info", "msg": "System started"})
docs = db.find("logs")

# Graph
db.link("users", "1", "orders", "99", "PURCHASED")
connections = db.traverse("users", "1", depth=2)

# Natural Language
nlq = NaturalLanguageQuery(db._conn)
results = nlq.ask("Show all users", language="en")

# Blockchain
is_valid = db.verify()
audit = db.audit()

db.close()
```

---

## Features

### Multi-Model Storage

| Model | Engine | CLI Command | Python API |
|-------|--------|-------------|------------|
| **SQL** | SQLite | `ule query` | `db.execute()` |
| **NoSQL** | Document | `ule push/find` | `db.push()/db.find()` |
| **Graph** | Graph DB | `ule link/traverse` | `db.link()/db.traverse()` |
| **Vector** | HNSW | Python only | `VectorEngine.add()/search()` |
| **Time-Series** | Time-Series | Python only | `TimeSeriesEngine.insert()/query_range()` |
| **Geospatial** | R-Tree | Python only | `GeospatialEngine.add_point()/find_nearby()` |
| **Full-Text** | FTS5 | Python only | `FullTextEngine.index()/search()` |
| **Quantum** | Qiskit/NumPy | `ule quantum` | `QuantumCircuit`, `QuantumAlgorithms` |

### IoT & Replication

| Feature | Description | CLI Command | Python API |
|---------|-------------|-------------|------------|
| **MQTT Client** | IoT message broker | `ule iot publish/subscribe` | `MQTTClient.publish()/subscribe()` |
| **CDC** | Change data capture | `ule cdc enable/changes` | `CDCManager.enable_table()/get_changes()` |
| **Offline Mode** | Queue & sync | `ule offline status/sync` | `OfflineManager.go_offline()/sync()` |

### DevTools

| Feature | Description | CLI Command | Python API |
|---------|-------------|-------------|------------|
| **Migrations** | Schema version control | `ule migrate create/up/rollback/status` | `MigrationManager.migrate()/rollback()` |
| **Tutorials** | Interactive learning | `ule tutorial list/start/next` | `TutorialManager.start_tutorial()/next_step()` |

### Quantum Computing

Run quantum algorithms and simulate circuits:

```bash
# Initialize quantum register
ule quantum init --qubits 2 --state 00

# Apply gates
ule quantum gate --gate H --target 0
ule quantum gate --gate CNOT --target 1 --control 0

# Run circuits
ule quantum circuit --name bell --qubits 2

# Run algorithms
ule quantum algorithm --algorithm grover --params '{"n": 3, "target": 5}'
ule quantum algorithm --algorithm bernstein-vazirani --params '{"n": 4, "secret": 10}'

# Show info
ule quantum info
```

```python
from ule.quantum import Qubit, QuantumCircuit, QuantumAlgorithms

# Create qubit in superposition
qubit = Qubit(alpha=1/np.sqrt(2), beta=1/np.sqrt(2))

# Build Bell state circuit
circuit = QuantumCircuit(num_qubits=2)
circuit.h(0)
circuit.cnot(0, 1)
result = circuit.execute()

# Run Grover's algorithm
algo = QuantumAlgorithms()
result = algo.grover_search(oracle_target=5, n=3)
print(f"Found: {result.output}")
```

**Features:**
- ⚛️ **Qubit simulation** - Up to 20 qubits with NumPy
- 🚪 **Quantum gates** - X, Y, Z, H, S, T, CNOT, CZ, SWAP, Toffoli, Fredkin
- 🔬 **Algorithms** - Grover, Deutsch-Jozsa, QFT, Teleportation, Superdense Coding, Bernstein-Vazirani
- 🖥️ **IBM Qiskit** - Run on real quantum computers (optional)
- 📊 **Visualization** - Bloch sphere, circuit diagrams, probability distributions
- 🔐 **Security** - Input validation, audit logging, state integrity verification

### IoT & MQTT Integration

Connect IoT devices and stream real-time data to your database:

```python
from ule.iot import MQTTClient

# Create MQTT client
client = MQTTClient(broker='localhost', port=1883, db=db)
client.connect()

# Publish sensor data
client.publish('sensors/temperature', {'value': 25.5, 'unit': 'C'})
client.publish('sensors/humidity', {'value': 65.2, 'unit': '%'})

# Subscribe to topic
def on_message(client, userdata, msg):
    print(f"Received: {msg.payload}")

client.subscribe('sensors/#', on_message)

# Route messages to database table
client.route_to_table('sensors/#', 'sensor_data')
```

### Change Data Capture (CDC)

Track all data changes with real-time streaming:

```python
from ule.replication import CDCManager, ChangeType

# Enable CDC
cdc = CDCManager(db)
cdc.enable_table('users')

# Add listener
def on_change(event):
    print(f"{event.change_type.value} on {event.table}")

cdc.add_listener('users', on_change)

# Get recent changes
changes = cdc.get_changes('users', limit=10)
stats = cdc.get_stats()
```

### Offline Mode

Queue operations offline and sync when online:

```python
from ule.replication import OfflineManager

offline = OfflineManager(db)

# Go offline
offline.go_offline()

# Queue operations
offline.execute("INSERT INTO users (name) VALUES (?)", ("Alice",), table="users")
offline.execute("UPDATE users SET name = ? WHERE id = ?", ("Bob", 1), table="users")

# Go online and sync
offline.go_online()
result = offline.sync()
print(f"Synced: {result['synced']}, Failed: {result['failed']}")
```

### Database Migrations

Version control for your schema:

```python
from ule.migrations import MigrationManager

migrations = MigrationManager(db)

# Create migration
migrations.create_migration(
    version='001',
    description='Create users table',
    up_sql='CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)',
    down_sql='DROP TABLE users'
)

# Apply migrations
migrations.migrate()

# Rollback
migrations.rollback(steps=1)

# Check status
status = migrations.get_status()
```

### Transformer NLQ (HuggingFace)

Enhanced natural language queries with transformer models:

```python
from ule.ai import TransformerNLQ

nlq = TransformerNLQ(model_name='t5-small')

if nlq.has_transformer:
    result = nlq.query_to_sql("show me all users older than 25")
    print(f"SQL: {result['sql']}")
    print(f"Confidence: {result['confidence']}")
```

### Tutorial System

Interactive tutorials for learning all features:

```python
from ule.tutorials import TutorialManager

tutorials = TutorialManager(db)

# List tutorials
all_tutorials = tutorials.list_tutorials()
beginner_tutorials = tutorials.list_tutorials(difficulty='beginner')

# Start tutorial
tutorial = tutorials.start_tutorial('basic_sql')
step = tutorials.get_current_step()
print(f"Step {step.id}: {step.title}")

# Navigate
tutorials.next_step()
tutorials.previous_step()

# Check progress
progress = tutorials.get_progress('basic_sql')
print(f"Progress: {progress['progress'] * 100:.0f}%")
```

### Natural Language Support

Ask questions in **20 languages** - no SQL needed!

**Supported Languages:** English, Urdu, Chinese, French, Russian, Japanese, Korean, Spanish, Portuguese, Hindi, Arabic, Bengali, Turkish, Indonesian, Vietnamese, Thai, German, Italian, Polish, Swedish

```bash
# English
ule ask mydb.udb "show all users"
ule ask mydb.udb "count all users"
ule ask mydb.udb "show users older than 25"

# Urdu (اردو)
ule ask mydb.udb "تمام صارفین دکھائیں" --language ur
ule ask mydb.udb "صارفین کی تعداد دکھائیں" --language ur

# Chinese (中文)
ule ask mydb.udb "显示所有用户" --language zh
ule ask mydb.udb "计算用户总数" --language zh

# Spanish (Español)
ule ask mydb.udb "mostrar todos los usuarios" --language es
ule ask mydb.udb "contar todos los usuarios" --language es

# French (Français)
ule ask mydb.udb "afficher tous les utilisateurs" --language fr

# Russian (Русский)
ule ask mydb.udb "показать всех пользователей" --language ru

# Japanese (日本語)
ule ask mydb.udb "すべてのユーザーを表示" --language ja

# Korean (한국어)
ule ask mydb.udb "모든 사용자 표시" --language ko

# Portuguese (Português)
ule ask mydb.udb "mostrar todos os usuários" --language pt
```

### Security Features

- **AES-256-GCM** encryption for data at rest
- **RSA-4096 / Ed25519** key pairs for digital signatures
- **SHA-256 hash chain** for tamper-proof audit trail
- **Role-Based Access Control (RBAC)** for permissions
- **Blockchain audit trail** - every operation recorded immutably
- **Web UI Authentication** - Token-based auth with rate limiting
- **Terminal UI Password** - Password protection for CLI access
- **Input Validation** - SQL injection & XSS protection
- **CORS Protection** - Cross-origin request security
- **Rate Limiting** - DoS protection (60 req/min)

### Security Configuration

```bash
# Change default password for Web/Terminal UI (IMPORTANT!)
export ULE_ADMIN_PASSWORD="your-secure-password"

# Set secret key for token signing (optional, auto-generated if not set)
export ULE_SECRET_KEY="your-random-secret-key"

# Then start UI
ule ui           # Terminal UI (asks for password)
ule serve        # Web UI (login required)
```

**⚠️ Default credentials:** `admin` / `admin` — **Change before production use!**

**🔒 Security Note:** Web UI and Terminal UI require authentication. All API routes are protected with token-based auth, rate limiting, and input validation.

---

## CLI Commands

### Initialization

```bash
ule init mydb.udb              # Create new database
ule init mydb.udb --password   # Create encrypted database
```

### Queries

```bash
ule query mydb.udb "SELECT * FROM users"           # SQL query
ule ask mydb.udb "Show all users"                  # Natural language
ule ask mydb.udb "تمام صارفین دکھائیں" -l ur       # Urdu
ule ask mydb.udb "显示所有用户" -l zh               # Chinese
```

### Documents (NoSQL)

```bash
ule push -c logs -d '{"level":"info","msg":"Hi"}'  # Push document
ule find -c logs                                   # Find all documents
ule find -c logs --filter '{"level":"error"}'      # Filter documents
```

### Graph

```bash
ule link --from users --from-id 1 --to users --to-id 2 --relation FRIEND
ule traverse --table users --id 1 --depth 2
```

### Blockchain & Security

```bash
ule keys generate --user admin        # Generate RSA/Ed25519 keys
ule verify mydb.udb                   # Verify database integrity
ule audit mydb.udb                    # View audit trail
```

### Server & UI

```bash
ule serve mydb.udb                    # Start Unified Professional Server (API + Web Studio)
ule serve mydb.udb --host 0.0.0.0 --port 8000

ule ui                                # Launch interactive terminal UI
```

**Web Interface:** Open http://localhost:8000 in your browser after running `ule serve`.

### Info

```bash
ule stats mydb.udb    # Show database statistics
```

---

## Project Structure

```
ule/
├── core/           # Database, connection, config
├── storage/        # SQLite backend, WAL
├── security/       # Encryption, keys, auth, RBAC
├── blockchain/     # Hash chain, audit trail
├── engines/        # SQL, NoSQL, Graph, Vector
├── ai/             # Natural Language (9 languages)
│   └── patterns/   # Language patterns (en, ur, zh, es, fr, ru, ja, ko, pt)
├── server/         # Unified Server (REST API + Web Studio)
├── utils/          # Helpers, logging
└── cli.py          # Command-line interface
```

---

## Examples

### 1. Quick Start Demo

```bash
python examples/01_quickstart.py
```

Covers: SQL, Natural Language, Documents, Graph, Blockchain

### 2. Multilingual Demo

```bash
python examples/02_multilingual.py
```

Shows natural language queries in all 9 supported languages.

### 3. Complete Feature Demo

```bash
python examples/03_complete_demo.py
```

Demonstrates all ULE features: SQL, NoSQL, Graph, Vector, NLQ, Blockchain.

---

## Documentation

- **[Quick Start Guide](docs/QUICKSTART.md)** - Get started in 5 minutes
- **[CLI Reference](docs/CLI.md)** - Complete CLI command reference
- **[Python API](docs/API.md)** - Python API documentation

---

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/ule-db/ule.git
cd ule

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=ule

# Specific test file
pytest tests/test_engines/test_sql.py
```

---

## Roadmap

| Phase | Status | Features |
|-------|--------|----------|
| Phase 1 | ✅ | Core, SQL, Encryption |
| Phase 2 | ✅ | Blockchain, NoSQL, Graph |
| Phase 3 | ✅ | Natural Language (9 langs), Vector |
| Phase 4 | 🟡 | Testing, Documentation, PyPI Launch |
| Phase 5 | ⬜ | Time-series, Geospatial, Full-text search |
| Phase 6 | ⬜ | 50+ languages, Domain-specific models |

---

## FAQ

### General Questions

**Q: Is ULE production-ready?**  
A: ULE is currently in alpha (v0.1.0-alpha++). All core features are implemented and tested (304 tests passing), but we recommend thorough testing for production use.

**Q: How does ULE compare to SQLite/PostgreSQL/MongoDB?**  
A: ULE combines multiple database models in one file. It's not meant to replace specialized databases but provides a unified solution for projects needing SQL + NoSQL + Graph + Vector + IoT capabilities without managing multiple systems.

**Q: Is ULE free?**  
A: Yes, 100% free under MIT License. No paid tiers, no premium features.

### Technical Questions

**Q: How do I migrate from SQLite to ULE?**  
A: ULE uses SQLite as its SQL engine, so you can import existing SQLite databases directly. See `docs/MIGRATION.md` for detailed instructions.

**Q: How does encryption work?**  
A: ULE supports AES-256-GCM column-level encryption. Enable it per-column, and data is automatically encrypted before storage and decrypted on retrieval. See `docs/SECURITY_FEATURES.md`.

**Q: Can I use ULE offline?**  
A: Yes! The Offline Mode queues operations locally and syncs when connectivity is restored. Perfect for mobile/edge scenarios.

**Q: What languages are supported for NLQ?**  
A: 20 languages: English, Urdu, Chinese, French, Russian, Japanese, Korean, Spanish, Portuguese, Hindi, Arabic, Bengali, Turkish, Indonesian, Vietnamese, Thai, German, Italian, Polish, Swedish.

**Q: How do I run the tutorials?**  
A: Use the CLI: `ule tutorial list` to see all tutorials, `ule tutorial start basic_sql` to begin.

### Deployment Questions

**Q: Can I deploy ULE with Docker?**  
A: Docker support is planned. For now, install via pip and run with Python.

**Q: How do I secure my database?**  
A: ULE is "Secure by Default". You are required to set a unique admin password during the `ule init` wizard. This password is used for both encryption (if enabled) and UI authentication.

**Q: Does ULE support concurrent access?**  
A: Yes, ULE uses SQLite's WAL mode for concurrent reads. Writes are serialized.

### Performance Questions

**Q: What's the maximum database size?**  
A: SQLite supports up to 281 TB per database file. Practical limits depend on hardware.

**Q: How fast is vector search?**  
A: Vector search uses efficient indexing. For millions of vectors, consider dedicated vector databases.

**Q: Does quantum computing work on real hardware?**  
A: Yes, ULE integrates with IBM Qiskit for real quantum hardware access (optional).

---

## License

**MIT License** - Free 

```
Copyright (c) 2026 ULE Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md)

### How to Contribute:

- 📝 **Translate** - Help translate docs to your language
- 📖 **Write tutorials** - Share your knowledge
- 🐛 **Report bugs** - File issues on GitHub
- 💡 **Suggest features** - Open RFCs
- 🔧 **Code** - Submit pull requests

---

## Support

- **Documentation:** `/docs`
- **Examples:** `/examples`
- **Issues:** GitHub Issues
- **Email:** sadiqaliali1987@gmail.com

---

**ULE = One File, Every Model, Absolute Trust, Zero Cost**

Made with 💚 for the open source community
tHub Issues
- **Email:** sadiqaliali1987@gmail.com

---

**ULE = One File, Every Model, Absolute Trust, Zero Cost**

Made with 💚 for the open source community
