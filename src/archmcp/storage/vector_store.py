"""
ArchMCP - In-Memory Token Search Index.

@author Shubham Upadhyay
@license MIT
"""

import re
from typing import List, Dict, Any, Tuple


class SimpleSearchStore:
    """
    In-memory keyword and token-frequency search engine for microservices knowledge.
    """

    def __init__(self) -> None:
        self._entries: Dict[str, Dict[str, Any]] = {}

    def index_item(self, item_id: str, text: str, metadata: Dict[str, Any]) -> None:
        """
        Indexes an item for rapid full-text keyword retrieval.

        @param str item_id: Unique identifier of the item
        @param str text: Text content to tokenize and index
        @param Dict[str, Any] metadata: Payload returned upon search match
        @return None
        """
        self._entries[item_id] = {
            "text": text.lower(),
            "metadata": metadata
        }

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Searches indexed items by token matching and ranks by relevance score.

        @param str query: Search keywords
        @param int top_k: Maximum number of results to return
        @return List[Dict[str, Any]]: Ranked search result dictionaries
        """
        tokens = [t.lower() for t in re.findall(r'\w+', query)]
        if not tokens:
            return []

        scored: List[Tuple[float, Dict[str, Any]]] = []
        for item_id, entry in self._entries.items():
            text = entry["text"]
            score = 0.0
            for token in tokens:
                count = text.count(token)
                if count > 0:
                    score += 1.0 + (count * 0.5)

            if score > 0:
                result = dict(entry["metadata"])
                result["item_id"] = item_id
                result["score"] = round(score, 2)
                scored.append((score, result))

        # Sort by relevance score descending
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:top_k]]

    def clear(self) -> None:
        """
        Clears the in-memory search index.

        @return None
        """
        self._entries.clear()


# Global search index instance
search_index = SimpleSearchStore()
