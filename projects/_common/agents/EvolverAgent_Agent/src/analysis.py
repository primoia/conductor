import glob
import os
from pathlib import Path
from typing import List, Dict
from radon.complexity import cc_visit


def analyze_repo(repo_path: str) -> List[Dict]:
    """
    Analyze the repository for code complexity issues.
    
    Args:
        repo_path: Path to the repository root
        
    Returns:
        List of dictionaries containing complexity issues found
    """
    repo_path = Path(repo_path)
    problems = []
    
    # Find all Python files in the repository
    python_files = glob.glob(str(repo_path / "**" / "*.py"), recursive=True)
    
    for file_path in python_files:
        try:
            # Read the file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Calculate cyclomatic complexity using radon
            complexity_results = cc_visit(content)
            
            # Filter for functions/methods with complexity > 10
            for result in complexity_results:
                if result.complexity > 10:
                    # Get relative path from repo root
                    relative_path = os.path.relpath(file_path, repo_path)
                    
                    problem = {
                        'file': relative_path,
                        'function': result.name,
                        'complexity': result.complexity,
                        'line': result.lineno,
                        'type': result.type  # 'function', 'method', or 'class'
                    }
                    problems.append(problem)
                    
        except Exception as e:
            # Skip files that can't be parsed (e.g., syntax errors)
            print(f"Warning: Could not analyze {file_path}: {e}")
            continue
    
    return problems


def analyze_file_complexity(file_path: str) -> List[Dict]:
    """
    Analyze a single Python file for complexity issues.
    
    Args:
        file_path: Path to the Python file
        
    Returns:
        List of dictionaries containing complexity issues in the file
    """
    problems = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        complexity_results = cc_visit(content)
        
        for result in complexity_results:
            if result.complexity > 10:
                problem = {
                    'file': file_path,
                    'function': result.name,
                    'complexity': result.complexity,
                    'line': result.lineno,
                    'type': result.type
                }
                problems.append(problem)
                
    except Exception as e:
        print(f"Warning: Could not analyze {file_path}: {e}")
    
    return problems