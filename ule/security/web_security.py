"""ULE Security Middleware for Web UI."""

from fastapi import FastAPI, Request, HTTPException, status, Form
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import HTTPBearer, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from datetime import datetime, timedelta
import secrets
import hashlib
import time
import os
from typing import Dict, Optional, Set
from collections import defaultdict

# ============ Configuration ============

SECRET_KEY = os.environ.get("ULE_SECRET_KEY", secrets.token_urlsafe(32))
TOKEN_EXPIRY_HOURS = 24
MAX_REQUESTS_PER_MINUTE = 60
MAX_FAILED_LOGINS = 5
LOCKOUT_MINUTES = 15

# ============ Token Management ============

class TokenManager:
    """Manage authentication tokens."""

    def __init__(self):
        self.tokens: Dict[str, dict] = {}
        self.failed_attempts: Dict[str, list] = defaultdict(list)
        self.locked_ips: Dict[str, datetime] = {}

    def create_token(self, username: str) -> str:
        """Create new authentication token."""
        token = secrets.token_urlsafe(32)
        self.tokens[token] = {
            "username": username,
            "created": datetime.now(),
            "expires": datetime.now() + timedelta(hours=TOKEN_EXPIRY_HOURS),
            "last_used": datetime.now()
        }
        return token

    def validate_token(self, token: str) -> Optional[dict]:
        """Validate token and return user info."""
        if token not in self.tokens:
            return None

        token_data = self.tokens[token]

        # Check expiry
        if datetime.now() > token_data["expires"]:
            del self.tokens[token]
            return None

        # Update last used
        token_data["last_used"] = datetime.now()
        return token_data

    def revoke_token(self, token: str) -> bool:
        """Revoke authentication token."""
        if token in self.tokens:
            del self.tokens[token]
            return True
        return False

    def record_failed_login(self, ip: str) -> bool:
        """Record failed login attempt. Returns True if locked out."""
        now = datetime.now()

        # Clean old attempts
        self.failed_attempts[ip] = [
            t for t in self.failed_attempts[ip]
            if (now - t).total_seconds() < 3600
        ]

        self.failed_attempts[ip].append(now)

        # Check if locked out
        if len(self.failed_attempts[ip]) >= MAX_FAILED_LOGINS:
            self.locked_ips[ip] = now
            return True

        return False

    def is_locked(self, ip: str) -> bool:
        """Check if IP is locked out."""
        if ip not in self.locked_ips:
            return False

        lock_time = self.locked_ips[ip]
        if (datetime.now() - lock_time).total_seconds() > LOCKOUT_MINUTES * 60:
            del self.locked_ips[ip]
            return False

        return True

    def cleanup(self):
        """Clean up expired tokens."""
        now = datetime.now()
        expired = [t for t, d in self.tokens.items() if now > d["expires"]]
        for token in expired:
            del self.tokens[token]


# Global token manager
token_manager = TokenManager()


# ============ Rate Limiting ============

class RateLimiter:
    """Rate limiting middleware."""

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = defaultdict(list)

    def is_allowed(self, client_ip: str) -> bool:
        """Check if request is allowed."""
        now = time.time()
        window_start = now - self.window_seconds

        # Clean old requests
        self.requests[client_ip] = [
            t for t in self.requests[client_ip] if t > window_start
        ]

        # Check limit
        if len(self.requests[client_ip]) >= self.max_requests:
            return False

        # Record request
        self.requests[client_ip].append(now)
        return True


rate_limiter = RateLimiter(max_requests=MAX_REQUESTS_PER_MINUTE)


# ============ Input Sanitization ============

import re
import html

# Dangerous SQL patterns
SQL_INJECTION_PATTERNS = [
    r";\s*DROP\s+",
    r";\s*DELETE\s+",
    r";\s*UPDATE\s+.*\s+SET\s+",
    r";\s*INSERT\s+",
    r";\s*ALTER\s+",
    r";\s*CREATE\s+",
    r";\s*TRUNCATE\s+",
    r"--\s*$",
    r"/\*.*\*/",
    r"'\s*OR\s+'1'\s*=\s*'1",
    r"'\s*OR\s+1\s*=\s*1",
    r"'\s*;\s*--",
]

