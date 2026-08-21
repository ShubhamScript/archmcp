"""
Git ingestion pipeline for pulling repository metadata and documentation.

@author Shubham Upadhyay
@license MIT
"""

import logging
from ..models.repository import RepositoryInfo
from ..repositories.git_repository import GitRepositoryClient

logger = logging.getLogger(__name__)


class GitIngestionPipeline:
    """
    Ingestion pipeline for pulling metadata and docs from Git sources.
    """

    @staticmethod
    def ingest_repository(repo: RepositoryInfo) -> str:
        """
        Ingests documentation from a repository client.

        @param RepositoryInfo repo: Repository metadata info
        @return str: Ingested README content
        """
        client = GitRepositoryClient(repo)
        readme = client.get_readme()
        logger.info(f"Ingested repository {repo.id} from {repo.repo_url}")
        return readme
