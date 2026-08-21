"""
Repository service providing repository metadata and directory information.

@author Shubham Upadhyay
@license MIT
"""

from typing import List, Optional
from ..storage.database import db
from ..models.service import ServiceMetadata


class RepositoryService:
    """
    Service to query tracked service repositories.
    """

    def list_all_services(self) -> List[ServiceMetadata]:
        """
        Lists all registered microservices.

        @return List[ServiceMetadata]: List of services
        """
        return db.list_services()

    def get_service_details(self, service_id: str) -> Optional[ServiceMetadata]:
        """
        Retrieves deep metadata for a specific service ID.

        @param str service_id: Unique service identifier
        @return Optional[ServiceMetadata]: Service metadata or None
        """
        return db.get_service(service_id)
