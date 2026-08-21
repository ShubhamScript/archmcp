"""
Architecture topology and graph representation models.

@author Shubham Upadhyay
@license MIT
"""

from typing import List
from pydantic import BaseModel, Field


class ArchitectureNode(BaseModel):
    """A service node in the microservices dependency graph."""
    id: str
    name: str
    language: str
    owner: str


class ArchitectureEdge(BaseModel):
    """A directional communication dependency between two microservices."""
    source: str = Field(..., description="Calling upstream service ID")
    target: str = Field(..., description="Called downstream service ID")
    protocol: str = Field("HTTP/REST", description="Communication protocol (REST, gRPC, Kafka, etc.)")


class ArchitectureGraph(BaseModel):
    """The organization-wide microservices dependency graph."""
    nodes: List[ArchitectureNode] = Field(default_factory=list)
    edges: List[ArchitectureEdge] = Field(default_factory=list)
    summary: str = Field("", description="Overview description of system topology")


class BlastRadiusReport(BaseModel):
    """Deep impact analysis report of changing a service, endpoint, or schema."""
    target_service_id: str
    changed_component: str
    impact_severity: str = Field(..., description="LOW, MEDIUM, HIGH, CRITICAL")
    direct_dependent_services: List[str] = Field(default_factory=list, description="Immediate callers/consumers")
    transitive_dependent_services: List[str] = Field(default_factory=list, description="Indirect downstream affected services (2+ hops)")
    affected_teams: List[str] = Field(default_factory=list, description="Engineering teams that must be notified")
    affected_endpoints: List[str] = Field(default_factory=list, description="Endpoints directly or transitively impacted")
    risk_summary: str = Field(..., description="Assessment of change risks and mitigation advice")


class SequenceDiagram(BaseModel):
    """Generated Mermaid sequence diagram for distributed workflows."""
    flow_name: str
    participating_services: List[str]
    mermaid_code: str
    description: str
