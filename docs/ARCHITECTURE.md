# 🏗️ ULE Architecture Guide

This document explains how the Universal Ledger Engine (ULE) maps complex data models (NoSQL, Graph, Vector, Quantum) onto its relational SQLite backend.

## 1. Core Principles
- **Portability First:** Everything is stored in a single `.udb` file.
- **SQLite Foundation:** ULE uses SQLite as the primary storage engine, leveraging WAL (Write-Ahead Logging) for high-performance concurrent reads.
- **Layered Abstraction:** Each data model is a logical layer that translates its operations into optimized SQL.

## 2. Model Mapping

### 📄 Document Model (NoSQL)
- **Table:** `_documents`
- **Mapping:** Documents are JSON-serialized, encrypted (optional), and stored as BLOBs. 
- **Indexing:** Primary key is `(collection, doc_id)`. Ad-hoc filtering is performed at the application layer by deserializing JSON during the query phase.

### 🕸️ Graph Model
- **Table:** `_edges`
- **Mapping:** An adjacency list model. Each row represents a directed edge with `from_table`, `from_id`, `to_table`, `to_id`, and a `relation` type.
- **Traversals:** Performed via recursive Python functions (BFS/DFS) that query the `_edges` table at each step.

### 📐 Vector Model
- **Table:** `_vectors`
- **Mapping:** High-dimensional embeddings are stored as BLOBs alongside metadata.
- **Search:** For small datasets, cosine similarity is computed in Python. For large datasets, ULE integrates with **HNSWLib** to provide fast Approximate Nearest Neighbor (ANN) search.

### ⚛️ Quantum Model
- **Engine:** `QuantumEngine`
- **Simulation:** A state-vector simulator using NumPy.
- **Persistence:** Quantum circuits and computed state-vectors can be persisted into standard ULE tables for later retrieval and analysis.

## 3. Security & Integrity

### 🛡️ Envelope Encryption
ULE uses a two-tier encryption system:
1. **Master Key (MK):** Derived from the user's password using PBKDF2.
2. **Data Key (DK):** A random AES-256 key used for all data encryption, which is itself encrypted by the Master Key and stored in the `_keys` table.
This allows for password rotation without re-encrypting the entire database.

### ⛓️ Blockchain Audit Trail
- **Table:** `_audit`
- **Mechanism:** A SHA-256 hash chain where each block contains the `prev_hash` of the previous operation.
- **Batching:** An asynchronous `BatchAuditManager` buffers events and flushes them in bulk to maximize throughput, with an optional `blockchain_sync` mode for absolute integrity.

## 4. Storage Engine Details
- **Journal Mode:** `WAL` (Write-Ahead Logging) is enabled by default to allow multiple readers and a single writer.
- **Synchronous:** Set to `NORMAL` to balance safety and performance.
- **Application ID:** Every `.udb` file has a custom Application ID (`0x554c4531`) in its header for file type identification.
