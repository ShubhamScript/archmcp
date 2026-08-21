"""
Repository registry that loads and tracks microservices from YAML configuration.

@author Shubham Upadhyay
@license MIT
"""

import os
from typing import List, Optional, Dict
import yaml

from ..models.service import ServiceMetadata, ServiceDependencies
from ..models.api import APIEndpoint
from ..models.database_table import DatabaseTable
from ..models.repository import RepositoryInfo


class RepositoryRegistry:
    """
    Loads and provides access to registered microservice repositories.
    """

    def __init__(self, config_path: str = "data/repositories.yaml") -> None:
        self.config_path = config_path
        self._repositories: Dict[str, RepositoryInfo] = {}
        self._services: Dict[str, ServiceMetadata] = {}

    def load(self) -> None:
        """
        Loads repository definitions from the configured YAML file.

        @return None
        """
        if not os.path.exists(self.config_path):
            return

        with open(self.config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        raw_repos = data.get("repositories", [])
        for item in raw_repos:
            repo_id = item.get("id")
            name = item.get("name", repo_id)
            repo_url = item.get("repo_url", "")
            language = item.get("language", "Unknown")

            repo_info = RepositoryInfo(
                id=repo_id,
                name=name,
                repo_url=repo_url,
                default_branch="main"
            )
            self._repositories[repo_id] = repo_info

            raw_apis = item.get("apis", [])
            apis = [
                APIEndpoint(
                    path=a.get("path"),
                    method=a.get("method", "GET"),
                    summary=a.get("summary", ""),
                    description=a.get("description", "")
                )
                for a in raw_apis
            ]

            raw_tables = item.get("database_tables", [])
            tables = [
                DatabaseTable(
                    name=t.get("name"),
                    description=t.get("description", ""),
                    columns=t.get("columns", [])
                )
                for t in raw_tables
            ]

            deps = item.get("dependencies", {})
            dependencies = ServiceDependencies(
                upstream=deps.get("upstream", []),
                downstream=deps.get("downstream", [])
            )

            service = ServiceMetadata(
                id=repo_id,
                name=name,
                repo_url=repo_url,
                owner=item.get("owner", "Engineering"),
                language=language,
                description=item.get("description", ""),
                dependencies=dependencies,
                apis=apis,
                database_tables=tables
            )
            self._services[repo_id] = service

    def get_all_services(self) -> List[ServiceMetadata]:
        """
        Returns all registered services.

        @return List[ServiceMetadata]: List of all microservices
        """
        return list(self._services.values())

    def get_service(self, service_id: str) -> Optional[ServiceMetadata]:
        """
        Retrieves a single service by ID.

        @param str service_id: Unique service identifier
        @return Optional[ServiceMetadata]: Service metadata or None
        """
        return self._services.get(service_id)

    def get_all_repositories(self) -> List[RepositoryInfo]:
        """
        Returns all registered repositories.

        @return List[RepositoryInfo]: List of repository objects
        """
        return list(self._repositories.values())
