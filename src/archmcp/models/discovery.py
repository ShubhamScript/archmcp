"""
Discovery metadata models for automatic repository and architecture analysis.

@author Shubham Upadhyay
@license MIT
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from .architecture import ArchitectureGraph


class EnvVarInfo(BaseModel):
    """Extracted environment or configuration variable."""
    key: str = Field(..., description="Configuration variable name (e.g. DATABASE_URL)")
    default_value: Optional[str] = Field(None, description="Default value or masked placeholder")
    is_secret: bool = Field(False, description="True if key represents a secret, token, or password")
    source_file: str = Field("", description="File where variable was discovered")


class MessageQueueInfo(BaseModel):
    """Extracted message queue or event streaming topic."""
    name: str = Field(..., description="Topic or queue name (e.g. user-events, order.created)")
    broker_type: str = Field("Unknown", description="Broker type (Kafka, RabbitMQ, SQS, Redis, Celery, NATS)")
    role: str = Field("producer", description="Role: producer (publishes), consumer (subscribes), or both")
    source_file: str = Field("", description="File where queue usage was discovered")


class BackgroundJobInfo(BaseModel):
    """Extracted background job or scheduled cron task."""
    name: str = Field(..., description="Job or task name (e.g. sync_user_data, purge_logs)")
    job_type: str = Field("Unknown", description="Job framework (Celery, BullMQ, Cron, Spring Scheduled, Temporal)")
    schedule: Optional[str] = Field(None, description="Cron expression or interval schedule if defined")
    source_file: str = Field("", description="File where job was defined")


class DockerServiceInfo(BaseModel):
    """Extracted Docker or Compose service configuration."""
    service_name: str = Field(..., description="Service container name (e.g. postgres, redis, api-gateway)")
    image: Optional[str] = Field(None, description="Docker image name or build path")
    ports: List[str] = Field(default_factory=list, description="Port bindings (e.g. ['8080:8080'])")
    depends_on: List[str] = Field(default_factory=list, description="Container dependency names")
    environment: List[str] = Field(default_factory=list, description="Environment variable keys defined")
    source_file: str = Field("", description="Source compose or Dockerfile path")


class DiscoveryReport(BaseModel):
    """Aggregated project architecture discovery report."""
    scanned_path: str = Field(..., description="Root directory path scanned")
    project_name: str = Field(..., description="Name of the scanned project or monorepo")
    is_monorepo: bool = Field(False, description="Whether project contains multiple independent services")
    service_count: int = Field(0, description="Total microservices/modules discovered")
    api_count: int = Field(0, description="Total API routes discovered")
    table_count: int = Field(0, description="Total database tables discovered")
    queue_count: int = Field(0, description="Total message queues/topics discovered")
    job_count: int = Field(0, description="Total background jobs discovered")
    docker_count: int = Field(0, description="Total docker services discovered")
    env_count: int = Field(0, description="Total configuration variables discovered")
    graph: ArchitectureGraph = Field(default_factory=ArchitectureGraph, description="Discovered dependency graph")
    services: List[Any] = Field(default_factory=list, description="List of Discovered/Metadata services")
    docker_services: List[DockerServiceInfo] = Field(default_factory=list, description="Top-level Docker services")
    global_configs: List[EnvVarInfo] = Field(default_factory=list, description="Root-level configuration keys")
    ascii_flow: str = Field("", description="ASCII visualization of service flow")
    mermaid_diagram: str = Field("", description="Mermaid diagram representation of discovered architecture")
    summary: Dict[str, Any] = Field(default_factory=dict, description="Summary statistics")
