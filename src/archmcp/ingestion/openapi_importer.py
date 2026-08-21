"""
ArchMCP - Dynamic OpenAPI & Swagger Importer.

@author Shubham Upadhyay
@license MIT
"""

import json
import logging
from typing import Dict, Any
import httpx
import yaml

from ..models.service import ServiceMetadata, ServiceDependencies
from ..models.api import APIEndpoint
from ..models.database_table import DatabaseTable
from ..storage.database import db
from ..storage.vector_store import search_index
from ..ingestion.document_parser import DocumentParser

logger = logging.getLogger(__name__)


class OpenAPIImporter:
    """
    Parses OpenAPI 3.0+ / Swagger 2.0 specs into ArchMCP service models.
    """

    @staticmethod
    def parse_spec_dict(spec: Dict[str, Any], default_owner: str = "Engineering Team") -> ServiceMetadata:
        """
        Parses an OpenAPI specification dictionary into a ServiceMetadata model.

        @param Dict[str, Any] spec: Parsed OpenAPI/Swagger dictionary
        @param str default_owner: Default team owner
        @return ServiceMetadata: Extracted service metadata entity
        """
        info = spec.get("info", {})
        title = info.get("title", "Imported Service")
        service_id = title.lower().replace(" ", "-").replace("_", "-")
        description = info.get("description", "Imported via OpenAPI specification")
        version = info.get("version", "1.0.0")

        # Parse Endpoints
        apis = []
        paths = spec.get("paths", {})
        for path, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue
            for method in ["get", "post", "put", "delete", "patch", "options", "head"]:
                if method in path_item:
                    op = path_item[method]
                    summary = op.get("summary") or op.get("description") or f"{method.upper()} {path}"
                    apis.append(APIEndpoint(
                        path=path,
                        method=method.upper(),
                        summary=summary[:120],
                        description=op.get("description", "")
                    ))

        # Parse Schemas / Models as virtual entity tables
        components = spec.get("components", {}).get("schemas", {})
        if not components:
            components = spec.get("definitions", {})

        database_tables = []
        for schema_name, schema_def in components.items():
            if isinstance(schema_def, dict) and "properties" in schema_def:
                props = schema_def.get("properties", {})
                cols = [f"{k} ({v.get('type', 'any')})" for k, v in props.items()]
                database_tables.append(DatabaseTable(
                    name=schema_name.lower(),
                    description=schema_def.get("description", f"Data entity model for {schema_name}"),
                    columns=cols[:10]
                ))

        service = ServiceMetadata(
            id=service_id,
            name=f"{title} (v{version})",
            repo_url=f"https://github.com/company-org/{service_id}",
            owner=default_owner,
            language="OpenAPI Spec",
            description=description,
            dependencies=ServiceDependencies(upstream=[], downstream=[]),
            database_tables=database_tables,
            apis=apis
        )

        return service

    @classmethod
    def import_from_url(cls, url: str, default_owner: str = "Platform Team") -> ServiceMetadata:
        """
        Fetches live OpenAPI JSON/YAML from remote HTTP endpoint and registers in ArchMCP.

        @param str url: Remote OpenAPI/Swagger URL
        @param str default_owner: Default team owner
        @return ServiceMetadata: Registered service metadata entity
        """
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(url)
            resp.raise_for_status()
            try:
                spec = resp.json()
            except Exception:
                spec = yaml.safe_load(resp.text)

        service = cls.parse_spec_dict(spec, default_owner=default_owner)
        cls._index_imported_service(service)
        return service

    @classmethod
    def import_from_file(cls, file_path: str, default_owner: str = "Platform Team") -> ServiceMetadata:
        """
        Parses local JSON or YAML OpenAPI file and registers in ArchMCP.

        @param str file_path: Path to local openapi.json/yaml
        @param str default_owner: Default team owner
        @return ServiceMetadata: Registered service metadata entity
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            try:
                spec = json.loads(content)
            except Exception:
                spec = yaml.safe_load(content)

        service = cls.parse_spec_dict(spec, default_owner=default_owner)
        cls._index_imported_service(service)
        return service

    @classmethod
    def _index_imported_service(cls, service: ServiceMetadata) -> None:
        """
        Saves service to metadata DB, vector search index, and doc catalog.

        @param ServiceMetadata service: Service to save and index
        @return None
        """
        db.save_service(service)

        api_text = " ".join([f"{a.method} {a.path} {a.summary}" for a in service.apis])
        db_text = " ".join([f"{t.name} {t.description}" for t in service.database_tables])
        full_text = f"{service.name} {service.id} {service.owner} {service.description} {api_text} {db_text}"

        search_index.index_item(
            item_id=service.id,
            text=full_text,
            metadata={
                "type": "service",
                "id": service.id,
                "name": service.name,
                "owner": service.owner,
                "language": service.language,
                "description": service.description
            }
        )

        doc = DocumentParser.parse_markdown(
            service_id=service.id,
            title=f"{service.name} API Catalog",
            content=f"# {service.name}\n\n{service.description}\n\n### Endpoints\n" +
                    "\n".join([f"- `{a.method} {a.path}`: {a.summary}" for a in service.apis])
        )
        db.save_document(doc)
        logger.info(f"Successfully imported and indexed service '{service.id}' ({len(service.apis)} APIs).")
