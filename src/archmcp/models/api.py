"""
API route and endpoint data models.

@author Shubham Upadhyay
@license MIT
"""

from typing import Optional
from pydantic import BaseModel, Field


class APIEndpoint(BaseModel):
    """Representation of an exposed REST or gRPC endpoint in a microservice."""
    path: str = Field(..., description="Route URI path (e.g. /api/v1/orders)")
    method: str = Field(..., description="HTTP Method (GET, POST, PUT, DELETE)")
    summary: str = Field(..., description="Short explanation of endpoint purpose")
    description: Optional[str] = Field(None, description="Detailed request/response documentation")
