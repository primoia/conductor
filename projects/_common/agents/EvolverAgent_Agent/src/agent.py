import os
import sys
from datetime import datetime
from pathlib import Path
from git import Repo
from git.exc import InvalidGitRepositoryError

from .knowledge_base import KnowledgeBase
from .analysis import analyze_repo
from .security_analysis import (
    analyze_security_issues,
    analyze_dependency_vulnerabilities,
    get_security_summary,
)
from .task_generator import generate_task_suggestions
from .artifacts import (
    generate_health_report,
    generate_summary_stats,
    generate_task_suggestions_json,
    generate_enhanced_health_report,
)


class EvolverAgent:
    """
    The main EvolverAgent that analyzes the repository for code quality issues
    and generates health reports while avoiding redundant work.
    """

    def __init__(self):
        """Initialize the EvolverAgent."""
        self.repo_path = self._get_repo_path()
        self.knowledge_base = KnowledgeBase(self.repo_path)

    def _get_repo_path(self) -> str:
        """
        Get the repository root path. In Docker container, use /monorepo.
        Otherwise, try to detect the repository root.

        Returns:
            Path to the repository root
        """
        # Check if running in Docker container with mounted volume
        docker_repo_path = Path("/monorepo")
        if docker_repo_path.exists() and (docker_repo_path / ".git").exists():
            return str(docker_repo_path.absolute())

        # Fallback: Get the current script's directory and go up levels
        current_dir = Path(__file__).parent.absolute()

        # Go up 6 levels to reach primoia-main/primoia-monorepo
        # Note: This agent is in legacy structure and should be migrated to .conductor_workspace/agents/
        # Current structure: .../primoia-monorepo/projects/conductor/projects/_common/agents/EvolverAgent_Agent/src
        repo_path = current_dir.parent.parent.parent.parent.parent.parent.parent

        return str(repo_path.absolute())

    def _get_current_commit_hash(self) -> str:
        """
        Get the current Git commit hash.

        Returns:
            The current commit hash

        Raises:
            SystemExit: If the repository is not a valid Git repository
        """
        try:
            repo = Repo(self.repo_path)
            return repo.head.commit.hexsha
        except InvalidGitRepositoryError:
            print("Error: Not a valid Git repository")
            sys.exit(1)

    def run(self) -> None:
        """
        Main execution method for the EvolverAgent Phase 2.

        This method orchestrates the comprehensive analysis process:
        1. Gets the current commit hash
        2. Checks if the commit has already been analyzed
        3. If not, performs complexity, security, and dependency analysis
        4. Generates task suggestions and enhanced reports
        5. Stores the results in the knowledge base
        """
        print("🧠 EvolverAgent Phase 2 Starting...")
        print(f"📁 Repository path: {self.repo_path}")

        # Get current commit hash
        commit_hash = self._get_current_commit_hash()
        print(f"📋 Current commit: {commit_hash[:8]}")

        # Check if this commit has already been analyzed
        if self.knowledge_base.has_commit(commit_hash):
            print("✅ This commit has already been analyzed. Exiting.")
            return

        print("🔍 Running comprehensive analysis...")

        # Perform the repository analysis
        try:
            # Perform complexity analysis
            complexity_results = analyze_repo(self.repo_path)
            print(f"📊 Found {len(complexity_results)} complexity issues")

            # Perform security analysis
            security_results = analyze_security_issues(self.repo_path)
            print(f"🔒 Found {len(security_results)} security issues")

            # Perform dependency analysis
            dependency_results = analyze_dependency_vulnerabilities(self.repo_path)
            print(f"📦 Found {len(dependency_results)} dependency issues")

            # Generate task suggestions
            task_suggestions = generate_task_suggestions(
                complexity_results, security_results, dependency_results
            )
            print(f"📋 Generated {len(task_suggestions)} task suggestions")

            # Generate artifacts
            generate_enhanced_health_report(
                complexity_results, security_results, dependency_results, self.repo_path
            )
            generate_task_suggestions_json(task_suggestions, self.repo_path)
            print("📄 Enhanced reports generated")

            # Generate summary statistics
            complexity_stats = generate_summary_stats(complexity_results)
            security_stats = get_security_summary(security_results, dependency_results)

            # Prepare results for storage
            results = {
                "commit_hash": commit_hash,
                "timestamp": datetime.now().isoformat(),
                "complexity_results": complexity_results,
                "security_results": security_results,
                "dependency_results": dependency_results,
                "task_suggestions": task_suggestions,
                "complexity_stats": complexity_stats,
                "security_stats": security_stats,
                "agent_version": "Phase2-1.0",
            }

            # Store results in knowledge base
            self.knowledge_base.store_results(commit_hash, results)
            print("💾 Results stored in knowledge base")

            print("✅ EvolverAgent Phase 2 analysis completed successfully!")

        except Exception as e:
            print(f"❌ Error during analysis: {e}")
            sys.exit(1)

    def get_repo_info(self) -> dict:
        """
        Get basic repository information.

        Returns:
            Dictionary with repository information
        """
        try:
            repo = Repo(self.repo_path)
            return {
                "repo_path": self.repo_path,
                "current_branch": repo.active_branch.name,
                "current_commit": repo.head.commit.hexsha,
                "is_dirty": repo.is_dirty(),
                "remote_url": repo.remotes.origin.url if repo.remotes else None,
            }
        except Exception as e:
            return {"repo_path": self.repo_path, "error": str(e)}
