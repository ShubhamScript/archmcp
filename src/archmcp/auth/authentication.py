"""
ArchMCP - Remote MCP Authentication Middleware.

@author Shubham Upadhyay
@license MIT
"""

import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from .token_verifier import TokenVerifier
from ..config.settings import settings


class RemoteMCPAuthMiddleware(BaseHTTPMiddleware):
    """
    Protects MCP endpoints (SSE and message postbacks) requiring valid bearer tokens.
    Attaches authenticated principal context to request state.
    """

    # Endpoints that are accessible publicly without a token (e.g. health checks, dashboard)
    PUBLIC_PATHS = [
        "/health",
        "/health/live",
        "/health/ready",
        "/docs",
        "/openapi.json",
        "/",
        "/dashboard",
        "/api/dashboard/data",
        "/api/dashboard/run-tool"
    ]

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Validates Bearer token in headers or ?token= query parameter.

        @param Request request: Incoming HTTP request
        @param Callable call_next: Next ASGI handler
        @return Response: HTTP response or 401 Unauthorized
        """
        # Generate or capture correlation request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        # If authentication is disabled in config, or if path is public, let request through
        if not settings.AUTH_ENABLED or request.url.path in self.PUBLIC_PATHS:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response

        # 1. Check Authorization header (e.g. 'Bearer arch_live_...')
        auth_header = request.headers.get("Authorization")
        
        # 2. Check query parameter (e.g. ?token=arch_live_... or ?api_key=...)
        query_token = request.query_params.get("token") or request.query_params.get("api_key")

        token_to_check = auth_header or query_token
        client_ip = request.client.host if request.client else "127.0.0.1"

        # Verify token against configured valid list
        user = TokenVerifier.verify(
            token=token_to_check,
            client_ip=client_ip,
            request_id=request_id
        )
        if not user:
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Unauthorized",
                    "message": "Valid Bearer token ('arch_*' or OIDC JWT) or ?token= query parameter required to access ArchMCP Server."
                },
                headers={"X-Request-ID": request_id}
            )

        # Attach validated user info to request state so downstream handlers know who connected
        request.state.user = user
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
