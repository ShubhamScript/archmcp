"""
Architecture document models.

@author Shubham Upadhyay
@license MIT
"""

from typing import Optional
from pydantic import BaseModel, Field


class Document(BaseModel):
    """Representation of an architectural guide, ADR, or microservice documentation snippet."""
    id: str = Field(..., description="Unique document ID")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Markdown or text content")
    service_id: Optional[str] = Field(None, description="Associated microservice ID if applicable")
