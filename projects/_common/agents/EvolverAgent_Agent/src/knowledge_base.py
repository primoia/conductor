import json
import os
from pathlib import Path


class KnowledgeBase:
    """
    Manages the knowledge base for the EvolverAgent, storing analysis results
    keyed by Git commit hash to avoid redundant work.
    """

    def __init__(self, repo_path: str):
        """
        Initialize the knowledge base.

        Args:
            repo_path: Path to the repository root
        """
        self.repo_path = Path(repo_path)
        self.knowledge_base_dir = self.repo_path / ".evolver" / "knowledge_base"

        # Ensure the knowledge base directory exists
        self.knowledge_base_dir.mkdir(parents=True, exist_ok=True)

    def has_commit(self, commit_hash: str) -> bool:
        """
        Check if analysis results for a given commit hash already exist.

        Args:
            commit_hash: The Git commit hash

        Returns:
            True if the commit has been analyzed before, False otherwise
        """
        knowledge_file = self.knowledge_base_dir / f"{commit_hash}.json"
        return knowledge_file.exists()

    def store_results(self, commit_hash: str, results: dict) -> None:
        """
        Store analysis results for a given commit hash.

        Args:
            commit_hash: The Git commit hash
            results: Dictionary containing the analysis results
        """
        knowledge_file = self.knowledge_base_dir / f"{commit_hash}.json"

        with open(knowledge_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

    def get_results(self, commit_hash: str) -> dict:
        """
        Retrieve analysis results for a given commit hash.

        Args:
            commit_hash: The Git commit hash

        Returns:
            Dictionary containing the analysis results, or empty dict if not found
        """
        knowledge_file = self.knowledge_base_dir / f"{commit_hash}.json"

        if not knowledge_file.exists():
            return {}

        with open(knowledge_file, "r", encoding="utf-8") as f:
            return json.load(f)
