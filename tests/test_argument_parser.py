import argparse
import pytest
from src.cli.shared.argument_parser import CLIArgumentParser


class TestCLIArgumentParser:
    """Unit tests for the shared CLI argument parser."""

    def test_validate_admin_args_meta_ok(self, capsys):
        """Test successful validation with --meta flag."""
        args = argparse.Namespace(meta=True, environment=None, project=None)
        assert CLIArgumentParser.validate_admin_args(args) is True

    def test_validate_admin_args_project_ok(self, capsys):
        """Test successful validation for a project agent."""
        args = argparse.Namespace(meta=False, environment="develop", project="myapp")
        assert CLIArgumentParser.validate_admin_args(args) is True

    def test_validate_admin_args_meta_with_project_fails(self, capsys):
        """Test validation failure when --meta is used with --project."""
        args = argparse.Namespace(meta=True, environment=None, project="myapp")
        assert CLIArgumentParser.validate_admin_args(args) is False
        captured = capsys.readouterr()
        assert "Error: --meta flag cannot be used with" in captured.out

    def test_validate_admin_args_meta_with_environment_fails(self, capsys):
        """Test validation failure when --meta is used with --environment."""
        args = argparse.Namespace(meta=True, environment="develop", project=None)
        assert CLIArgumentParser.validate_admin_args(args) is False
        captured = capsys.readouterr()
        assert "Error: --meta flag cannot be used with" in captured.out

    def test_validate_admin_args_project_missing_environment_fails(self, capsys):
        """Test validation failure for project agent missing --environment."""
        args = argparse.Namespace(meta=False, environment=None, project="myapp")
        assert CLIArgumentParser.validate_admin_args(args) is False
        captured = capsys.readouterr()
        assert "Error: --environment and --project are required" in captured.out

    def test_validate_admin_args_project_missing_project_fails(self, capsys):
        """Test validation failure for project agent missing --project."""
        args = argparse.Namespace(meta=False, environment="develop", project=None)
        assert CLIArgumentParser.validate_admin_args(args) is False
        captured = capsys.readouterr()
        assert "Error: --environment and --project are required" in captured.out
