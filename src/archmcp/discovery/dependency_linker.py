"""
Cross-service dependency graph and communication channel linker.

Analyzes outgoing HTTP client requests, gRPC stubs, inter-service environment URLs,
shared message queues/event topics, and Docker Compose relations to automatically
link microservices into an end-to-end dependency graph and visual flow.

@author Shubham Upadhyay
@license MIT
"""

import os
import re
from typing import List, Dict, Set, Tuple
from ..models.service import ServiceMetadata, ServiceDependencies
from ..models.architecture import ArchitectureGraph, ArchitectureNode, ArchitectureEdge


class DependencyLinker:
    """
    Infers directional relationships and builds the system architecture graph.
    """

    # HTTP client invocation patterns
    HTTP_CLIENT_PATTERNS = [
        # requests.get("http://service-name/...") or httpx.post(...)
        re.compile(r"""(?:requests|httpx|http|client|session)\.(?:get|post|put|delete|patch)\s*\(\s*["'](https?://[a-zA-Z0-9_\-\.:]+[^"']*)["']""", re.IGNORECASE),
        # axios.get("http://service-name/...") or fetch("http://service-name/...")
        re.compile(r"""(?:axios|fetch|got|needle)\.(?:get|post|put|delete|patch|\()\s*\(?\s*["'](https?://[a-zA-Z0-9_\-\.:]+[^"']*)["']""", re.IGNORECASE),
        # Generic url string "http://svc-name:8080/..."
        re.compile(r"""["'](https?://([a-zA-Z0-9_\-]+)(?::[0-9]+)?/[^"']*)["']""", re.IGNORECASE)
    ]

    @classmethod
    def link_services(cls, services: List[ServiceMetadata], root_dir: str = "") -> ArchitectureGraph:
        """
        Calculates upstream and downstream dependencies across all services,
        populates their ServiceDependencies, and constructs the ArchitectureGraph.

        @param List[ServiceMetadata] services: Discovered microservices
        @param str root_dir: Root directory of project
        @return ArchitectureGraph: Complete organization topology graph
        """
        service_map = {s.id: s for s in services}
        edges_set: Set[Tuple[str, str, str]] = set()  # (source, target, protocol)

        # 1. Analyze Outgoing HTTP Calls from Source Code
        for svc in services:
            svc_path = svc.path or "."
            svc_full_path = os.path.join(root_dir, svc_path) if root_dir else svc_path
            if os.path.isdir(svc_full_path):
                cls._scan_code_for_outgoing_calls(svc, svc_full_path, service_map, edges_set)

        # 2. Analyze Inter-Service Environment Variables
        for svc in services:
            for env in svc.env_vars:
                k_lower = env.key.lower()
                v_lower = (env.default_value or "").lower()
                for target_id, target_svc in service_map.items():
                    if target_id == svc.id:
                        continue
                    # Matches keys like AUTH_SERVICE_URL or PAYMENT_HOST or values containing the service id
                    clean_target = target_id.replace("-", "_")
                    if target_id in k_lower or clean_target in k_lower or target_id in v_lower:
                        edges_set.add((svc.id, target_id, "HTTP / Inter-Service Config"))

        # 3. Analyze Shared Message Queues / Event Topics
        # Service A produces to Topic T -> Service B consumes from Topic T => Edge(A -> B)
        topic_producers: Dict[str, Set[str]] = {}
        topic_consumers: Dict[str, Set[str]] = {}

        for svc in services:
            for q in svc.message_queues:
                if q.role in {"producer", "both"}:
                    topic_producers.setdefault(q.name, set()).add(svc.id)
                if q.role in {"consumer", "both"}:
                    topic_consumers.setdefault(q.name, set()).add(svc.id)

        for topic, producers in topic_producers.items():
            consumers = topic_consumers.get(topic, set())
            for prod in producers:
                for cons in consumers:
                    if prod != cons:
                        edges_set.add((prod, cons, f"Event ({topic})"))

        # 4. Analyze Docker Compose depends_on
        for svc in services:
            for d in svc.docker_services:
                for dep in d.depends_on:
                    if dep in service_map and dep != svc.id:
                        edges_set.add((svc.id, dep, "Container Dependency"))

        # 5. Populate Upstream & Downstream in ServiceMetadata
        for source_id, target_id, protocol in edges_set:
            if source_id in service_map and target_id in service_map:
                source_svc = service_map[source_id]
                target_svc = service_map[target_id]

                if target_id not in source_svc.dependencies.downstream:
                    source_svc.dependencies.downstream.append(target_id)
                if source_id not in target_svc.dependencies.upstream:
                    target_svc.dependencies.upstream.append(source_id)

        # 6. Build ArchitectureGraph
        nodes = [
            ArchitectureNode(
                id=s.id,
                name=s.name,
                language=s.language,
                owner=s.owner
            )
            for s in services
        ]

        edges = [
            ArchitectureEdge(
                source=src,
                target=tgt,
                protocol=prot
            )
            for src, tgt, prot in sorted(list(edges_set))
        ]

        summary = (
            f"Discovered topology with {len(nodes)} microservices and {len(edges)} "
            f"inferred communication channels."
        )
        return ArchitectureGraph(nodes=nodes, edges=edges, summary=summary)

    @classmethod
    def _scan_code_for_outgoing_calls(
        cls,
        current_svc: ServiceMetadata,
        directory: str,
        service_map: Dict[str, ServiceMetadata],
        edges_set: Set[Tuple[str, str, str]]
    ) -> None:
        """Inspects code files to detect outbound HTTP requests to other known services."""
        for root, dirs, files in os.walk(directory):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext not in {".py", ".ts", ".js", ".go", ".java", ".kt", ".rs"}:
                    continue

                full_path = os.path.join(root, file)
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        code = f.read()
                except Exception:
                    continue

                # Check known other services
                for other_id, other_svc in service_map.items():
                    if other_id == current_svc.id:
                        continue

                    # Direct URL mention e.g. "http://payment-service" or "payment-service:8080"
                    if f"://{other_id}" in code or f"//{other_id}:" in code or f"@{other_id}" in code:
                        edges_set.add((current_svc.id, other_id, "HTTP / REST"))
                        continue

                    # Match against other service's exposed endpoint paths
                    for api in other_svc.apis:
                        if len(api.path) > 4 and api.path in code:
                            edges_set.add((current_svc.id, other_id, f"HTTP {api.method} {api.path}"))
                            break

    @classmethod
    def generate_ascii_flow(cls, graph: ArchitectureGraph) -> str:
        """
        Renders a clean, readable ASCII dependency flow representation.

        Example:
        user-service
            ↓ [HTTP/REST]
        payment-service
            ↓ [Event (order.paid)]
        notification-service
        """
        if not graph.edges:
            if graph.nodes:
                return "\n".join([f"📦 {n.name} ({n.id})" for n in graph.nodes])
            return "No service dependencies discovered."

        lines = []
        # Find root services (no incoming edges or fewest incoming)
        targets = {e.target for e in graph.edges}
        sources = {e.source for e in graph.edges}
        roots = [s for s in sources if s not in targets] or list(sources)

        visited = set()
        for root in roots:
            if root in visited:
                continue
            lines.append(f"📦 {root}")
            visited.add(root)
            cls._render_ascii_children(root, graph.edges, lines, visited, indent=1)

        # Append remaining disconnected nodes
        all_ids = {n.id for n in graph.nodes}
        remaining = all_ids - visited
        for rem in remaining:
            lines.append(f"📦 {rem} (Standalone / Event Listener)")

        return "\n".join(lines)

    @classmethod
    def _render_ascii_children(
        cls,
        parent: str,
        edges: List[ArchitectureEdge],
        lines: List[str],
        visited: Set[str],
        indent: int
    ) -> None:
        child_edges = [e for e in edges if e.source == parent]
        for edge in child_edges:
            indent_str = "    " * indent
            lines.append(f"{indent_str}↓ [{edge.protocol}]")
            lines.append(f"{indent_str}📦 {edge.target}")
            if edge.target not in visited:
                visited.add(edge.target)
                cls._render_ascii_children(edge.target, edges, lines, visited, indent + 1)

    @classmethod
    def generate_mermaid_diagram(cls, graph: ArchitectureGraph, services: List[ServiceMetadata]) -> str:
        """
        Generates Mermaid flowchart diagram for discovered architecture.
        """
        lines = ["graph TD"]
        svc_map = {s.id: s for s in services}

        # Render Nodes with nice styles
        for node in graph.nodes:
            clean_id = node.id.replace("-", "_")
            svc = svc_map.get(node.id)
            lang = svc.language if svc else node.language
            fw = f" / {svc.framework}" if (svc and svc.framework and svc.framework not in lang) else ""
            label = f'"{node.name}\\n({lang}{fw})"'
            lines.append(f"    {clean_id}[{label}]")

        # Render Edges
        for edge in graph.edges:
            src_clean = edge.source.replace("-", "_")
            tgt_clean = edge.target.replace("-", "_")
            protocol_label = edge.protocol.replace('"', '')
            lines.append(f'    {src_clean} -->|"{protocol_label}"| {tgt_clean}')

        return "\n".join(lines)
