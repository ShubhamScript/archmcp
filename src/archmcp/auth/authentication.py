"""
ArchMCP - Remote MCP Authentication Middleware.

@author Shubham Upadhyay
@license MIT
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from .token_verifier import TokenVerifier
from ..config.settings import settings


class RemoteMCPAuthMiddleware(BaseHTTPMiddleware):
    """
    Protects MCP endpoints (SSE and message postbacks) requiring valid bearer tokens.
    """

    # Endpoints that are accessible publicly without a token (e.g. health checks, dashboard)
    PUBLIC_PATHS = ["/health", "/docs", "/openapi.json", "/", "/dashboard", "/api/dashboard/data", "/api/dashboard/run-tool"]

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Validates Bearer token in headers or ?token= query parameter.

        @param Request request: Incoming HTTP request
        @param Callable call_next: Next ASGI handler
        @return Response: HTTP response or 401 Unauthorized
        """
        # If authentication is disabled in config, or if path is public, let request through
        if not settings.AUTH_ENABLED or request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)

        # 1. Check Authorization header (e.g. 'Bearer dev-token-secret-123')
        auth_header = request.headers.get("Authorization")
        
        # 2. Check query parameter (e.g. ?token=dev-token-secret-123 or ?api_key=...)
        query_token = request.query_params.get("token") or request.query_params.get("api_key")

        token_to_check = auth_header or query_token

        # Verify token against configured valid list
        user = TokenVerifier.verify(token_to_check)
        if not user:
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Unauthorized",
                    "message": "Valid Bearer token or ?token= query parameter required to access ArchMCP Server."
                }
            )

        # Attach validated user info to request state so downstream handlers know who connected
        request.state.user = user
        return await call_next(request)