# Dangerous HTML/JS patterns
XSS_PATTERNS = [
    r"<script[^>]*>",
    r"javascript:",
    r"on\w+\s*=",
    r"<iframe[^>]*>",
    r"<object[^>]*>",
    r"<embed[^>]*>",
]


def sanitize_sql_input(value: str) -> str:
    """Sanitize SQL input to prevent injection."""
    if not isinstance(value, str):
        return value

    # Check for SQL injection patterns
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, value, re.IGNORECASE):
            raise ValueError(f"Potentially dangerous SQL input detected")

    return value.strip()


def sanitize_html_input(value: str) -> str:
    """Sanitize HTML input to prevent XSS."""
    if not isinstance(value, str):
        return value

    # Check for XSS patterns
    for pattern in XSS_PATTERNS:
        if re.search(pattern, value, re.IGNORECASE):
            raise ValueError(f"Potentially dangerous HTML input detected")

    # Escape HTML
    return html.escape(value)


def validate_json_input(data: dict, schema: dict) -> tuple:
    """Validate JSON input against schema."""
    errors = []

    for field, rules in schema.items():
        value = data.get(field)

        # Required check
        if rules.get("required", False) and value is None:
            errors.append(f"Field '{field}' is required")
            continue

        if value is None:
            continue

        # Type check
        expected_type = rules.get("type")
        if expected_type and not isinstance(value, expected_type):
            errors.append(f"Field '{field}' must be {expected_type.__name__}")
            continue

        # Max length check
        max_length = rules.get("max_length")
        if max_length and isinstance(value, str) and len(value) > max_length:
            errors.append(f"Field '{field}' exceeds maximum length of {max_length}")
            continue

        # Pattern check
        pattern = rules.get("pattern")
        if pattern and isinstance(value, str) and not re.match(pattern, value):
            errors.append(f"Field '{field}' does not match required pattern")
            continue

    return len(errors) == 0, errors


# ============ Security Middleware ============

