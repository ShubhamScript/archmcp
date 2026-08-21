"""Tests for ArchMCP endpoints, authentication middleware, tools, resources, prompts, and dashboard."""

import pytest
from starlette.testclient import TestClient
from archmcp.main import app, initialize_knowledge_base
from archmcp.mcp.tools import register_tools
from archmcp.mcp.resources import register_resources
from archmcp.mcp.prompts import register_prompts
from archmcp.ingestion.openapi_importer import OpenAPIImporter
from mcp.server import MCPServer
from archmcp.config.settings import settings


@pytest.fixture
def client():
    return TestClient(app, base_url="http://localhost:8000")


def test_health_endpoint_public(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["indexed_services"] > 0


def test_dashboard_endpoint_public(client):
    # /dashboard and / should return HTML
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "ArchMCP" in response.text

    # /api/dashboard/data returns aggregated JSON
    res_data = client.get("/api/dashboard/data")
    assert res_data.status_code == 200
    json_data = res_data.json()
    assert "services" in json_data
    assert json_data["total_apis"] > 0


def test_dashboard_run_tool_endpoint(client):
    # Test interactive tool runner from browser dashboard
    res = client.post("/api/dashboard/run-tool", json={
        "tool": "analyze_blast_radius",
        "arg": "auth-service"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "impact_severity" in data["result"]


def test_unauthorized_access_rejected(client):
    # Without token, requests to protected routes return 401 Unauthorized
    response = client.get("/sse")
    assert response.status_code == 401
    data = response.json()
    assert data["error"] == "Unauthorized"


@pytest.mark.asyncio
async def test_mcp_server_tools_registered():
    server = MCPServer("test-archmcp")
    register_tools(server)
    register_resources(server)
    register_prompts(server)

    tools = await server.list_tools()
    tool_names = [t.name for t in tools]
    assert "search_microservices" in tool_names
    assert "list_all_services" in tool_names
    assert "get_service_details" in tool_names
    assert "get_service_apis" in tool_names
    assert "get_service_dependencies" in tool_names
    assert "get_database_schema" in tool_names
    assert "find_api_owner" in tool_names
    assert "find_table_owner" in tool_names
    assert "get_full_context_package" in tool_names
    assert "analyze_blast_radius" in tool_names
    assert "generate_sequence_diagram" in tool_names


@pytest.mark.asyncio
async def test_mcp_server_tool_invocation():
    initialize_knowledge_base()
    server = MCPServer("test-archmcp")
    register_tools(server)

    # 1. Search tool
    result = await server.call_tool("search_microservices", {"query": "auth"})
    assert result is not None
    assert len(result.content) > 0
    assert "auth-service" in result.content[0].text

    # 2. Blast Radius tool
    result_blast = await server.call_tool("analyze_blast_radius", {"service_id": "auth-service"})
    assert "impact_severity" in result_blast.content[0].text
    assert "CRITICAL" in result_blast.content[0].text

    # 3. Sequence diagram tool
    result_seq = await server.call_tool("generate_sequence_diagram", {"flow_name": "checkout"})
    assert "sequenceDiagram" in result_seq.content[0].text


@pytest.mark.asyncio
async def test_mcp_server_prompts():
    server = MCPServer("test-archmcp")
    register_prompts(server)

    prompts = await server.list_prompts()
    prompt_names = [p.name for p in prompts]
    assert "cross_service_feature_planner" in prompt_names
    assert "distributed_incident_triage" in prompt_names
    assert "api_contract_refactor" in prompt_names

    # Test prompt generation
    prompt_res = await server.get_prompt("cross_service_feature_planner", {
        "feature_description": "Add multi-currency payment support",
        "primary_service": "payment-service"
    })
    assert prompt_res is not None
    assert len(prompt_res.messages) > 0


def test_openapi_importer():
    sample_spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "Delivery Tracking Service",
            "version": "2.1.0",
            "description": "Real-time delivery driver location and route optimization"
        },
        "paths": {
            "/api/v1/deliveries/{id}/location": {
                "get": {
                    "summary": "Get driver live coordinates",
                    "description": "Returns latitude, longitude, and ETA."
                }
            }
        },
        "components": {
            "schemas": {
                "DeliveryLocation": {
                    "description": "Driver GPS coordinates",
                    "properties": {
                        "latitude": {"type": "number"},
                        "longitude": {"type": "number"},
                        "driver_id": {"type": "string"}
                    }
                }
            }
        }
    }

    service = OpenAPIImporter.parse_spec_dict(sample_spec, default_owner="Logistics Fleet")
    assert service.id == "delivery-tracking-service"
    assert len(service.apis) == 1
    assert service.apis[0].path == "/api/v1/deliveries/{id}/location"
    assert len(service.database_tables) == 1
    assert service.database_tables[0].name == "deliverylocation"
