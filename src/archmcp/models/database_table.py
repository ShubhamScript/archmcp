"""
Database table and schema models.

@author Shubham Upadhyay
@license MIT
"""

from typing import List
from pydantic import BaseModel, Field


class DatabaseTable(BaseModel):
    """Representation of a database table owned by a microservice."""
    name: str = Field(..., description="Table name e.g. users, orders")
    description: str = Field("", description="Purpose and business context of this table")
    columns: List[str] = Field(default_factory=list, description="Column names and data types")
