"""
Knowledge service providing aggregated domain & architecture intelligence.

@author Shubham Upadhyay
@license MIT
"""

from typing import List, Dict, Any, Optional
from ..storage.database import db
from ..models.api import APIEndpoint
from ..models.database_table import DatabaseTable


class KnowledgeService:
    """
    Provides high-level knowledge queries such as finding who owns an API or DB table.
    """

    def get_service_apis(self, service_id: str) -> Optional[List[APIEndpoint]]:
        """
        Retrieves all APIs exposed by a service ID.

        @param str service_id: Unique service identifier
        @return Optional[List[APIEndpoint]]: List of API endpoints or None
        """
        svc = db.get_service(service_id)
        if not svc:
            return None
        return svc.apis

    def get_database_schema(self, service_id: str) -> Optional[List[DatabaseTable]]:
        """
        Retrieves database tables owned by a service ID.

        @param str service_id: Unique service identifier
        @return Optional[List[DatabaseTable]]: List of database tables or None
        """
        svc = db.get_service(service_id)
        if not svc:
            return None
        return svc.database_tables

    def find_api_by_route(self, route_pattern: str) -> List[Dict[str, Any]]:
        """
        Finds which microservice owns an API path.

        @param str route_pattern: URL path fragment or keyword
        @return List[Dict[str, Any]]: List of matching service ownership records
        """
        matches = []
        pattern = route_pattern.lower()
        for svc in db.list_services():
            for api in svc.apis:
                if pattern in api.path.lower() or pattern in api.summary.lower():
                    matches.append({
                        "service_id": svc.id,
                        "service_name": svc.name,
                        "owner": svc.owner,
                        "api": api.model_dump()
                    })
        return matches

    def find_table_owner(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Finds which microservice owns a given database table.

        @param str table_name: Table name string
        @return List[Dict[str, Any]]: List of matching service ownership records
        """
        matches = []
        name = table_name.lower()
        for svc in db.list_services():
            for table in svc.database_tables:
                if name in table.name.lower():
                    matches.append({
                        "service_id": svc.id,
                        "service_name": svc.name,
                        "owner": svc.owner,
                        "table": table.model_dump()
                    })
        return matches
