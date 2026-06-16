# 🧪 ULE v0.1.0 Professional Testing Guide

This guide provides a step-by-step verification process to ensure your Universal Ledger Engine (ULE) deployment is secure, stable, and production-ready.

---

### **1. Professional Setup Wizard Test**
Verify that the mandatory password and feature configuration are working as intended.
- **Command:**
  ```bash
  python3 ule/cli.py init production_test.udb
  ```
- **Expectation:** 
  - The system must prompt for an **Admin Password**.
  - Try entering a password shorter than 8 characters (it should reject it).
  - Verify that you can toggle **Blockchain**, **WAL**, and **Quantum** features.
  - On success, it should report: `✓ Database production_test.udb initialized successfully.`

---

### **2. Security Hardening Test (No Defaults)**
Verify that the legacy `admin/admin` credentials have been completely removed.
- **Command:**
  ```bash
  # Attempt to login to the Terminal UI
  python3 ule/ui/terminal.py production_test.udb
  ```
- **Expectation:** 
  - Enter `admin` as username and `admin` as password.
  - **Result:** It **must** fail with `✗ Invalid credentials.`
  - Now enter the unique password you set in Step 1.
  - **Result:** It should succeed with `✓ Authentication successful (via Database)!`

---

### **3. SQL Injection Protection Test (NLQ)**
Verify that the Natural Language Query engine is now parameterized and immune to basic injection.
- **Command:**
  ```bash
  # Attempt a classic SQL injection payload through the NLQ engine
  python3 ule/cli.py ask production_test.udb "show all users where name = 'admin' OR '1'='1'"
  ```
- **Expectation:** 
  - The engine should treat `'admin' OR '1'='1'` as a single literal search string.
  - It **must not** return all users. It should return 0 results (unless a user is literally named `'admin' OR '1'='1'`).

---

### **4. Data Integrity Verification (D-Hash)**
Verify that the NoSQL engine detects manual file tampering or silent corruption.
- **Steps:**
  1. **Push data:** `python3 ule/cli.py push production_test.udb -c secrets -d '{"key":"top_secret"}'`
  2. **Tamper:** Use an external SQLite browser to open `production_test.udb`. Go to the `_documents` table and change one letter in the `data` column for that record.
  3. **Retrieve:** `python3 ule/cli.py find production_test.udb -c secrets`
- **Expectation:** 
  - The system should output: `[CRITICAL] Data corruption detected in collection 'secrets'. Hash mismatch.`
  - The corrupted record will be skipped to protect application logic.

---

### **5. Blockchain Repair Tool Test**
Verify that the system can self-heal a broken audit trail.
- **Steps:**
  1. **Verify:** `python3 ule/cli.py verify production_test.udb` (Should be Green/Success).
  2. **Tamper:** Use an external SQLite tool to change a value in the `hash` or `prev_hash` columns of the `_audit` table.
  3. **Verify Again:** `python3 ule/cli.py verify production_test.udb` (Should be Red/Fail).
  4. **Repair:** `python3 ule/cli.py repair production_test.udb`
- **Expectation:** 
  - The repair tool will recompute the chain.
  - Final output: `✓ Repair complete. X links updated.`

---

### **6. REST API Authentication Test**
Verify the hardened FastAPI security layer.
- **Command:**
  ```bash
  # Start the server
  python3 ule/server/api.py
  ```
- **Test (Terminal/Curl):**
  ```bash
  curl -X GET "http://localhost:8000/stats?db_path=production_test.udb"
  ```
- **Expectation:** 
  - **Result:** `401 Unauthorized`.
  - Sensitive stats are now protected and require a valid session token or Basic Auth header.

---

### **7. Full Automated Test Suite**
Run the comprehensive regression suite to ensure no structural regressions.
- **Command:**
  ```bash
  export PYTHONPATH=.
  pytest tests/
  ```
- **Expectation:** 
  - All 300+ tests (SQL, NoSQL, Graph, Vector, Security, Quantum) should pass.

---
**Note:** These tests confirm that ULE v0.1.0 meets the professional "Secure-by-Default" standard.
