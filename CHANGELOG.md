# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Database statistics method `db.stats()`
- Optional `--dbname` parameter to `ule serve` command

## [0.1.0-alpha++](https://github.com/ule-db/ule/releases/tag/v0.1.0-alpha++) - 2026-04-06

### 🎉 Major Release - All Features Complete

### Added - Languages (20 Total)
- English, Urdu, Chinese, French, Russian, Japanese, Korean, Spanish, Portuguese (existing)
- **NEW**: Hindi, Arabic, Bengali, Turkish
- **NEW**: Indonesian, Vietnamese, Thai, German, Italian, Polish, Swedish

### Added - Domain Models (5 Total)
- Healthcare model with HIPAA compliance
- Finance model with AML/PCI-DSS compliance
- Education model
- Retail model
- IoT model

### Added - Engines (7 Total)
- SQL Engine (existing)
- NoSQL Document Engine (existing)
- Graph Engine (existing)
- Vector Engine (existing, improved)
- **NEW**: Time-Series Engine
- **NEW**: Geospatial Engine
- **NEW**: Full-Text Search Engine

### Added - Security
- AES-256-GCM Column Encryption (existing)
- Digital Signatures RSA/Ed25519 (existing)
- **NEW**: Post-Quantum Cryptography (ML-KEM + Dilithium)
- **NEW**: Row-Level Security (RLS)
- **NEW**: Data Masking

### Added - IoT & Replication
- **NEW**: MQTT Client for IoT integration
- **NEW**: Change Data Capture (CDC)
- **NEW**: Offline Mode with automatic sync

### Added - DevTools
- **NEW**: Database Migrations system
- **NEW**: Interactive Tutorial System (10 tutorials)
- **NEW**: 15+ CLI commands for new features

### Added - AI
- **NEW**: Transformer NLQ with HuggingFace integration
- Natural Language Query in 20 languages

### Fixed
- Database context manager auto-initialization
- SQL engine `get_tables()` pattern matching
- NoSQL engine update method
- NLQ pattern ordering for English, Urdu, Chinese
- Italian NLQ patterns (added "gli" article support)
- Polish NLQ patterns (added "wszystkich" form)
- Import errors in test files
- Security module exports

### Documentation
- Complete API reference
- CLI command reference
- Quick start guide
- Security features guide
- Quantum computing guide
- New features documentation
- Contributing guide
- 6 example scripts

### Testing
- 304 tests passing (100% pass rate)
- Unit tests for all modules
- Integration tests for workflows
- Real-world scenario tests

---

## [0.1.0-alpha](https://github.com/ule-db/ule/releases/tag/v0.1.0-alpha) - 2026-03-10

### Initial Alpha Release

### Added
- Core SQLite-based database engine
- Basic NoSQL document storage
- Graph database with relationship tracking
- Vector similarity search
- Blockchain audit trail with SHA-256 hash chain
- Natural Language Query in 9 languages
- Column encryption with AES-256-GCM
- Digital signatures
- Quantum computing simulation
- Basic CLI commands
- Python API

### Testing
- 82 tests passing
- Core database tests
- Engine tests
- NLQ tests
- Blockchain tests
- Security tests

---

## Version Numbering

- `0.1.0-alpha`: Initial release with core features
- `0.1.0-alpha++`: All planned features complete (20 langs, 7 engines, IoT, CDC, Offline, etc.)
- `0.1.0-beta`: Will include bug fixes, performance improvements, stability
- `0.1.0`: First stable release
- `1.0.0`: Production-ready release

## Migration Guide

### From 0.1.0-alpha to 0.1.0-alpha++

Database files are **compatible** between versions. No migration needed.

**New imports available:**
```python
# IoT & Replication
from ule.iot import MQTTClient
from ule.replication import CDCManager, OfflineManager

# Migrations
from ule.migrations import MigrationManager

# AI
from ule.ai import TransformerNLQ

# Tutorials
from ule.tutorials import TutorialManager

# All engines
from ule.engines import (
    TimeSeriesEngine,
    GeospatialEngine,
    FullTextEngine
)
```

**New CLI commands:**
```bash
ule migrate create/up/rollback/status
ule tutorial list/start/next
ule iot publish/subscribe
ule cdc enable/changes
ule offline status/sync
```

---

[Unreleased]: https://github.com/ule-db/ule/compare/v0.1.0-alpha++...HEAD
[0.1.0-alpha++]: https://github.com/ule-db/ule/releases/tag/v0.1.0-alpha++
[0.1.0-alpha]: https://github.com/ule-db/ule/releases/tag/v0.1.0-alpha