class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for ULE web UI."""

    def __init__(self, app, exclude_paths: Set[str] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or {"/", "/health", "/login", "/static"}

    async def dispatch(self, request: Request, call_next) -> Response:
        # Get client IP
        client_ip = request.client.host

        # Check lockout
        if token_manager.is_locked(client_ip):
            return JSONResponse(
                status_code=423,
                content={"error": "Too many failed attempts. Try again later."}
            )

        # Rate limiting
        if not rate_limiter.is_allowed(client_ip):
            return JSONResponse(
                status_code=429,
                content={"error": "Too many requests. Please slow down."}
            )

        # Skip auth for excluded paths
        path = request.url.path
        if any(path.startswith(exclude) for exclude in self.exclude_paths):
            return await call_next(request)

        # Check authentication
        auth_header = request.headers.get("Authorization", "")
        token = None

        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
        elif auth_header.startswith("Token "):
            token = auth_header[6:]

        # Also check cookie
        if not token:
            cookie = request.cookies.get("ule_auth_token")
            if cookie:
                token = cookie

        if not token:
            return JSONResponse(
                status_code=401,
                content={"error": "Authentication required"}
            )

        # Validate token
        token_data = token_manager.validate_token(token)
        if not token_data:
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid or expired token"}
            )

        # Add user info to request state
        request.state.user = token_data["username"]
        request.state.token = token

        # Add security headers to response
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"

        return response


# ============ Auth Routes ============

from fastapi import APIRouter

auth_router = APIRouter()


@auth_router.post("/login")
async def login(
    username: str = Form(...),
    password: str = Form(...),
    request: Request = None
):
    """Authenticate user and return token."""
    client_ip = request.client.host if request else "unknown"

    # Check lockout
    if token_manager.is_locked(client_ip):
        raise HTTPException(
            status_code=423,
            detail="Too many failed attempts. Try again later."
        )

    # Validate credentials
    env_admin_password = os.environ.get("ULE_ADMIN_PASSWORD")
    authenticated = False
    
    # 1. Check Environment Variable (High Priority)
    if env_admin_password:
        if username == "admin" and password == env_admin_password:
            authenticated = True
            
    # 2. Check Database (If ENV not set or auth failed)
    if not authenticated:
        # Try to find db_path from request or common location
        db_path = request.query_params.get("db_path") or "main.udb"
        if os.path.exists(db_path):
            try:
                from ule.core.database import ULEDatabase
                import hashlib
                
                db = ULEDatabase(db_path)
                db.open()
                
                cursor = db._conn.execute(
                    "SELECT password_hash FROM _users WHERE username = ?",
                    (username,)
                )
                row = cursor.fetchone()
                db.close()
                
                if row:
                    stored_hash = row[0]
                    from argon2 import PasswordHasher
                    ph = PasswordHasher()
                    try:
                        ph.verify(stored_hash, password)
                        authenticated = True
                    except Exception:
                        pass
            except Exception:
                pass

    if authenticated:
        token = token_manager.create_token(username)
        # ... rest of successful login logic ...

        response = JSONResponse(content={
            "success": True,
            "token": token,
            "expires_in": TOKEN_EXPIRY_HOURS * 3600
        })

        # Set secure cookie
        response.set_cookie(
            key="ule_auth_token",
            value=token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=TOKEN_EXPIRY_HOURS * 3600
        )

        return response

    # Record failed attempt
    token_manager.record_failed_login(client_ip)

    raise HTTPException(
        status_code=401,
        detail="Invalid credentials"
    )


@auth_router.post("/logout")
async def logout(authorization: str = None):
    """Logout and revoke token."""
    token = None

    if authorization:
        if authorization.startswith("Bearer "):
            token = authorization[7:]
        elif authorization.startswith("Token "):
            token = authorization[6:]

    if token:
        token_manager.revoke_token(token)

    response = JSONResponse(content={"success": True, "message": "Logged out"})
    response.delete_cookie("ule_auth_token")
    return response


@auth_router.get("/me")
async def get_current_user(request: Request):
    """Get current user info."""
    if hasattr(request.state, "user"):
        return {
            "username": request.state.user,
            "authenticated": True
        }
    return {"authenticated": False}


# ============ Security Helper Functions ============

def setup_security(app: FastAPI):
    """Setup security for FastAPI app."""

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

    # Add security middleware
    app.add_middleware(
        SecurityMiddleware,
        exclude_paths={"/", "/health", "/login", "/static", "/docs", "/openapi.json"}
    )

    # Include auth router
    app.include_router(auth_router)

    # Cleanup expired tokens periodically
    @app.on_event("startup")
    async def startup():
        print("[Security] ULE Security enabled")
        print(f"[Security] Token expiry: {TOKEN_EXPIRY_HOURS} hours")
        print(f"[Security] Rate limit: {MAX_REQUESTS_PER_MINUTE} requests/minute")
        print(f"[Security] Max failed logins: {MAX_FAILED_LOGINS}")
        print(f"[Security] Lockout duration: {LOCKOUT_MINUTES} minutes")
        print("[Security] Default admin password: 'admin' (change via ULE_ADMIN_PASSWORD env var)")

    @app.on_event("shutdown")
    async def shutdown():
        token_manager.cleanup()


def require_auth(func):
    """Decorator to require authentication for routes."""
    from functools import wraps

    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        if not hasattr(request.state, "user") or not request.state.user:
            raise HTTPException(
                status_code=401,
                detail="Authentication required"
            )
        return await func(request, *args, **kwargs)

    return wrapper


def validate_request_data(data: dict, schema: dict):
    """Validate request data against schema."""
    is_valid, errors = validate_json_input(data, schema)
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail={"validation_errors": errors}
        )
    return True
