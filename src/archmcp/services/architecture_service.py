"""
Architecture service providing topology graphs, dependency analysis, and blast radius calculation.

@author Shubham Upadhyay
@license MIT
"""

from typing import List, Dict, Any, Optional, Set
from collections import deque
from ..storage.database import db
from ..models.architecture import ArchitectureGraph, BlastRadiusReport, SequenceDiagram
from ..ingestion.dependency_analyzer import DependencyAnalyzer


class ArchitectureService:
    """
    Service to compute overall architecture maps, upstream/downstream dependencies, and blast-radius analysis.
    """

    def get_system_architecture(self) -> ArchitectureGraph:
        """
        Returns the global microservices dependency graph.

        @return ArchitectureGraph: Complete system graph
        """
        services = db.list_services()
        return DependencyAnalyzer.build_graph(services)

    def get_service_dependencies(self, service_id: str) -> Optional[Dict[str, Any]]:
        """
        Returns detailed upstream and downstream dependencies for a single service.

        @param str service_id: Unique service identifier
        @return Optional[Dict[str, Any]]: Upstream and downstream dependency mapping
        """
        svc = db.get_service(service_id)
        if not svc:
            return None

        all_services = db.list_services()
        callers = [s.id for s in all_services if service_id in s.dependencies.downstream]
        callees = [s.id for s in all_services if service_id in s.dependencies.upstream]

        return {
            "service_id": service_id,
            "name": svc.name,
            "declared_upstream": svc.dependencies.upstream,
            "declared_downstream": svc.dependencies.downstream,
            "inferred_called_by": list(set(callers)),
            "inferred_calls_to": list(set(callees)),
        }

    def analyze_blast_radius(self, service_id: str, component: str = "") -> Optional[BlastRadiusReport]:
        """
        Calculates the full blast radius and transitive ripple effects of modifying a service or API.

        @param str service_id: Target service ID being modified
        @param str component: Optional specific endpoint or table name
        @return Optional[BlastRadiusReport]: Full impact analysis report
        """
        svc = db.get_service(service_id)
        if not svc:
            return None

        all_services = {s.id: s for s in db.list_services()}

        # Build reverse caller adjacency graph (callee -> list of callers)
        caller_graph: Dict[str, Set[str]] = {s_id: set() for s_id in all_services}
        for s_id, s_data in all_services.items():
            for upstream_id in s_data.dependencies.upstream:
                if upstream_id in caller_graph:
                    caller_graph[upstream_id].add(s_id)

        # BFS to discover direct and transitive callers
        direct_callers: Set[str] = set(caller_graph.get(service_id, set()))
        for s_id, s_data in all_services.items():
            if service_id in s_data.dependencies.upstream:
                direct_callers.add(s_id)

        transitive_callers: Set[str] = set()
        visited: Set[str] = {service_id}.union(direct_callers)
        queue = deque(list(direct_callers))

        while queue:
            curr = queue.popleft()
            for next_caller in caller_graph.get(curr, set()):
                if next_caller not in visited:
                    visited.add(next_caller)
                    transitive_callers.add(next_caller)
                    queue.append(next_caller)

        # Collect affected teams
        affected_teams: Set[str] = {svc.owner}
        for dep_id in direct_callers.union(transitive_callers):
            if dep_id in all_services:
                affected_teams.add(all_services[dep_id].owner)

        # Endpoints impacted
        affected_endpoints = [f"{a.method} {a.path}" for a in svc.apis]
        if component:
            matching_ep = [ep for ep in affected_endpoints if component.lower() in ep.lower()]
            if matching_ep:
                affected_endpoints = matching_ep

        # Determine severity
        total_dependents = len(direct_callers) + len(transitive_callers)
        if service_id == "auth-service" or total_dependents >= 3:
            severity = "CRITICAL"
        elif total_dependents >= 2 or len(transitive_callers) > 0:
            severity = "HIGH"
        elif total_dependents == 1:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        risk_summary = (
            f"Modifying '{service_id}' ({component or 'entire service'}) will directly impact "
            f"{len(direct_callers)} immediate consumers and {len(transitive_callers)} indirect multi-hop services across "
            f"{len(affected_teams)} engineering teams. "
            f"Severity rated {severity}. Recommend contract testing and maintaining backwards-compatible API versioning."
        )

        return BlastRadiusReport(
            target_service_id=service_id,
            changed_component=component or "All APIs & Schemas",
            impact_severity=severity,
            direct_dependent_services=sorted(list(direct_callers)),
            transitive_dependent_services=sorted(list(transitive_callers)),
            affected_teams=sorted(list(affected_teams)),
            affected_endpoints=affected_endpoints,
            risk_summary=risk_summary
        )

    def generate_sequence_diagram(self, flow_name: str) -> SequenceDiagram:
        """
        Generates a Mermaid sequence diagram representation for common microservice workflows.

        @param str flow_name: Name of workflow or process
        @return SequenceDiagram: Mermaid sequence diagram model
        """
        flow_lower = flow_name.lower()

        if "order" in flow_lower or "checkout" in flow_lower:
            mermaid = """sequenceDiagram
    autonumber
    actor Client as End User
    participant Auth as auth-service
    participant Order as order-service
    participant Inv as inventory-service
    participant Pay as payment-service
    participant Notif as notification-service

    Client->>Auth: POST /api/v1/auth/login (JWT)
    Auth-->>Client: 200 OK (Bearer Token)
    Client->>Order: POST /api/v1/orders (with Bearer Token)
    Order->>Auth: GET /api/v1/auth/verify
    Auth-->>Order: 200 OK (Token Valid)
    Order->>Inv: POST /api/v1/inventory/reserve (Lock SKU Stock)
    Inv-->>Order: 200 OK (Stock Reserved)
    Order->>Pay: POST /api/v1/payments/charge (Idempotency-Key)
    Pay-->>Order: 200 OK (Transaction Success)
    Order->>Notif: POST /api/v1/notifications/send (Async Kafka Event)
    Order-->>Client: 201 Created (Order Confirmed)"""
            services = ["auth-service", "order-service", "inventory-service", "payment-service", "notification-service"]
            desc = "End-to-end distributed checkout and order placement workflow with authentication, stock lock, and payment settlement."

        elif "refund" in flow_lower or "payment" in flow_lower:
            mermaid = """sequenceDiagram
    autonumber
    actor Admin as Customer Support
    participant Auth as auth-service
    participant Pay as payment-service
    participant Notif as notification-service

    Admin->>Auth: Verify Admin RBAC
    Auth-->>Admin: 200 OK
    Admin->>Pay: POST /api/v1/payments/refund (Transaction ID)
    Pay->>Pay: Validate Immutable Ledger & Idempotency
    Pay->>Notif: POST /api/v1/notifications/send (Refund Email)
    Pay-->>Admin: 200 OK (Refund Initiated)"""
            services = ["auth-service", "payment-service", "notification-service"]
            desc = "Payment refund workflow involving transaction ledger rollback and automated customer notification dispatch."

        else:
            all_services = db.list_services()
            service_names = [s.id for s in all_services]
            mermaid_lines = ["sequenceDiagram", "    autonumber", "    actor Client as API Gateway"]
            for s in all_services:
                mermaid_lines.append(f"    participant {s.id.replace('-', '_')} as {s.name}")
            mermaid_lines.append("    Client->>auth_service: Authenticate & Authorize")
            mermaid_lines.append("    Client->>order_service: Invoke Operation")
            mermaid = "\n".join(mermaid_lines)
            services = service_names
            desc = f"Architecture workflow communication sequence for '{flow_name}'."

        return SequenceDiagram(
            flow_name=flow_name,
            participating_services=services,
            mermaid_code=mermaid,
            description=desc
        )
