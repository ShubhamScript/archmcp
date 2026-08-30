"""
ArchMCP Discovery Package.

Provides automatic repository architecture scanning, microservice detection,
API extraction, database table inspection, event queue linking, and dependency graph generation.

@author Shubham Upadhyay
@license MIT
"""

from .engine import RepositoryDiscoveryEngine
from .detector import ProjectDetector, ServiceRoot
from .route_extractor import RouteExtractor
from .schema_extractor import SchemaExtractor
from .queue_extractor import QueueExtractor
from .job_extractor import JobExtractor
from .config_extractor import ConfigExtractor
from .docker_extractor import DockerExtractor
from .openapi_extractor import OpenAPIExtractor
from .dependency_linker import DependencyLinker

__all__ = [
    "RepositoryDiscoveryEngine",
    "ProjectDetector",
    "ServiceRoot",
    "RouteExtractor",
    "SchemaExtractor",
    "QueueExtractor",
    "JobExtractor",
    "ConfigExtractor",
    "DockerExtractor",
    "OpenAPIExtractor",
    "DependencyLinker",
]
