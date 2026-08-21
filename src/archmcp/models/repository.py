"""
Repository metadata models.

@author Shubham Upadhyay
@license MIT
"""

from pydantic import BaseModel, Field


class RepositoryInfo(BaseModel):
    """Metadata representation of a source code repository."""
    id: str = Field(..., description="Service identifier")
    name: str = Field(..., description="Service display name")
    repo_url: str = Field(..., description="Git remote URL")
    default_branch: str = Field("main", description="Primary Git branch")
