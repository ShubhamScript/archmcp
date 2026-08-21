"""
ArchMCP - MCP Resource Definitions.

@author Shubham Upadhyay
@license MIT
"""

import json
from mcp.server import MCPServer
from ..services.architecture_service import ArchitectureService
from ..services.repository_service import RepositoryService
from ..storage.database import db

arch_service = ArchitectureService()
repo_service = RepositoryService()


def register_resources(server: MCPServer) -> None:
    """
    Registers URI-addressable read-only resources onto the MCP server.

    @param MCPServer server: The active MCP server instance
    @return None
    """

    # -------------------------------------------------------------------------
    # RESOURCE 1: System-Wide Architecture Overview Graph
    # -------------------------------------------------------------------------
    @server.resource("archmcp://architecture/overview")
    def get_architecture_overview() -> str:
        """
        Global microservice architecture topology and communication paths.

        @return str: Formatted JSON architecture graph
        """
        graph = arch_service.get_system_architecture()
        return json.dumps(graph.model_dump(), indent=2)

    # -------------------------------------------------------------------------
    # RESOURCE 2: Full Microservices Catalog
    # -------------------------------------------------------------------------
    @server.resource("archmcp://services/catalog")
    def get_services_catalog() -> str:
        """
        Catalog of all microservices, owners, tech stacks, and repository locations.

        @return str: Formatted JSON service catalog
        """
        services = repo_service.list_all_services()
        return json.dumps([s.model_dump() for s in services], indent=2)

    # -------------------------------------------------------------------------
    # RESOURCE 3: Engineering & Architecture Guidelines
    # -------------------------------------------------------------------------
    @server.resource("archmcp://guidelines/microservices")
    def get_engineering_guidelines() -> str:
        """
        Standard company-wide engineering patterns, API guidelines, and communication protocols.

        @return str: Markdown text of engineering guidelines
        """
        return """# Microservice Engineering Standards

1. **Authentication**:
   - All external client requests must carry a JWT verified by `auth-service`.
   - Internal inter-service calls pass the original request context or internal mTLS identity.

2. **Communication Protocols**:
   - Synchronous RPC / Query: Use RESTful JSON APIs.
   - Asynchronous Events: Publish domain events to Kafka topics (e.g., `orders.created`, `payment.succeeded`).

3. **Database Ownership**:
   - Each microservice strictly owns its database tables.
   - Direct database joins across service boundaries are PROHIBITED. Query via API or event replication.

4. **Idempotency**:
   - All state-modifying operations (such as payments or inventory deductions) must support `Idempotency-Key` headers.
"""

    # -------------------------------------------------------------------------
    # RESOURCE 4: Service-Specific Markdown Documentation
    # -------------------------------------------------------------------------
    @server.resource("archmcp://services/{service_id}/docs")
    def get_service_docs(service_id: str) -> str:
        """
        Documentation and architecture summary for a specific microservice.

        @param str service_id: Target microservice identifier
        @return str: Markdown documentation text
        """
        docs = db.list_documents(service_id=service_id)
        if not docs:
            svc = db.get_service(service_id)
            if not svc:
                return f"# Microservice '{service_id}' not found."
            return f"# {svc.name}\nNo additional documents found."
        return "\n\n---\n\n".join([d.content for d in docs])
