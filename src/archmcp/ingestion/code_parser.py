"""
Parser for source code structure, API routes, and schema definitions.

@author Shubham Upadhyay
@license MIT
"""

from typing import List
from ..models.api import APIEndpoint


class CodeParser:
    """
    Extracts route definitions and configuration endpoints from raw source code.
    """

    @staticmethod
    def extract_endpoints_from_text(raw_text: str) -> List[APIEndpoint]:
        """
        Extracts endpoint definitions from raw code text snippets.

        @param str raw_text: Source code content
        @return List[APIEndpoint]: List of parsed API endpoints
        """
        endpoints = []
        for line in raw_text.splitlines():
            line = line.strip()
            if line.startswith(("@app.get", "@app.post", "@app.put", "@app.delete", "router.get", "router.post")):
                parts = line.split('"')
                if len(parts) >= 2:
                    path = parts[1]
                    method = "GET" if "get" in line.lower() else "POST"
                    endpoints.append(APIEndpoint(path=path, method=method, summary=f"Extracted route {path}"))
        return endpoints
