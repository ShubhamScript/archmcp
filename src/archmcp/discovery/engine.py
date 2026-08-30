"""
ArchMCP Automatic Repository & Architecture Discovery Engine.

Master orchestrator that scans any project or monorepo directory,
discovers all microservices, routes, database schemas, message queues,
background jobs, configs, docker services, and builds the dependency graph.

@author Shubham Upadhyay
@license MIT
"""

import os
import logging
from typing import Optional, List, Dict, Any

from ..models.service import ServiceMetadata, ServiceDependencies
from ..models.discovery import DiscoveryReport
from ..storage.database import db
from ..storage.vector_store import search_index
from ..ingestion.document_parser import DocumentParser

from .detector import ProjectDetector
from .route_extractor import RouteExtractor
from .schema_extractor import SchemaExtractor
from .queue_extractor import QueueExtractor
from .job_extractor import JobExtractor
from .config_extractor import ConfigExtractor
from .docker_extractor import DockerExtractor
from .openapi_extractor import OpenAPIExtractor
from .dependency_linker import DependencyLinker

logger = logging.getLogger(__name__)


class RepositoryDiscoveryEngine:
    """
    Automatic discovery engine for software repositories and architecture topologies.
    """

    def __init__(self, default_owner: str = "Engineering Team", tenant_id: str = "default") -> None:
        self.default_owner = default_owner
        self.tenant_id = tenant_id

    def discover(
        self,
        directory: str,
        persist: bool = True,
        owner: Optional[str] = None
    ) -> DiscoveryReport:
        """
        Scans a repository root path and automatically discovers the complete architecture.

        @param str directory: Root directory path of codebase or monorepo
        @param bool persist: If True, saves and indexes discovered services into ArchMCP DB & Vector Store
        @param Optional[str] owner: Default owning team for discovered services
        @return DiscoveryReport: Complete structured discovery report
        """
        root_dir = os.path.abspath(directory)
        if not os.path.exists(root_dir):
            raise FileNotFoundError(f"Repository path '{root_dir}' does not exist.")

        service_owner = owner or self.default_owner
        project_name = os.path.basename(root_dir) or "monorepo"

        # 1. Detect microservice roots & monorepo structure
        service_roots = ProjectDetector.detect(root_dir)
        is_monorepo = len(service_roots) > 1 or (len(service_roots) == 1 and service_roots[0].path != ".")

        discovered_services: List[ServiceMetadata] = []

        # 2. Deep inspection per microservice
        for s_root in service_roots:
            s_dir = s_root.full_path

            # A. Extract Routes / APIs
            code_apis = RouteExtractor.extract_from_dir(s_dir)
            spec_files, spec_apis = OpenAPIExtractor.find_and_extract(s_dir)
            # Deduplicate APIs
            all_apis_map = {}
            for a in code_apis + spec_apis:
                key = f"{a.method.upper()}:{a.path}"
                all_apis_map[key] = a
            apis = list(all_apis_map.values())

            # B. Extract Database Tables / Schemas
            tables = SchemaExtractor.extract_from_dir(s_dir)

            # C. Extract Message Queues & Event Topics
            queues = QueueExtractor.extract_from_dir(s_dir)

            # D. Extract Background Jobs
            jobs = JobExtractor.extract_from_dir(s_dir)

            # E. Extract Environment Configurations
            envs = ConfigExtractor.extract_from_dir(s_dir)

            # F. Extract Docker Services
            docker_svcs = DockerExtractor.extract_from_dir(s_dir)

            # Assemble Service Metadata
            lang_label = f"{s_root.language} / {s_root.framework}" if s_root.framework and s_root.framework not in s_root.language else s_root.language
            svc = ServiceMetadata(
                id=s_root.id,
                name=s_root.name,
                repo_url=None,
                owner=service_owner,
                language=lang_label,
                framework=s_root.framework,
                path=s_root.path,
                description=s_root.description or f"Microservice module discovered in {s_root.path}",
                tenant_id=self.tenant_id,
                dependencies=ServiceDependencies(upstream=[], downstream=[]),
                apis=apis,
                database_tables=tables,
                docs=[],
                env_vars=envs,
                message_queues=queues,
                background_jobs=jobs,
                docker_services=docker_svcs,
                openapi_specs=spec_files
            )
            discovered_services.append(svc)

        # 3. Discover Global Root-level Docker & Configs
        global_docker = DockerExtractor.extract_from_dir(root_dir)
        global_configs = ConfigExtractor.extract_from_dir(root_dir)

        # 4. Infer Cross-Service Dependencies and Build Graph
        graph = DependencyLinker.link_services(discovered_services, root_dir=root_dir)
        ascii_flow = DependencyLinker.generate_ascii_flow(graph)
        mermaid_diagram = DependencyLinker.generate_mermaid_diagram(graph, discovered_services)

        # 5. Persist to Database & Search Index if requested
        if persist:
            for svc in discovered_services:
                db.save_service(svc)

                # Build full text index
                api_text = " ".join([f"{a.method} {a.path} {a.summary}" for a in svc.apis])
                db_text = " ".join([f"{t.name} {' '.join(t.columns)}" for t in svc.database_tables])
                q_text = " ".join([f"{q.broker_type} {q.name} {q.role}" for q in svc.message_queues])
                job_text = " ".join([f"{j.name} {j.job_type}" for j in svc.background_jobs])
                env_text = " ".join([e.key for e in svc.env_vars])
                dep_text = f"Upstream: {' '.join(svc.dependencies.upstream)} Downstream: {' '.join(svc.dependencies.downstream)}"
                full_text = f"{svc.name} {svc.id} {svc.owner} {svc.language} {svc.description} {api_text} {db_text} {q_text} {job_text} {env_text} {dep_text}"

                search_index.index_item(
                    item_id=svc.id,
                    text=full_text,
                    metadata={
                        "type": "service",
                        "id": svc.id,
                        "name": svc.name,
                        "owner": svc.owner,
                        "language": svc.language,
                        "description": svc.description,
                        "tenant_id": svc.tenant_id
                    }
                )

                # Generate Architecture Documentation
                doc_content = f"""# {svc.name} ({svc.id})
**Path**: `{svc.path}`
**Owner**: {svc.owner}
**Tech Stack**: {svc.language}

## Description
{svc.description}

## APIs ({len(svc.apis)} Endpoints)
{chr(10).join([f"- `{a.method} {a.path}`: {a.summary}" for a in svc.apis]) or "No exposed HTTP endpoints discovered."}

## Database Tables ({len(svc.database_tables)} Tables)
{chr(10).join([f"- **{t.name}**: {t.description} (Columns: {', '.join(t.columns)})" for t in svc.database_tables]) or "No database tables discovered."}

## Message Queues & Event Streaming ({len(svc.message_queues)} Topics)
{chr(10).join([f"- **{q.broker_type} Topic `{q.name}`** ({q.role})" for q in svc.message_queues]) or "No event topics discovered."}

## Background Jobs ({len(svc.background_jobs)} Jobs)
{chr(10).join([f"- **{j.name}** ({j.job_type}) - Schedule: {j.schedule or 'N/A'}" for j in svc.background_jobs]) or "No background jobs discovered."}

## Dependencies
- **Calls (Downstream)**: {', '.join(svc.dependencies.downstream) or 'None'}
- **Called By (Upstream)**: {', '.join(svc.dependencies.upstream) or 'None'}
"""
                doc = DocumentParser.parse_markdown(
                    service_id=svc.id,
                    title=f"{svc.name} Architecture Overview",
                    content=doc_content,
                    tenant_id=svc.tenant_id
                )
                db.save_document(doc)

            logger.info(f"Persisted and indexed {len(discovered_services)} discovered microservices.")

        # 6. Assemble Discovery Report
        total_apis = sum(len(s.apis) for s in discovered_services)
        total_tables = sum(len(s.database_tables) for s in discovered_services)
        total_queues = sum(len(s.message_queues) for s in discovered_services)
        total_jobs = sum(len(s.background_jobs) for s in discovered_services)
        total_docker = len(global_docker)
        total_envs = sum(len(s.env_vars) for s in discovered_services) + len(global_configs)

        report = DiscoveryReport(
            scanned_path=root_dir,
            project_name=project_name,
            is_monorepo=is_monorepo,
            service_count=len(discovered_services),
            api_count=total_apis,
            table_count=total_tables,
            queue_count=total_queues,
            job_count=total_jobs,
            docker_count=total_docker,
            env_count=total_envs,
            graph=graph,
            services=discovered_services,
            docker_services=global_docker,
            global_configs=global_configs,
            ascii_flow=ascii_flow,
            mermaid_diagram=mermaid_diagram,
            summary={
                "services": len(discovered_services),
                "apis": total_apis,
                "database_tables": total_tables,
                "message_queues": total_queues,
                "background_jobs": total_jobs,
                "docker_services": total_docker,
                "config_variables": total_envs,
                "communication_channels": len(graph.edges)
            }
        )

        return report
