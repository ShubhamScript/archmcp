"""
OpenAPI and Swagger specification extractor.

Scans the repository tree for OpenAPI/Swagger JSON and YAML specs
and deep-parses defined paths, methods, and summaries.

@author Shubham Upadhyay
@license MIT
"""

import os
from typing import List, Set, Tuple
from ..models.api import APIEndpoint
from ..ingestion.openapi_importer import OpenAPIImporter

IGNORED_DIRS: Set[str] = {
    ".git", ".venv", "venv", "env", "node_modules", "__pycache__",
    ".pytest_cache", "dist", "build", "target", "vendor", ".idea",
    ".vscode", "coverage", "htmlcov", ".mypy_cache"
}


class OpenAPIExtractor:
    """
    Finds and parses OpenAPI / Swagger specifications across directory trees.
    """

    SPEC_FILENAMES = {
        "openapi.json", "openapi.yaml", "openapi.yml",
        "swagger.json", "swagger.yaml", "swagger.yml",
        "api-spec.json", "api-spec.yaml", "api-spec.yml",
        "api.json", "api.yaml", "api.yml"
    }

    @classmethod
    def find_and_extract(cls, directory: str) -> Tuple[List[str], List[APIEndpoint]]:
        """
        Finds all OpenAPI specs in directory and extracts their endpoints.

        @param str directory: Search directory
        @return Tuple[List[str], List[APIEndpoint]]: List of spec file paths and extracted endpoints
        """
        found_specs = []
        endpoints = []

        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]

            for file in files:
                f_lower = file.lower()
                if f_lower in cls.SPEC_FILENAMES or ("openapi" in f_lower and f_lower.endswith((".json", ".yaml", ".yml"))):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, directory).replace("\\", "/")
                    found_specs.append(rel_path)

                    try:
                        svc = OpenAPIImporter.import_from_file(full_path)
                        endpoints.extend(svc.apis)
                    except Exception:
                        pass

        return found_specs, endpoints
