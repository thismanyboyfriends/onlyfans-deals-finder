"""Tests for CLI module."""
import pytest
import sys
import os
from pathlib import Path
from click.testing import CliRunner

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from cli import (
    get_default_chrome_path,
    get_default_user_data_dir,
    cli,
)


class TestCLIDefaults:
    """Tests for CLI default path functions."""

    def test_get_default_chrome_path_returns_string(self):
        """Test that default Chrome path is a string."""
        path = get_default_chrome_path()
        assert isinstance(path, str)
        assert len(path) > 0

    def test_get_default_chrome_path_platform_aware(self):
        """Test that Chrome path is platform-appropriate."""
        path = get_default_chrome_path()
        if os.name == 'nt':
            # Windows
            assert 'chrome.exe' in path.lower() or 'chrome' in path.lower()
        else:
            # Unix-like
            assert 'chrome' in path.lower()

    def test_get_default_user_data_dir_returns_string(self):
        """Test that default user data dir is a string."""
        path = get_default_user_data_dir()
        assert isinstance(path, str)
        assert len(path) > 0

    def test_get_default_user_data_dir_platform_aware(self):
        """Test that user data dir is platform-appropriate."""
        path = get_default_user_data_dir()
        if os.name == 'nt':
            # Windows
            assert 'tempchromdir' in path.lower() or 'chrome' in path.lower()
        else:
            # Unix-like
            assert '.config' in path or 'chrome' in path.lower()


class TestCLICommands:
    """Tests for CLI commands."""

    def test_cli_help(self):
        """Test that CLI help command works."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'Usage:' in result.output

    def test_cli_version(self):
        """Test that CLI version command works."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        assert '1.0.0' in result.output or 'OnlyFans Deals Finder' in result.output

    def test_config_command(self):
        """Test that config command shows configuration."""
        runner = CliRunner()
        result = runner.invoke(cli, ['config'])
        assert result.exit_code == 0
        assert 'Configuration' in result.output or 'Chrome' in result.output

    def test_scrape_help(self):
        """Test that scrape command help works."""
        runner = CliRunner()
        result = runner.invoke(cli, ['scrape', '--help'])
        assert result.exit_code == 0
        assert 'list-id' in result.output.lower() or 'List' in result.output

    def test_stats_help(self):
        """Test that stats command help works."""
        runner = CliRunner()
        result = runner.invoke(cli, ['stats', '--help'])
        assert result.exit_code == 0

    def test_deals_help(self):
        """Test that deals command help works."""
        runner = CliRunner()
        result = runner.invoke(cli, ['deals', '--help'])
        assert result.exit_code == 0

    def test_history_help(self):
        """Test that history command help works."""
        runner = CliRunner()
        result = runner.invoke(cli, ['history', '--help'])
        assert result.exit_code == 0

    def test_user_help(self):
        """Test that user command help works."""
        runner = CliRunner()
        result = runner.invoke(cli, ['user', '--help'])
        assert result.exit_code == 0
        assert 'USERNAME' in result.output or 'username' in result.output

    def test_new_deals_help(self):
        """Test that new-deals command help works."""
        runner = CliRunner()
        result = runner.invoke(cli, ['new-deals', '--help'])
        assert result.exit_code == 0
