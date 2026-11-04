import os
import re
import time
import socket
import ipaddress
import secrets
import logging
from typing import Optional, Dict, List, Tuple
from urllib.parse import urlparse

from fastapi import Request, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings

logger = logging.getLogger("API.Security")

# Security schemes for Swagger UI and header extraction
api_key_header_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_auth_scheme = HTTPBearer(auto_error=False)


# ==============================================================================
# 1. API Key Authentication
# ==============================================================================
async def verify_api_key(
    header_key: Optional[str] = Security(api_key_header_scheme),
    bearer_token: Optional[HTTPAuthorizationCredentials] = Security(bearer_auth_scheme)
) -> bool:
    """
    Enforces API authentication if API_SECRET_KEY is defined or API_KEY_AUTH_ENABLED is True.
    Supports both 'X-API-Key: <key>' and 'Authorization: Bearer <key>'.
    Falls back gracefully to open mode if no API_SECRET_KEY is configured (dev mode).
    """
    expected_key = getattr(settings, "API_SECRET_KEY", "").strip()
    auth_enabled = getattr(settings, "API_KEY_AUTH_ENABLED", False) or bool(expected_key)

    # In local development without an active secret key configured, allow unauthenticated access
    if not auth_enabled or not expected_key:
        return True

    candidate_key = None
    if header_key:
        candidate_key = header_key.strip()
    elif bearer_token and bearer_token.credentials:
        candidate_key = bearer_token.credentials.strip()

    if not candidate_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided. Pass 'X-API-Key' or 'Authorization: Bearer <token>' header.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Constant-time comparison to protect against timing attacks
    if not secrets.compare_digest(candidate_key, expected_key):
        logger.warning("Unauthorized API attempt with invalid secret key.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Invalid API key."
        )

    return True


# ==============================================================================
# 2. Sliding-Window In-Memory Rate Limiter
# ==============================================================================
class RateLimiter:
    """
    Thread-safe, high-performance in-memory sliding window rate limiter.
    Limits requests per IP address to safeguard against DoS attacks and LLM quota exhaustion.
    """
    def __init__(self, requests_per_minute: int = 120, window_seconds: int = 60):
        self.limit = requests_per_minute
        self.window = window_seconds
        self._records: Dict[str, List[float]] = {}
        self._last_cleanup = time.time()

    def _cleanup_stale(self, now: float):
        """Purge tracking records older than the active window to prevent memory leaks."""
        if now - self._last_cleanup < 30.0:
            return
        self._last_cleanup = now
        cutoff = now - self.window
        stale_keys = []
        for ip, timestamps in self._records.items():
            valid_ts = [t for t in timestamps if t > cutoff]
            if valid_ts:
                self._records[ip] = valid_ts
            else:
                stale_keys.append(ip)
        for ip in stale_keys:
            self._records.pop(ip, None)

    def _get_client_ip(self, request: Request) -> str:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Use the first client IP in the proxy chain
            return forwarded_for.split(",")[0].strip()
        if request.client and request.client.host:
            return request.client.host
        return "127.0.0.1"

    async def __call__(self, request: Request):
        if not getattr(settings, "RATE_LIMIT_ENABLED", True):
            return

        now = time.time()
        self._cleanup_stale(now)
        client_ip = self._get_client_ip(request)

        timestamps = self._records.get(client_ip, [])
        cutoff = now - self.window
        # Keep only timestamps within the rolling window
        timestamps = [t for t in timestamps if t > cutoff]

        if len(timestamps) >= self.limit:
            oldest_ts = timestamps[0]
            retry_after = max(1, int(self.window - (now - oldest_ts)))
            logger.warning("Rate limit exceeded for IP %s (%d requests in %ds)", client_ip, len(timestamps), self.window)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {self.limit} requests per {self.window}s.",
                headers={"Retry-After": str(retry_after)}
            )

        timestamps.append(now)
        self._records[client_ip] = timestamps


# Default rate limiters
standard_rate_limiter = RateLimiter(requests_per_minute=settings.RATE_LIMIT_PER_MINUTE)
expensive_rate_limiter = RateLimiter(requests_per_minute=settings.RATE_LIMIT_EXPENSIVE_PER_MINUTE)


