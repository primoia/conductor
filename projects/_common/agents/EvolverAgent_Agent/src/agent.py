import os
import sys
from pathlib import Path
from git import Repo
from git.exc import InvalidGitRepositoryError

from .knowledge_base import KnowledgeBase
from .analysis import analyze_repo
from .artifacts import generate_health_report, generate_summary_stats


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
        Get the repository root path by going up 6 levels from the script location
        to reach primoia-main/primoia-monorepo.
        
        Returns:
            Path to the repository root
        """
        # Get the current script's directory
        current_dir = Path(__file__).parent.absolute()
        
        # Go up 6 levels to reach primoia-main/primoia-monorepo
        # Current structure: .../primoia-monorepo/projects/conductor/projects/_common/agents/EvolverAgent_Agent/src
        # Need to go up: src -> EvolverAgent_Agent -> agents -> _common -> projects -> conductor -> projects -> primoia-monorepo
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
        Main execution method for the EvolverAgent.
        
        This method orchestrates the entire analysis process:
        1. Gets the current commit hash
        2. Checks if the commit has already been analyzed
        3. If not, performs the analysis and generates reports
        4. Stores the results in the knowledge base
        """
        print("🧠 EvolverAgent MVP Starting...")
        print(f"📁 Repository path: {self.repo_path}")
        
        # Get current commit hash
        commit_hash = self._get_current_commit_hash()
        print(f"📋 Current commit: {commit_hash[:8]}")
        
        # Check if this commit has already been analyzed
        if self.knowledge_base.has_commit(commit_hash):
            print("✅ This commit has already been analyzed. Exiting.")
            return
        
        print("🔍 Running analysis...")
        
        # Perform the repository analysis
        try:
            analysis_results = analyze_repo(self.repo_path)
            print(f"📊 Found {len(analysis_results)} complexity issues")
            
            # Generate summary statistics
            stats = generate_summary_stats(analysis_results)
            
            # Generate the health report
            generate_health_report(analysis_results, self.repo_path)
            print("📄 Health report generated")
            
            # Prepare results for storage
            results = {
                'commit_hash': commit_hash,
                'timestamp': None,  # Will be set by datetime in generate_health_report
                'analysis_results': analysis_results,
                'summary_stats': stats,
                'agent_version': 'MVP-1.0'
            }
            
            # Store results in knowledge base
            self.knowledge_base.store_results(commit_hash, results)
            print("💾 Results stored in knowledge base")
            
            print("✅ EvolverAgent analysis completed successfully!")
            
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
                'repo_path': self.repo_path,
                'current_branch': repo.active_branch.name,
                'current_commit': repo.head.commit.hexsha,
                'is_dirty': repo.is_dirty(),
                'remote_url': repo.remotes.origin.url if repo.remotes else None
            }
        except Exception as e:
            return {
                'repo_path': self.repo_path,
                'error': str(e)
            }