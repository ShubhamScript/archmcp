"""
ArchMCP - Main Entry Point & Server Bootstrap.

@author Shubham Upadhyay
@license MIT
"""

import sys
import logging
import uvicorn

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from .config.settings import settings
from .repositories.repository_registry import RepositoryRegistry
from .ingestion.repository_scanner import RepositoryScanner
from .mcp.server import create_asgi_app
from .auth.key_store import keystore
from .auth.permissions import Scope

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("archmcp")


def initialize_knowledge_base() -> None:
    """
    Initializes and indexes the microservices knowledge base from the configured data file.

    @return None
    """
    logger.info("Initializing microservices architecture knowledge base...")
    registry = RepositoryRegistry(config_path=settings.REPOSITORIES_FILE)
    scanner = RepositoryScanner(registry=registry)
    count = scanner.scan_and_index_all()
    logger.info(f"Loaded and indexed {count} microservices from {settings.REPOSITORIES_FILE}.")


def bootstrap_security() -> None:
    """
    Ensures at least one root admin API key exists on initial bootstrap.

    @return None
    """
    if not settings.AUTH_ENABLED:
        return

    active_keys = keystore.list_keys(include_revoked=False)
    if not active_keys and settings.BOOTSTRAP_ADMIN_KEY:
        record, raw_token = keystore.create_key(
            name="Initial Root Admin Key",
            scopes=[Scope.ALL.value],
            owner="admin",
            tenant_id="default",
            environment=settings.ENVIRONMENT
        )
        print("\n" + "=" * 68)
        print("🔐 ARCHMCP SECURITY BOOTSTRAP INITIALIZATION")
        print("=" * 68)
        print(f"Generated initial root API key: '{record.name}' (kid: {record.kid})")
        print(f"Token: {raw_token}")
        print("Save this token to configure your MCP clients (e.g. Claude Desktop).")
        print("=" * 68 + "\n")


# Initialize knowledge base once at module load time
initialize_knowledge_base()
bootstrap_security()

# Create Starlette ASGI application
app = create_asgi_app()


def main():
    """
    Starts the Uvicorn ASGI server.

    @return None
    """
    active_keys = len(keystore.list_keys(include_revoked=False))
    logger.info("=" * 65)
    logger.info(f"🚀 Starting {settings.APP_NAME}")
    logger.info(f"🌐 Remote MCP SSE Endpoint : http://{settings.HOST}:{settings.PORT}/sse")
    logger.info(f"📊 Web Visualizer          : http://{settings.HOST}:{settings.PORT}/dashboard")
    logger.info(f"❤️  Health Check Endpoint   : http://{settings.HOST}:{settings.PORT}/health")
    logger.info(f"🔒 Authentication Enabled  : {settings.AUTH_ENABLED} ({active_keys} active keys)")
    logger.info(f"⚡ Rate Limiting           : {settings.RATE_LIMIT_ENABLED} ({settings.RATE_LIMIT_PER_MINUTE} req/min)")
    logger.info("=" * 65)

    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        log_level="info"
    )


if __name__ == "__main__":
    main()
