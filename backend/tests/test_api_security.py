import os
import sys
import pytest
import asyncio
from starlette.datastructures import Headers
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import settings
from app.core.security import (
    sanitize_filename,
    validate_safe_url,
    RateLimiter,
    SecurityHeadersMiddleware,
    verify_api_key
)


def test_security_headers_middleware():
    """Verify that pure ASGI SecurityHeadersMiddleware injects required OWASP headers."""
    sent_messages = []
    async def dummy_send(msg):
        sent_messages.append(msg)

    async def dummy_receive():
        return {"type": "http.request"}

    async def dummy_app(scope, receive, send):
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    middleware = SecurityHeadersMiddleware(dummy_app)
    scope = {"type": "http", "method": "GET", "path": "/api/health"}

    async def run():
        await middleware(scope, dummy_receive, dummy_send)

    asyncio.run(run())

    assert len(sent_messages) >= 1
    headers_dict = dict(sent_messages[0]["headers"])
    assert b"x-content-type-options" in headers_dict
    assert headers_dict[b"x-content-type-options"] == b"nosniff"
    assert b"x-frame-options" in headers_dict
    assert headers_dict[b"x-frame-options"] == b"DENY"
    assert b"x-xss-protection" in headers_dict
    assert b"referrer-policy" in headers_dict
    assert b"server" in headers_dict
    assert b"AIStudyBuddy-API" in headers_dict[b"server"]


def test_cors_origins_configured():
    """Verify CORS origins are safely parsed and no empty origin strings exist."""
    origins = settings.cors_origins
    assert isinstance(origins, list)
    assert len(origins) >= 1
    for o in origins:
        assert len(o.strip()) > 0


def test_sanitize_filename():
    """Verify path traversal attacks and dangerous characters are sanitized."""
    assert sanitize_filename("../../etc/passwd") == "passwd"
    assert sanitize_filename("..\\..\\windows\\system32\\cmd.exe") == "cmd.exe"
    assert ".." not in sanitize_filename("....hidden_script.sh")
    
    safe = sanitize_filename("My Lecture Notes #1 (Spring 2026).pdf")
    assert ".." not in safe
    assert safe.endswith(".pdf")
    assert "/" not in safe and "\\" not in safe


def test_validate_safe_url_ssrf_protection():
    """Verify SSRF protection rejects private subnets, cloud metadata, and loopbacks."""
    # Localhost and loopback
    is_safe, msg = validate_safe_url("http://localhost:8000/api")
    assert not is_safe
    assert "localhost" in msg.lower() or "loopback" in msg.lower()

    is_safe, msg = validate_safe_url("http://127.0.0.1:3000/admin")
    assert not is_safe

    # AWS / Cloud Metadata endpoint (critical SSRF target)
    is_safe, msg = validate_safe_url("http://169.254.169.254/latest/meta-data/")
    assert not is_safe
    assert "private" in msg.lower() or "subnet" in msg.lower() or "not permitted" in msg.lower()

    # Unsupported schemes
    is_safe, msg = validate_safe_url("file:///etc/passwd")
    assert not is_safe
    assert "scheme" in msg.lower()


def test_rate_limiter_enforcement():
    """Verify RateLimiter blocks requests exceeding threshold with HTTP 429."""
    limiter = RateLimiter(requests_per_minute=3, window_seconds=60)

    class DummyRequest:
        def __init__(self, ip: str):
            self.client = type("Client", (), {"host": ip})()
            self.headers = Headers()

    req = DummyRequest("198.51.100.42")

    async def run_requests():
        # 3 allowed requests
        await limiter(req)
        await limiter(req)
        await limiter(req)

        # 4th request must raise 429
        with pytest.raises(HTTPException) as exc_info:
            await limiter(req)
        assert exc_info.value.status_code == 429
        assert "Rate limit exceeded" in str(exc_info.value.detail)
        assert "Retry-After" in exc_info.value.headers

    asyncio.run(run_requests())


def test_api_key_verification():
    """Verify API key authentication flow (valid, invalid, missing)."""
    original_key = settings.API_SECRET_KEY
    original_enabled = settings.API_KEY_AUTH_ENABLED

    async def run_auth_tests():
        try:
            # 1. Dev Mode (No secret key set) -> should allow open access
            settings.API_SECRET_KEY = ""
            settings.API_KEY_AUTH_ENABLED = False
            assert await verify_api_key(header_key=None, bearer_token=None) is True

            # 2. Production Mode (Secret key set)
            settings.API_SECRET_KEY = "test_super_secure_key_12345"
            settings.API_KEY_AUTH_ENABLED = True

            # Missing key -> 401
            with pytest.raises(HTTPException) as exc_401:
                await verify_api_key(header_key=None, bearer_token=None)
            assert exc_401.value.status_code == 401

            # Invalid key -> 403
            with pytest.raises(HTTPException) as exc_403:
                await verify_api_key(header_key="wrong_key", bearer_token=None)
            assert exc_403.value.status_code == 403

            # Valid X-API-Key header -> 200
            assert await verify_api_key(header_key="test_super_secure_key_12345", bearer_token=None) is True

            # Valid Authorization: Bearer token -> 200
            bearer = HTTPAuthorizationCredentials(scheme="Bearer", credentials="test_super_secure_key_12345")
            assert await verify_api_key(header_key=None, bearer_token=bearer) is True

        finally:
            settings.API_SECRET_KEY = original_key
            settings.API_KEY_AUTH_ENABLED = original_enabled

    asyncio.run(run_auth_tests())
