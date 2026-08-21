"""
Analyzes dependencies across microservices.

@author Shubham Upadhyay
@license MIT
"""

from typing import List
from ..models.service import ServiceMetadata
from ..models.architecture import ArchitectureGraph, ArchitectureNode, ArchitectureEdge


class DependencyAnalyzer:
    """
    Calculates cross-service dependency graphs and active communication channels.
    """

    @staticmethod
    def build_graph(services: List[ServiceMetadata]) -> ArchitectureGraph:
        """
        Builds a complete node-edge topology graph from a list of microservices.

        @param List[ServiceMetadata] services: Registered microservice entities
        @return ArchitectureGraph: Complete system topology graph
        """
        nodes = []
        edges = []

        for svc in services:
            nodes.append(ArchitectureNode(
                id=svc.id,
                name=svc.name,
                language=svc.language,
                owner=svc.owner
            ))

            for down in svc.dependencies.downstream:
                edges.append(ArchitectureEdge(
                    source=svc.id,
                    target=down,
                    protocol="HTTP/REST or Events"
                ))

        summary = f"Organization topology contains {len(nodes)} microservices with {len(edges)} active communication channels."
        return ArchitectureGraph(nodes=nodes, edges=edges, summary=summary)
