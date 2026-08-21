"""
Authentication data models.

@author Shubham Upadhyay
@license MIT
"""

from typing import List
from pydantic import BaseModel, Field


class AuthUser(BaseModel):
    """Authenticated user / developer identity."""
    token: str
    username: str = Field("developer", description="Identifier of the calling user or system")
    roles: List[str] = Field(default_factory=lambda: ["engineer"])
