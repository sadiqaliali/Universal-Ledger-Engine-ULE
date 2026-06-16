# 🚀 ULE Production Deployment Guide

This guide covers best practices for deploying the Universal Ledger Engine (ULE) in production environments, from Edge/IoT to Cloud Servers.

## 1. Environment Security

### Admin Credentials
- **Never** use default credentials. Set a strong password during `ule init`.
- For automated deployments, use the `ULE_ADMIN_PASSWORD` environment variable.
- Keep your `ULE_SECRET_KEY` private; it is used for signing session tokens.

### Firewall & Networking
- If running `ule serve`, ensure the port (default 8000) is not exposed directly to the public internet.
- Use a **Reverse Proxy** (Nginx, Caddy, or Traefik) with TLS/SSL termination.
- Restrict access to known IP addresses if possible.

## 2. Storage & Persistence

### File Integrity
- Store your `.udb` files on a filesystem that supports atomic writes.
- Enable **Write-Ahead Logging (WAL)** during `ule init` for high-concurrency read/write operations.
- Set `blockchain_sync: True` in your config if your application requires absolute ledger integrity over write speed.

### Backups
- Since ULE is a single-file database, backups are simple:
  - **Cold Backup:** Stop the server and copy the `.udb` file.
  - **Hot Backup:** Use the `ule snapshot` command (or the `storage.snapshots` module) to create a consistent point-in-time copy without downtime.

## 3. Deployment Methods

### Docker (Recommended)
Use the official Dockerfile provided in the repository:
```bash
docker build -t ule-db .
docker run -d \
  -p 8000:8000 \
  -v /path/to/your/data:/data \
  -e ULE_ADMIN_PASSWORD="your-secure-password" \
  ule-db
```

### Systemd (Linux)
For "bare metal" or VM deployments, use a systemd service to ensure ULE starts on boot and restarts on failure.

```ini
[Unit]
Description=ULE REST API Server
After=network.target

[Service]
User=uleuser
WorkingDirectory=/opt/ule
Environment="ULE_ADMIN_PASSWORD=your-secure-password"
ExecStart=/usr/local/bin/uvicorn ule.server.api:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

## 4. Performance Tuning

### Memory Management
- For large **Vector** collections (>100k items), ensure the host has sufficient RAM. HNSW indices are memory-intensive.
- Use the **Connection Pool** settings in `ule.server.api` to tune the maximum number of concurrent database connections.

### Concurrency
- SQLite (and thus ULE) supports multiple concurrent readers but a single writer. 
- If your application is write-heavy, implement a message queue (like RabbitMQ or Redis) to buffer writes and prevent "Database is locked" errors.

## 5. Monitoring & Maintenance

- **Integrity Checks:** Regularly run `ule verify` to ensure the blockchain hash chain is intact.
- **Audit Logs:** Monitor the `_audit` table for suspicious activity or unauthorized access attempts.
- **Log Rotation:** Configure `uvicorn` and Python logging to use rotating file handlers to prevent disk exhaustion.
