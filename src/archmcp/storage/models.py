"""Storage entity wrappers."""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class StoredRecord(BaseModel):
    """Generic record model for internal storage."""
    id: str
    category: str  # service, document, api, architecture
    data: Dict[str, Any]
    created_at: str
    updated_at: Optional[str] = None
