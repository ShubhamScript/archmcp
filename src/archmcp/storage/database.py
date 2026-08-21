"""
ArchMCP - In-Memory Metadata Database.

@author Shubham Upadhyay
@license MIT
"""

from typing import Dict, List, Optional
from ..models.service import ServiceMetadata
from ..models.document import Document


class MetadataDatabase:
    """
    Fast in-memory store for microservice metadata and architecture documents.
    """

    def __init__(self) -> None:
        self._services: Dict[str, ServiceMetadata] = {}
        self._documents: Dict[str, Document] = {}

    def save_service(self, service: ServiceMetadata) -> None:
        """
        Upserts a microservice metadata record.

        @param ServiceMetadata service: Service metadata object to store
        @return None
        """
        self._services[service.id] = service

    def get_service(self, service_id: str) -> Optional[ServiceMetadata]:
        """
        Retrieves a microservice record by ID.

        @param str service_id: Unique service identifier
        @return Optional[ServiceMetadata]: Service metadata or None
        """
        return self._services.get(service_id)

    def list_services(self) -> List[ServiceMetadata]:
        """
        Returns all registered microservices.

        @return List[ServiceMetadata]: List of all tracked microservices
        """
        return list(self._services.values())

    def save_document(self, doc: Document) -> None:
        """
        Saves an architecture document.

        @param Document doc: Architecture document object
        @return None
        """
        self._documents[doc.id] = doc

    def get_document(self, doc_id: str) -> Optional[Document]:
        """
        Retrieves a document by ID.

        @param str doc_id: Unique document identifier
        @return Optional[Document]: Document object or None
        """
        return self._documents.get(doc_id)

    def list_documents(self, service_id: Optional[str] = None) -> List[Document]:
        """
        Returns documents optionally filtered by service ID.

        @param Optional[str] service_id: Optional service ID filter
        @return List[Document]: Matching documents
        """
        if service_id:
            return [d for d in self._documents.values() if d.service_id == service_id]
        return list(self._documents.values())

    def clear(self) -> None:
        """
        Clears all in-memory database records.

        @return None
        """
        self._services.clear()
        self._documents.clear()


# Global singleton instance
db = MetadataDatabase()