# ==============================================================================
# 3. HTTP Security Headers Middleware (Pure ASGI - Zero Overhead)
# ==============================================================================
class SecurityHeadersMiddleware:
    """
    Pure ASGI middleware that injects OWASP-recommended security headers into all responses.
    Prevents clickjacking, MIME-type sniffing, cross-site leaks, and server banner fingerprinting.
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.extend([
                    (b"x-content-type-options", b"nosniff"),
                    (b"x-frame-options", b"DENY"),
                    (b"x-xss-protection", b"1; mode=block"),
                    (b"referrer-policy", b"strict-origin-when-cross-origin"),
                    (b"permissions-policy", b"geolocation=(), camera=(), microphone=()"),
                    (b"server", b"AIStudyBuddy-API")
                ])
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper)


# ==============================================================================
# 4. Input Sanitization & Anti-Path-Traversal
# ==============================================================================
def sanitize_filename(filename: str) -> str:
    """
    Sanitizes user-provided filenames to prevent Directory Traversal attacks (e.g., ../../etc/passwd)
    and strips dangerous characters.
    """
    if not filename:
        return f"file_{secrets.token_hex(4)}"

    # Strip directory path separators
    basename = os.path.basename(filename.replace("\\", "/"))
    # Normalize unicode and keep only safe characters
    cleaned = re.sub(r"[^A-Za-z0-9._\-]", "_", basename)
    # Prevent hidden files or double extensions like ..
    cleaned = re.sub(r"\.{2,}", ".", cleaned).lstrip(".")
    if not cleaned:
        cleaned = f"file_{secrets.token_hex(4)}"

    # Restrict length
    return cleaned[:128]


# ==============================================================================
# 5. Anti-SSRF (Server-Side Request Forgery) URL Validator
# ==============================================================================
BLOCKED_IP_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),       # AWS/Cloud Metadata Service
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("224.0.0.0/4"),          # Multicast
    ipaddress.ip_network("240.0.0.0/4"),          # Reserved
    ipaddress.ip_network("::1/128"),              # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),             # IPv6 Unique local
    ipaddress.ip_network("fe80::/10"),            # IPv6 Link-local
]


def validate_safe_url(url_string: str) -> Tuple[bool, str]:
    """
    Validates that a URL uses http/https and does NOT resolve to a private,
    loopback, link-local, or cloud-metadata IP (Anti-SSRF).
    """
    url_string = url_string.strip()
    if not url_string:
        return False, "URL cannot be empty."

    try:
        parsed = urlparse(url_string)
    except Exception:
        return False, "Malformed URL format."

    if parsed.scheme.lower() not in ("http", "https"):
        return False, f"Unsupported scheme '{parsed.scheme}'. Only http and https are allowed."

    hostname = parsed.hostname
    if not hostname:
        return False, "URL must include a valid host."

    if hostname.lower() in ("localhost", "127.0.0.1", "::1", "metadata.google.internal"):
        return False, "Access to localhost and internal loopback addresses is forbidden."

    # Fast IP format check before DNS resolution
    try:
        ip_obj = ipaddress.ip_address(hostname)
        for blocked_net in BLOCKED_IP_NETWORKS:
            if ip_obj in blocked_net:
                return False, f"Target IP {hostname} belongs to a private/restricted subnet and is not permitted."
        return True, "URL is safe."
    except ValueError:
        pass

    # Resolve hostname to IP and verify against private/restricted ranges
    try:
        resolved_ips = socket.getaddrinfo(hostname, None)
        for item in resolved_ips:
            ip_str = item[4][0]
            ip_obj = ipaddress.ip_address(ip_str)
            for blocked_net in BLOCKED_IP_NETWORKS:
                if ip_obj in blocked_net:
                    return False, f"Target IP {ip_str} belongs to a private/restricted subnet and is not permitted."
    except socket.gaierror:
        return False, f"Unable to resolve host: '{hostname}'."
    except Exception as e:
        return False, f"Security verification error: {str(e)}"

    return True, "URL is safe."
