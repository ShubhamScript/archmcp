"""
Microservice metadata models.

@author Shubham Upadhyay
@license MIT
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from .api import APIEndpoint
from .database_table import DatabaseTable


class ServiceDependencies(BaseModel):
    """Upstream and downstream microservice dependency mapping."""
    upstream: List[str] = Field(default_factory=list, description="Services that this service calls or relies on")
    downstream: List[str] = Field(default_factory=list, description="Services that call or rely on this service")


class ServiceMetadata(BaseModel):
    """Core metadata representation for a microservice."""
    id: str = Field(..., description="Unique service identifier (e.g. auth-service)")
    name: str = Field(..., description="Human readable service name")
    repo_url: Optional[str] = Field(None, description="Source code repository URL")
    owner: str = Field("Engineering Team", description="Team or engineer responsible for this service")
    language: str = Field("Unknown", description="Primary tech stack (e.g. Python / FastAPI)")
    description: str = Field("", description="High level purpose and responsibilities")
    dependencies: ServiceDependencies = Field(default_factory=ServiceDependencies)
    apis: List[APIEndpoint] = Field(default_factory=list, description="Exposed REST or gRPC endpoints")
    database_tables: List[DatabaseTable] = Field(default_factory=list, description="Database tables owned by this service")
    docs: List[str] = Field(default_factory=list, description="Documentation snippets and architecture notes")
