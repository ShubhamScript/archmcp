"""
ArchMCP - In-Memory Metadata Database with Multi-Tenant Partitioning.

@author Shubham Upadhyay
@license MIT
"""

from typing import Dict, List, Optional
import threading
from ..models.service import ServiceMetadata
from ..models.document import Document


class MetadataDatabase:
    """
    Fast in-memory store for microservice metadata and architecture documents with multi-tenant isolation.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._services: Dict[str, ServiceMetadata] = {}
        self._documents: Dict[str, Document] = {}

    def save_service(self, service: ServiceMetadata) -> None:
        """
        Upserts a microservice metadata record.

        @param ServiceMetadata service: Service metadata object to store
        @return None
        """
        with self._lock:
            self._services[service.id] = service

    def get_service(self, service_id: str, tenant_id: Optional[str] = None) -> Optional[ServiceMetadata]:
        """
        Retrieves a microservice record by ID with optional tenant isolation.

        @param str service_id: Unique service identifier
        @param Optional[str] tenant_id: Tenant filter
        @return Optional[ServiceMetadata]: Service metadata or None
        """
        with self._lock:
            svc = self._services.get(service_id)
            if not svc:
                return None
            if tenant_id and svc.tenant_id != tenant_id:
                return None
            return svc

    def list_services(self, tenant_id: Optional[str] = None) -> List[ServiceMetadata]:
        """
        Returns all registered microservices matching tenant filter.

        @param Optional[str] tenant_id: Optional tenant isolation filter
        @return List[ServiceMetadata]: List of tracked microservices
        """
        with self._lock:
            services = list(self._services.values())
            if tenant_id:
                return [s for s in services if s.tenant_id == tenant_id]
            return services

    def save_document(self, doc: Document) -> None:
        """
        Saves an architecture document.

        @param Document doc: Architecture document object
        @return None
        """
        with self._lock:
            self._documents[doc.id] = doc

    def get_document(self, doc_id: str, tenant_id: Optional[str] = None) -> Optional[Document]:
        """
        Retrieves a document by ID with optional tenant isolation.

        @param str doc_id: Unique document identifier
        @param Optional[str] tenant_id: Tenant filter
        @return Optional[Document]: Document object or None
        """
        with self._lock:
            doc = self._documents.get(doc_id)
            if not doc:
                return None
            if tenant_id and doc.tenant_id != tenant_id:
                return None
            return doc

    def list_documents(self, service_id: Optional[str] = None, tenant_id: Optional[str] = None) -> List[Document]:
        """
        Returns documents optionally filtered by service ID and tenant ID.

        @param Optional[str] service_id: Optional service ID filter
        @param Optional[str] tenant_id: Optional tenant ID filter
        @return List[Document]: Matching documents
        """
        with self._lock:
            docs = list(self._documents.values())
            if tenant_id:
                docs = [d for d in docs if d.tenant_id == tenant_id]
            if service_id:
                docs = [d for d in docs if d.service_id == service_id]
            return docs

    def clear(self) -> None:
        """
        Clears all in-memory database records.

        @return None
        """
        with self._lock:
            self._services.clear()
            self._documents.clear()


# Global singleton instance
db = MetadataDatabase()
