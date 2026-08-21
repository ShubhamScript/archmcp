"""=============================================================================
ArchMCP - Repositories Package
=============================================================================
This package handles everything related to repository discovery and abstraction.

CONCEPT:
In a microservices organization, you have many code repositories (one per service).
This package provides:
1. `RepositoryRegistry`: Reads configuration (e.g. data/repositories.yaml) to track
   what repositories exist in the organization.
2. `GitRepositoryClient`: An abstraction layer to interact with Git providers (GitHub,
   GitLab, Bitbucket) to fetch READMEs, commits, and code files.
=============================================================================
"""

from .repository_registry import RepositoryRegistry
from .git_repository import GitRepositoryClient

__all__ = ["RepositoryRegistry", "GitRepositoryClient"]
