"""
ArchMCP - MCP Server Initialization & ASGI Application Factory.

@author Shubham Upadhyay
@license MIT
"""

import logging
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.middleware import Middleware
from mcp.server import MCPServer

from .tools import register_tools
from .resources import register_resources
from .prompts import register_prompts
from ..auth.authentication import RemoteMCPAuthMiddleware
from ..auth.rate_limiter import RateLimitMiddleware
from ..auth.key_store import keystore
from ..config.settings import settings
from ..storage.database import db
from ..web.dashboard import dashboard_view, dashboard_data_endpoint, dashboard_run_tool_endpoint

logger = logging.getLogger(__name__)


def create_mcp_server() -> MCPServer:
    """
    Instantiates and configures the official Model Context Protocol server.

    @return MCPServer: Fully configured MCP server instance
    """
    server = MCPServer(
        name=settings.APP_NAME,
        instructions="""You are connected to ArchMCP — the centralized Microservices Knowledge & Architecture Brain.
Use the provided tools, resources, and prompts to answer questions about internal microservices, find APIs, inspect database schemas, understand service dependencies, and retrieve architecture guidelines.
When answering questions about the architecture, always check service dependencies and API definitions first."""
    )

    # Attach all tools (functions callable by the LLM)
    register_tools(server)

    # Attach all resources (URI documents readable like files)
    register_resources(server)

    # Attach all prompts (workflow templates surfaced to LLMs)
    register_prompts(server)

    return server


async def health_check(request):
    """
    Public health check endpoint for monitoring and container probes.

    @param Request request: Incoming HTTP request
    @return JSONResponse: Server health status payload
    """
    service_count = len(db.list_services())
    key_count = len(keystore.list_keys(include_revoked=False))
    return JSONResponse({
        "status": "healthy",
        "app": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "indexed_services": service_count,
        "active_api_keys": key_count,
        "auth_enabled": settings.AUTH_ENABLED,
        "rate_limiting_enabled": settings.RATE_LIMIT_ENABLED,
        "oidc_enabled": settings.OIDC_ENABLED
    })


async def health_live(request):
    """Kubernetes liveness probe."""
    return JSONResponse({"status": "alive"})


async def health_ready(request):
    """Kubernetes readiness probe checking metadata DB and KeyStore readiness."""
    is_ready = len(db.list_services()) >= 0
    return JSONResponse({
        "status": "ready" if is_ready else "not_ready",
        "ready": is_ready
    })


def create_asgi_app() -> Starlette:
    """
    Assembles the complete Starlette ASGI application with SSE routes, middleware, and dashboard.

    @return Starlette: Configured ASGI application
    """
    mcp_server = create_mcp_server()
    sse_app = mcp_server.sse_app()

    routes = [
        Route("/", endpoint=dashboard_view, methods=["GET"]),
        Route("/dashboard", endpoint=dashboard_view, methods=["GET"]),
        Route("/api/dashboard/data", endpoint=dashboard_data_endpoint, methods=["GET"]),
        Route("/api/dashboard/run-tool", endpoint=dashboard_run_tool_endpoint, methods=["POST"]),
        Route("/health", endpoint=health_check, methods=["GET"]),
        Route("/health/live", endpoint=health_live, methods=["GET"]),
        Route("/health/ready", endpoint=health_ready, methods=["GET"]),
    ] + list(sse_app.routes)

    middleware = [
        Middleware(RemoteMCPAuthMiddleware),
    ]

    if settings.RATE_LIMIT_ENABLED:
        middleware.append(Middleware(RateLimitMiddleware))

    app = Starlette(
        debug=settings.DEBUG,
        routes=routes,
        middleware=middleware
    )
    return app
