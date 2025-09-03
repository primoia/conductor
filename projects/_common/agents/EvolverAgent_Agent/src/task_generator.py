from typing import List, Dict
import uuid
from datetime import datetime
import os


def generate_task_suggestions(
    complexity_issues: List[Dict],
    security_issues: List[Dict],
    dependency_issues: List[Dict],
) -> List[Dict]:
    """
    Generate task suggestions based on analysis results.

    Args:
        complexity_issues: List of complexity issues
        security_issues: List of security issues
        dependency_issues: List of dependency vulnerabilities

    Returns:
        List of task suggestions
    """
    tasks = []

    # Generate refactoring tasks for complexity issues
    for issue in complexity_issues:
        task = {
            "id": f"REFACTOR-{str(uuid.uuid4())[:8].upper()}",
            "project": extract_project_name(issue["file"]),
            "type": "REFACTORING",
            "priority": get_complexity_priority(issue["complexity"]),
            "description": f"Refactor function '{issue['function']}' with complexity {issue['complexity']}",
            "location": {"file": issue["file"], "line": issue["line"]},
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "estimated_effort": estimate_refactoring_effort(issue["complexity"]),
            "complexity_details": {
                "current_complexity": issue["complexity"],
                "function_name": issue["function"],
                "function_type": issue["type"],
            },
        }
        tasks.append(task)

    # Generate security tasks
    for issue in security_issues:
        task = {
            "id": f"SECURITY-{str(uuid.uuid4())[:8].upper()}",
            "project": extract_project_name(issue["file"]),
            "type": "SECURITY",
            "priority": get_security_priority(issue["severity"]),
            "description": f"Fix security issue: {issue['test_name']}",
            "location": {"file": issue["file"], "line": issue.get("line_number", 1)},
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "estimated_effort": estimate_security_effort(issue["severity"]),
            "security_details": {
                "severity": issue["severity"],
                "confidence": issue["confidence"],
                "test_id": issue.get("test_id", ""),
                "issue_text": issue.get("issue_text", ""),
                "code_snippet": issue.get("code", ""),
            },
        }
        tasks.append(task)

    # Generate dependency update tasks
    for issue in dependency_issues:
        task = {
            "id": f"DEPENDENCY-{str(uuid.uuid4())[:8].upper()}",
            "project": extract_project_name(issue["file"]),
            "type": "DEPENDENCY",
            "priority": get_dependency_priority(issue["severity"]),
            "description": f"Update vulnerable dependency: {issue['package']} {issue['version']}",
            "location": {"file": issue["file"]},
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "estimated_effort": estimate_dependency_effort(issue["severity"]),
            "dependency_details": {
                "package": issue["package"],
                "current_version": issue["version"],
                "vulnerability_id": issue["id"],
                "advisory": issue["advisory"],
                "safe_versions": issue.get("safe_versions", "Unknown"),
                "cve": issue.get("cve", ""),
            },
        }
        tasks.append(task)

    # Sort tasks by priority and estimated effort
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    tasks.sort(
        key=lambda x: (priority_order.get(x["priority"], 4), x["estimated_effort"])
    )

    return tasks


def extract_project_name(file_path: str) -> str:
    """
    Extract project name from file path.

    Args:
        file_path: Path to the file

    Returns:
        Project name
    """
    # Split path and look for project indicators
    path_parts = file_path.split(os.sep)

    # Common project directory indicators
    project_indicators = ["projects", "src", "apps", "services"]

    # Try to find project name based on common patterns
    for i, part in enumerate(path_parts):
        if part in project_indicators and i + 1 < len(path_parts):
            # Next part after indicator is likely the project name
            candidate = path_parts[i + 1]
            # Skip common non-project directories
            if candidate not in ["_common", "shared", "lib", "utils"]:
                return candidate

    # Fallback: use the first directory that's not a common system directory
    for part in path_parts:
        if (
            part
            and not part.startswith(".")
            and part not in ["src", "lib", "app", "main"]
        ):
            return part

    return "unknown-project"


def get_complexity_priority(complexity: int) -> str:
    """
    Determine priority based on cyclomatic complexity.

    Args:
        complexity: Cyclomatic complexity value

    Returns:
        Priority level
    """
    if complexity >= 20:
        return "critical"
    elif complexity >= 15:
        return "high"
    elif complexity >= 11:
        return "medium"
    else:
        return "low"


def get_security_priority(severity: str) -> str:
    """
    Determine priority based on security severity.

    Args:
        severity: Security severity level

    Returns:
        Priority level
    """
    severity_map = {
        "critical": "critical",
        "high": "high",
        "medium": "medium",
        "low": "low",
    }
    return severity_map.get(severity.lower(), "medium")


def get_dependency_priority(severity: str) -> str:
    """
    Determine priority based on dependency vulnerability severity.

    Args:
        severity: Vulnerability severity level

    Returns:
        Priority level
    """
    severity_map = {
        "critical": "critical",
        "high": "high",
        "medium": "medium",
        "low": "low",
    }
    return severity_map.get(severity.lower(), "medium")


def estimate_refactoring_effort(complexity: int) -> str:
    """
    Estimate refactoring effort based on complexity.

    Args:
        complexity: Cyclomatic complexity value

    Returns:
        Effort estimate
    """
    if complexity >= 25:
        return "large"  # 1-2 days
    elif complexity >= 20:
        return "medium"  # 4-8 hours
    elif complexity >= 15:
        return "small"  # 2-4 hours
    else:
        return "minimal"  # < 2 hours


def estimate_security_effort(severity: str) -> str:
    """
    Estimate security fix effort based on severity.

    Args:
        severity: Security severity level

    Returns:
        Effort estimate
    """
    effort_map = {
        "critical": "large",  # Immediate attention needed
        "high": "medium",  # Should be fixed soon
        "medium": "small",  # Can be planned
        "low": "minimal",  # Low priority
    }
    return effort_map.get(severity.lower(), "small")


def estimate_dependency_effort(severity: str) -> str:
    """
    Estimate dependency update effort based on vulnerability severity.

    Args:
        severity: Vulnerability severity level

    Returns:
        Effort estimate
    """
    effort_map = {
        "critical": "medium",  # May require testing
        "high": "small",  # Usually straightforward
        "medium": "small",  # Standard update
        "low": "minimal",  # Low risk update
    }
    return effort_map.get(severity.lower(), "small")


def get_task_type_summary(tasks: List[Dict]) -> Dict:
    """
    Generate summary of task types.

    Args:
        tasks: List of tasks

    Returns:
        Dictionary with task type counts
    """
    summary = {}
    for task in tasks:
        task_type = task["type"]
        summary[task_type] = summary.get(task_type, 0) + 1

    return summary


def get_priority_summary(tasks: List[Dict]) -> Dict:
    """
    Generate summary of task priorities.

    Args:
        tasks: List of tasks

    Returns:
        Dictionary with priority counts
    """
    summary = {}
    for task in tasks:
        priority = task["priority"]
        summary[priority] = summary.get(priority, 0) + 1

    return summary
