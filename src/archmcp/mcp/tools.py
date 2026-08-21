"""
ArchMCP - MCP Tool Definitions.

@author Shubham Upadhyay
@license MIT
"""

import json
from mcp.server import MCPServer

from ..services.search_service import SearchService
from ..services.repository_service import RepositoryService
from ..services.architecture_service import ArchitectureService
from ..services.knowledge_service import KnowledgeService
from ..services.context_service import ContextService

# Instantiate underlying business services
search_service = SearchService()
repo_service = RepositoryService()
arch_service = ArchitectureService()
knowledge_service = KnowledgeService()
context_service = ContextService()


def register_tools(server: MCPServer) -> None:
    """
    Registers all microservice exploration tools onto the given MCPServer.

    @param MCPServer server: The active MCP server instance
    @return None
    """

    # -------------------------------------------------------------------------
    # TOOL 1: Search Across All Microservices & Knowledge
    # -------------------------------------------------------------------------
    @server.tool(
        name="search_microservices",
        description="Search across all microservices, API routes, database schemas, and documentation by keyword or concept."
    )
    def search_microservices(query: str, limit: int = 5) -> str:
        """
        Search microservices matching query keywords.

        @param str query: Search phrase (e.g. 'payment gateway', 'auth login', 'order items')
        @param int limit: Maximum number of search results to return (default 5)
        @return str: Formatted JSON string of search results
        """
        results = search_service.search_microservices(query=query, limit=limit)
        if not results:
            return f"No microservices or components found matching '{query}'."
        return json.dumps(results, indent=2)

    # -------------------------------------------------------------------------
    # TOOL 2: List All Registered Microservices
    # -------------------------------------------------------------------------
    @server.tool(
        name="list_all_services",
        description="List all registered microservices in the organization with their IDs, owners, and tech stacks."
    )
    def list_all_services() -> str:
        """
        Returns a high-level summary catalog of all registered microservices in the company.

        @return str: Formatted JSON list of service summaries
        """
        services = repo_service.list_all_services()
        summary = [
            {
                "id": s.id,
                "name": s.name,
                "owner": s.owner,
                "language": s.language,
                "description": s.description
            }
            for s in services
        ]
        return json.dumps(summary, indent=2)

    # -------------------------------------------------------------------------
    # TOOL 3: Get Detailed Metadata for a Specific Service
    # -------------------------------------------------------------------------
    @server.tool(
        name="get_service_details",
        description="Retrieve comprehensive metadata, description, owner, repository URL, and tech stack for a specific microservice ID."
    )
    def get_service_details(service_id: str) -> str:
        """
        Get full metadata of a specific microservice.

        @param str service_id: Unique ID of the service (e.g. 'auth-service', 'payment-service')
        @return str: Formatted JSON service metadata
        """
        svc = repo_service.get_service_details(service_id)
        if not svc:
            return f"Error: Microservice with ID '{service_id}' was not found."
        return json.dumps(svc.model_dump(), indent=2)

    # -------------------------------------------------------------------------
    # TOOL 4: Get API Endpoints of a Service
    # -------------------------------------------------------------------------
    @server.tool(
        name="get_service_apis",
        description="Get all REST or gRPC API endpoints exposed by a microservice ID (e.g. auth-service, order-service)."
    )
    def get_service_apis(service_id: str) -> str:
        """
        Get API endpoints of a specific microservice.

        @param str service_id: Unique service ID (e.g. 'order-service')
        @return str: Formatted JSON list of API endpoints
        """
        apis = knowledge_service.get_service_apis(service_id)
        if apis is None:
            return f"Error: Microservice '{service_id}' not found."
        return json.dumps([a.model_dump() for a in apis], indent=2)

    # -------------------------------------------------------------------------
    # TOOL 5: Get Microservice Upstream/Downstream Dependencies
    # -------------------------------------------------------------------------
    @server.tool(
        name="get_service_dependencies",
        description="Get upstream and downstream dependency relationships for a given microservice."
    )
    def get_service_dependencies(service_id: str) -> str:
        """
        Get dependency map for a microservice.

        @param str service_id: Unique service ID (e.g. 'order-service')
        @return str: Formatted JSON dependency mapping
        """
        deps = arch_service.get_service_dependencies(service_id)
        if not deps:
            return f"Error: Microservice '{service_id}' not found."
        return json.dumps(deps, indent=2)

    # -------------------------------------------------------------------------
    # TOOL 6: Get Database Schema (Tables & Columns)
    # -------------------------------------------------------------------------
    @server.tool(
        name="get_database_schema",
        description="Get database tables, column definitions, and primary/foreign keys owned by a microservice."
    )
    def get_database_schema(service_id: str) -> str:
        """
        Get database tables for a microservice.

        @param str service_id: Unique service ID (e.g. 'payment-service')
        @return str: Formatted JSON list of database tables
        """
        tables = knowledge_service.get_database_schema(service_id)
        if tables is None:
            return f"Error: Microservice '{service_id}' not found."
        return json.dumps([t.model_dump() for t in tables], indent=2)

    # -------------------------------------------------------------------------
    # TOOL 7: Reverse Lookup - Find API Owner
    # -------------------------------------------------------------------------
    @server.tool(
        name="find_api_owner",
        description="Find which microservice owns or handles a given API route pattern (e.g. '/orders', 'login', 'refund')."
    )
    def find_api_owner(route_or_keyword: str) -> str:
        """
        Find microservices owning an API matching route or keyword.

        @param str route_or_keyword: URL fragment or operation (e.g. '/refund', 'charge', 'users')
        @return str: Formatted JSON list of matching services
        """
        matches = knowledge_service.find_api_by_route(route_or_keyword)
        if not matches:
            return f"No microservice found owning API route matching '{route_or_keyword}'."
        return json.dumps(matches, indent=2)

    # -------------------------------------------------------------------------
    # TOOL 8: Reverse Lookup - Find Database Table Owner
    # -------------------------------------------------------------------------
    @server.tool(
        name="find_table_owner",
        description="Find which microservice owns a given database table name (e.g. 'users', 'transactions', 'orders')."
    )
    def find_table_owner(table_name: str) -> str:
        """
        Find microservices owning a database table.

        @param str table_name: Table name to search (e.g. 'transactions', 'orders')
        @return str: Formatted JSON list of matching services
        """
        matches = knowledge_service.find_table_owner(table_name)
        if not matches:
            return f"No microservice found owning database table '{table_name}'."
        return json.dumps(matches, indent=2)

    # -------------------------------------------------------------------------
    # TOOL 9: Full Context Package for AI Assistants
    # -------------------------------------------------------------------------
    @server.tool(
        name="get_full_context_package",
        description="Get an aggregated full context package (service metadata, docs, and implementation guidelines) for an AI assistant working on a service."
    )
    def get_full_context_package(service_id: str) -> str:
        """
        Get full aggregated context package for a microservice.

        @param str service_id: Unique service ID (e.g. 'auth-service')
        @return str: Formatted JSON context bundle
        """
        ctx = context_service.assemble_service_context(service_id)
        if not ctx:
            return f"Error: Microservice '{service_id}' not found."
        return json.dumps(ctx, indent=2)

    # -------------------------------------------------------------------------
    # TOOL 10: Blast Radius & Breaking Impact Analyzer
    # -------------------------------------------------------------------------
    @server.tool(
        name="analyze_blast_radius",
        description="Analyze the transitive blast radius and ripple effect across dependent microservices when modifying an API route, schema, or service."
    )
    def analyze_blast_radius(service_id: str, component: str = "") -> str:
        """
        Calculates direct and indirect downstream microservices and engineering teams impacted by a change.

        @param str service_id: Service ID being modified (e.g. 'auth-service', 'order-service')
        @param str component: Optional specific endpoint or table name (e.g. '/api/v1/auth/verify', 'users')
        @return str: Formatted JSON blast radius report
        """
        report = arch_service.analyze_blast_radius(service_id=service_id, component=component)
        if not report:
            return f"Error: Microservice '{service_id}' not found."
        return json.dumps(report.model_dump(), indent=2)

    # -------------------------------------------------------------------------
    # TOOL 11: Distributed Workflow Sequence Diagram Generator
    # -------------------------------------------------------------------------
    @server.tool(
        name="generate_sequence_diagram",
        description="Generate a Mermaid sequence diagram visualizing the communication flow between microservices for a given business workflow (e.g. checkout, refund, login)."
    )
    def generate_sequence_diagram(flow_name: str) -> str:
        """
        Generates Mermaid sequence diagram representing multi-service interaction.

        @param str flow_name: Name of workflow or business process (e.g. 'checkout', 'refund', 'user_login')
        @return str: Formatted JSON sequence diagram model
        """
        diagram = arch_service.generate_sequence_diagram(flow_name=flow_name)
        return json.dumps(diagram.model_dump(), indent=2)
