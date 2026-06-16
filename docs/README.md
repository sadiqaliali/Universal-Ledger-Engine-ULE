# Universal Ledger Engine (ULE) Documentation

## API Reference
The ULE API provides a unified interface for managing multi-model data, quantum simulations, and audit trails.

### Endpoints
- `GET /health` - Service status and readiness check.
- `GET /docs` - Swagger UI documentation.
- `POST /query` - Execute multi-model queries.

## Deployment Guide
### Prerequisites
- Python 3.12+
- Docker (optional)

### Quick Start
1. Install: `pip install ule`
2. Initialize: `ule init`
3. Start: `ule serve`

## Security
ULE utilizes envelope encryption and PQC-ready modules. See `docs/SECURITY_FEATURES.md` for details.
