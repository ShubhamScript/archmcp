"""
Context service that compiles full context payloads for AI models.

@author Shubham Upadhyay
@license MIT
"""

from typing import Optional, Dict, Any
from ..storage.database import db


class ContextService:
    """
    Compiles complete multi-angle context package for an AI assistant working on a task.
    """

    def assemble_service_context(self, service_id: str) -> Optional[Dict[str, Any]]:
        """
        Assembles metadata, documentation, and prompt guidelines for a microservice.

        @param str service_id: Unique service identifier
        @return Optional[Dict[str, Any]]: Full context dictionary or None
        """
        svc = db.get_service(service_id)
        if not svc:
            return None

        docs = db.list_documents(service_id=service_id)

        return {
            "service": svc.model_dump(),
            "documentation": [d.model_dump() for d in docs],
            "recommended_prompt_guidelines": f"When modifying {svc.name}, ensure compatibility with upstream ({', '.join(svc.dependencies.upstream) or 'None'}) and downstream ({', '.join(svc.dependencies.downstream) or 'None'})."
        }
