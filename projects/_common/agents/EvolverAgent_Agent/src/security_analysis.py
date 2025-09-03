import subprocess
import json
import tempfile
import os
import glob
from pathlib import Path
from typing import List, Dict


def analyze_security_issues(repo_path: str) -> List[Dict]:
    """
    Analyze security issues using bandit.

    Args:
        repo_path: Path to the repository root

    Returns:
        List of security issues found
    """
    security_issues = []
    repo_path = Path(repo_path)

    try:
        # Create temporary file for bandit output
        with tempfile.NamedTemporaryFile(
            mode="w+", suffix=".json", delete=False
        ) as temp_file:
            temp_output = temp_file.name

        # Run bandit on Python files
        cmd = [
            "bandit",
            "-r",
            str(repo_path),
            "-f",
            "json",
            "-o",
            temp_output,
            "--exclude",
            "**/node_modules/**,**/venv/**,**/.git/**,**/build/**,**/dist/**",
        ]

        # Run bandit and capture result
        result = subprocess.run(cmd, capture_output=True, text=True)

        # Read the output file
        if os.path.exists(temp_output):
            with open(temp_output, "r") as f:
                bandit_data = json.load(f)

            # Parse bandit results
            for result_item in bandit_data.get("results", []):
                # Get relative path from repo root
                file_path = os.path.relpath(result_item["filename"], repo_path)

                issue = {
                    "file": file_path,
                    "line_number": result_item["line_number"],
                    "test_name": result_item["test_name"],
                    "test_id": result_item["test_id"],
                    "issue_severity": result_item["issue_severity"],
                    "issue_confidence": result_item["issue_confidence"],
                    "issue_text": result_item["issue_text"],
                    "code": result_item.get("code", "").strip(),
                    "severity": map_bandit_severity(result_item["issue_severity"]),
                    "confidence": result_item["issue_confidence"],
                }
                security_issues.append(issue)

        # Clean up temp file
        if os.path.exists(temp_output):
            os.unlink(temp_output)

    except Exception as e:
        print(f"Warning: Could not run bandit security analysis: {e}")

    return security_issues


def analyze_dependency_vulnerabilities(repo_path: str) -> List[Dict]:
    """
    Analyze dependency vulnerabilities using safety.

    Args:
        repo_path: Path to the repository root

    Returns:
        List of dependency vulnerabilities found
    """
    vulnerabilities = []
    repo_path = Path(repo_path)

    # Find all requirements.txt files in the repository
    requirements_files = []
    for pattern in ["**/requirements*.txt", "**/Pipfile", "**/pyproject.toml"]:
        requirements_files.extend(glob.glob(str(repo_path / pattern), recursive=True))

    for req_file in requirements_files:
        try:
            # Create temporary file for safety output
            with tempfile.NamedTemporaryFile(
                mode="w+", suffix=".json", delete=False
            ) as temp_file:
                temp_output = temp_file.name

            # Run safety check
            cmd = ["safety", "check", "-r", req_file, "--json", "--output", temp_output]

            result = subprocess.run(cmd, capture_output=True, text=True)

            # Read the output file
            if os.path.exists(temp_output):
                with open(temp_output, "r") as f:
                    content = f.read().strip()
                    if content:
                        safety_data = json.loads(content)

                        # Parse safety results
                        for vuln in safety_data:
                            # Get relative path from repo root
                            file_path = os.path.relpath(req_file, repo_path)

                            vulnerability = {
                                "file": file_path,
                                "package": vuln["package_name"],
                                "version": vuln["analyzed_version"],
                                "id": vuln["vulnerability_id"],
                                "advisory": vuln["advisory"],
                                "severity": map_safety_severity(
                                    vuln.get("severity", "medium")
                                ),
                                "cve": vuln.get("cve", ""),
                                "affected_versions": vuln.get("affected_versions", ""),
                                "safe_versions": vuln.get("safe_versions", ""),
                            }
                            vulnerabilities.append(vulnerability)

            # Clean up temp file
            if os.path.exists(temp_output):
                os.unlink(temp_output)

        except Exception as e:
            print(f"Warning: Could not analyze {req_file} with safety: {e}")
            continue

    return vulnerabilities


def map_bandit_severity(bandit_severity: str) -> str:
    """
    Map bandit severity levels to standard severity levels.

    Args:
        bandit_severity: Bandit severity level

    Returns:
        Standardized severity level
    """
    severity_map = {"HIGH": "critical", "MEDIUM": "high", "LOW": "medium"}
    return severity_map.get(bandit_severity.upper(), "low")


def map_safety_severity(safety_severity: str) -> str:
    """
    Map safety severity levels to standard severity levels.

    Args:
        safety_severity: Safety severity level

    Returns:
        Standardized severity level
    """
    severity_map = {
        "critical": "critical",
        "high": "high",
        "medium": "medium",
        "low": "low",
    }
    return severity_map.get(safety_severity.lower(), "medium")


def get_security_summary(
    security_issues: List[Dict], dependency_issues: List[Dict]
) -> Dict:
    """
    Generate summary statistics for security analysis.

    Args:
        security_issues: List of security issues
        dependency_issues: List of dependency vulnerabilities

    Returns:
        Dictionary with security summary statistics
    """
    security_by_severity = {}
    for issue in security_issues:
        severity = issue["severity"]
        security_by_severity[severity] = security_by_severity.get(severity, 0) + 1

    deps_by_severity = {}
    for issue in dependency_issues:
        severity = issue["severity"]
        deps_by_severity[severity] = deps_by_severity.get(severity, 0) + 1

    return {
        "total_security_issues": len(security_issues),
        "total_dependency_issues": len(dependency_issues),
        "security_by_severity": security_by_severity,
        "dependencies_by_severity": deps_by_severity,
        "unique_vulnerable_packages": len(
            set(issue["package"] for issue in dependency_issues)
        ),
    }
