"""
ArchMCP - MCP Prompt Definitions.

@author Shubham Upadhyay
@license MIT
"""

import json
from typing import List, Dict, Any
from mcp.server import MCPServer
from ..storage.database import db
from ..services.architecture_service import ArchitectureService

arch_service = ArchitectureService()


def register_prompts(server: MCPServer) -> None:
    """
    Registers reusable engineering workflow prompts on the MCPServer.

    @param MCPServer server: The active MCP server instance
    @return None
    """

    # -------------------------------------------------------------------------
    # PROMPT 1: Cross-Service Feature Planner
    # -------------------------------------------------------------------------
    @server.prompt(
        name="cross_service_feature_planner",
        description="Plan and scaffold a new feature that touches multiple microservices with contract consistency."
    )
    def cross_service_feature_planner(feature_description: str, primary_service: str) -> List[Dict[str, Any]]:
        """
        Scaffolds a comprehensive architectural implementation plan for a feature across microservices.

        @param str feature_description: Description of feature to build
        @param str primary_service: Initiating microservice ID
        @return List[Dict[str, Any]]: MCP prompt message structure
        """
        svc = db.get_service(primary_service)
        deps = arch_service.get_service_dependencies(primary_service) if svc else {}
        svc_name = svc.name if svc else primary_service

        system_instruction = (
            f"You are an Expert Distributed Systems Architect assisting with implementing: '{feature_description}'.\n\n"
            f"Primary Service: {svc_name} (`{primary_service}`)\n"
            f"Upstream Dependencies: {deps.get('declared_upstream', [])}\n"
            f"Downstream Dependencies: {deps.get('declared_downstream', [])}\n\n"
            "Please follow these microservice architecture guidelines:\n"
            "1. Identify every microservice that needs schema, route, or message updates.\n"
            "2. Define strict REST/gRPC API payloads and ensure backwards compatibility.\n"
            "3. Specify database transactions, idempotency requirements, and rollback strategies.\n"
            "4. Define event structures for any asynchronous message queues (Kafka/RabbitMQ).\n"
            "5. Provide step-by-step rollout and zero-downtime migration instructions."
        )

        return [
            {
                "role": "user",
                "content": system_instruction
            }
        ]

    # -------------------------------------------------------------------------
    # PROMPT 2: Distributed Incident Triage
    # -------------------------------------------------------------------------
    @server.prompt(
        name="distributed_incident_triage",
        description="Diagnose and troubleshoot a production issue or latency spike across service dependency chains."
    )
    def distributed_incident_triage(symptom: str, failing_service: str) -> List[Dict[str, Any]]:
        """
        Guides the AI model through systematic root-cause analysis for distributed system incidents.

        @param str symptom: Production symptom or error message
        @param str failing_service: Suspect or failing microservice ID
        @return List[Dict[str, Any]]: MCP prompt message structure
        """
        report = arch_service.analyze_blast_radius(service_id=failing_service)
        blast_info = json.dumps(report.model_dump(), indent=2) if report else f"Service {failing_service} details unavailable."

        instruction = (
            f"🚨 DISTRIBUTED SYSTEM INCIDENT TRIAGE\n\n"
            f"Failing Service: {failing_service}\n"
            f"Reported Symptom: {symptom}\n\n"
            f"Dependency Graph & Blast Radius:\n{blast_info}\n\n"
            "Analyze this incident systematically:\n"
            "1. Trace the propagation path: Which upstream callers could be impacted or cascading timeouts?\n"
            "2. Check failure domain isolation: Are circuit breakers or fallback mechanisms needed?\n"
            "3. Identify immediate mitigation steps to stop bleeding (rate limiting, queue draining, feature flags).\n"
            "4. Propose root-cause diagnostic queries and database connection / dead-lock checks."
        )

        return [
            {
                "role": "user",
                "content": instruction
            }
        ]

    # -------------------------------------------------------------------------
    # PROMPT 3: API Contract & Schema Refactor
    # -------------------------------------------------------------------------
    @server.prompt(
        name="api_contract_refactor",
        description="Safely refactor an API endpoint or database column while ensuring zero downtime for callers."
    )
    def api_contract_refactor(service_id: str, change_description: str) -> List[Dict[str, Any]]:
        """
        Provides safe refactoring recipes with contract deprecation and consumer migration stages.

        @param str service_id: Target service ID being refactored
        @param str change_description: Proposed API or schema change
        @return List[Dict[str, Any]]: MCP prompt message structure
        """
        instruction = (
            f"🔧 API CONTRACT & SCHEMA REFACTORING BLUEPRINT\n\n"
            f"Target Service: {service_id}\n"
            f"Proposed Change: {change_description}\n\n"
            "Generate a production-grade 4-phase migration plan:\n"
            "Phase 1: Expand - Add new fields/endpoints without removing old ones (dual-write / dual-read).\n"
            "Phase 2: Migrate Consumers - Identify all dependent services and update their client SDKs.\n"
            "Phase 3: Verify & Monitor - Log deprecation warnings and monitor traffic on legacy endpoints.\n"
            "Phase 4: Contract - Safely decommission old fields/routes after all consumers have migrated."
        )

        return [
            {
                "role": "user",
                "content": instruction
            }
        ]
