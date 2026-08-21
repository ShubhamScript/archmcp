"""
Git repository interface abstraction.

@author Shubham Upadhyay
@license MIT
"""

from ..models.repository import RepositoryInfo


class GitRepositoryClient:
    """
    Simulates repository operations such as fetching README or commit hash.
    """

    def __init__(self, repo_info: RepositoryInfo) -> None:
        self.repo_info = repo_info

    def get_readme(self) -> str:
        """
        Returns simulated README markdown content.

        @return str: Markdown README text
        """
        return f"# {self.repo_info.name}\n\nRemote URL: {self.repo_info.repo_url}\nPrimary Branch: {self.repo_info.default_branch}"

    def get_latest_commit(self) -> str:
        """
        Returns mock latest commit SHA.

        @return str: Commit hash string
        """
        return "a1b2c3d4e5f67890"
