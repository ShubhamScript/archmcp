"""
Search service providing discovery capabilities over microservices knowledge.

@author Shubham Upadhyay
@license MIT
"""

from typing import List, Dict, Any
from ..storage.vector_store import search_index


class SearchService:
    """
    Service to search across all microservices, endpoints, schemas, and docs.
    """

    def __init__(self) -> None:
        self._index = search_index

    def search_microservices(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Searches indexed services matching the query.

        @param str query: Search keywords or phrase
        @param int limit: Max number of results
        @return List[Dict[str, Any]]: Ranked matching items
        """
        return self._index.search(query=query, top_k=limit)
