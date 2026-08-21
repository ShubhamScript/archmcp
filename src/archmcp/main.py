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


# Initialize knowledge base once at module load time
initialize_knowledge_base()

# Create Starlette ASGI application
app = create_asgi_app()


def main():
    """
    Starts the Uvicorn ASGI server.

    @return None
    """
    logger.info("=" * 60)
    logger.info(f"🚀 Starting {settings.APP_NAME}")
    logger.info(f"🌐 Remote MCP SSE Endpoint : http://{settings.HOST}:{settings.PORT}/sse")
    logger.info(f"📊 Web Visualizer          : http://{settings.HOST}:{settings.PORT}/dashboard")
    logger.info(f"❤️  Health Check Endpoint   : http://{settings.HOST}:{settings.PORT}/health")
    logger.info(f"🔒 Authentication Enabled  : {settings.AUTH_ENABLED}")
    if settings.AUTH_ENABLED:
        logger.info(f"🔑 Configured Tokens       : {settings.AUTH_TOKENS}")
    logger.info("=" * 60)

    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        log_level="info"
    )


if __name__ == "__main__":
    main()
