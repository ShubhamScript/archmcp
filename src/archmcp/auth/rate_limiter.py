"""
ArchMCP - Sliding Window Rate Limiting Middleware.

Enforces per-client / per-token rate limits, protects SSE endpoints from abuse,
and emits standard RFC-compliant rate limit headers.

@author Shubham Upadhyay
@license MIT
"""

import time
import threading
from typing import Dict, List, Tuple
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from .audit import audit_logger, AuditEventType
from ..config.settings import settings


class InMemoryRateLimiter:
    """
    Thread-safe sliding window rate limiter tracking request timestamps per client key/IP.
    """

    def __init__(self, limit: int = 60, window_seconds: int = 60) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._lock = threading.RLock()
        # Maps client_identifier -> list of epoch timestamps
        self._clients: Dict[str, List[float]] = {}

    def is_allowed(self, identifier: str) -> Tuple[bool, int, int]:
        """
        Determines if request from identifier is allowed under sliding window.

        @param str identifier: Unique client identifier (Token ID or IP)
        @return Tuple[bool, int, int]: (allowed_bool, remaining_count, reset_seconds)
        """
        now = time.time()
        window_start = now - self.window_seconds

        with self._lock:
            timestamps = self._clients.get(identifier, [])
            # Filter timestamps outside sliding window
            timestamps = [ts for ts in timestamps if ts > window_start]

            current_count = len(timestamps)
            if current_count >= self.limit:
                oldest = timestamps[0] if timestamps else now
                reset_seconds = max(1, int(oldest + self.window_seconds - now))
                self._clients[identifier] = timestamps
                return False, 0, reset_seconds

            # Add current timestamp
            timestamps.append(now)
            self._clients[identifier] = timestamps

            remaining = max(0, self.limit - len(timestamps))
            reset_seconds = self.window_seconds
            return True, remaining, reset_seconds

    def reset(self) -> None:
        """
        Clears all rate limit trackers (used for testing).

        @return None
        """
        with self._lock:
            self._clients.clear()


# Global rate limiter instance
limiter = InMemoryRateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    ASGI middleware intercepting incoming HTTP/SSE requests to enforce rate limits.
    """

    PUBLIC_BYPASS_PATHS = ["/health", "/health/live", "/health/ready", "/docs", "/openapi.json"]

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Checks rate limit before passing to next ASGI handler.

        @param Request request: Incoming request
        @param Callable call_next: Next ASGI handler
        @return Response: HTTP response with rate limit headers or 429
        """
        if request.url.path in self.PUBLIC_BYPASS_PATHS:
            return await call_next(request)

        # Identify client by Bearer token ID (if set) or client IP
        auth_user = getattr(request.state, "user", None)
        client_ip = request.client.host if request.client else "127.0.0.1"
        identifier = auth_user.token_id if (auth_user and hasattr(auth_user, "token_id")) else f"ip:{client_ip}"

        allowed, remaining, reset_secs = limiter.is_allowed(identifier)

        if not allowed:
            # Record security audit event
            audit_logger.log(
                event_type=AuditEventType.RATE_LIMITED,
                action=f"rate_limit:{request.url.path}",
                actor=identifier,
                client_ip=client_ip,
                status="DENIED",
                details={"limit": limiter.limit, "reset_seconds": reset_secs}
            )
            response = JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "message": f"Rate limit exceeded. Try again in {reset_secs} seconds.",
                    "retry_after": reset_secs
                }
            )
            response.headers["Retry-After"] = str(reset_secs)
            response.headers["X-RateLimit-Limit"] = str(limiter.limit)
            response.headers["X-RateLimit-Remaining"] = "0"
            response.headers["X-RateLimit-Reset"] = str(int(time.time() + reset_secs))
            return response

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limiter.limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + reset_secs))
        return response
