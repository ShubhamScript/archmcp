"""
Repository scanner and metadata ingestion orchestrator.

@author Shubham Upadhyay
@license MIT
"""

import logging
from ..repositories.repository_registry import RepositoryRegistry
from ..storage.database import db
from ..storage.vector_store import search_index
from ..ingestion.document_parser import DocumentParser

logger = logging.getLogger(__name__)


class RepositoryScanner:
    """
    Scans all registered microservices, saves them to database, and indexes them for search.
    """

    def __init__(self, registry: RepositoryRegistry) -> None:
        self.registry = registry

    def scan_and_index_all(self) -> int:
        """
        Loads services from registry, populates database, and builds search index.

        @return int: Total count of scanned and indexed microservices
        """
        self.registry.load()
        services = self.registry.get_all_services()

        for svc in services:
            # 1. Save structured metadata to database
            db.save_service(svc)

            # 2. Build indexable text body
            api_text = " ".join([f"{a.method} {a.path} {a.summary} {a.description or ''}" for a in svc.apis])
            db_text = " ".join([f"{t.name} {t.description} {' '.join(t.columns)}" for t in svc.database_tables])
            dep_text = f"Upstream: {' '.join(svc.dependencies.upstream)} Downstream: {' '.join(svc.dependencies.downstream)}"
            full_text = f"{svc.name} {svc.id} {svc.owner} {svc.language} {svc.description} {api_text} {db_text} {dep_text}"

            # Index into search engine
            search_index.index_item(
                item_id=svc.id,
                text=full_text,
                metadata={
                    "type": "service",
                    "id": svc.id,
                    "name": svc.name,
                    "owner": svc.owner,
                    "language": svc.language,
                    "description": svc.description
                }
            )

            # 3. Create default architecture document
            doc_content = f"""# {svc.name} ({svc.id})
**Owner**: {svc.owner}
**Tech Stack**: {svc.language}
**Repository**: {svc.repo_url}

## Description
{svc.description}

## APIs
{chr(10).join([f"- `{a.method} {a.path}`: {a.summary}" for a in svc.apis])}

## Database Tables
{chr(10).join([f"- **{t.name}**: {t.description} (Columns: {', '.join(t.columns)})" for t in svc.database_tables])}
"""
            doc = DocumentParser.parse_markdown(
                service_id=svc.id,
                title=f"{svc.name} Overview",
                content=doc_content
            )
            db.save_document(doc)

        logger.info(f"Successfully scanned and indexed {len(services)} microservices.")
        return len(services)
