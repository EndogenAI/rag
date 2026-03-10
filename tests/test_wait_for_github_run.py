"""Tests for wait_for_github_run.py."""

import os
import subprocess
import sys
from unittest.mock import MagicMock, patch

# Add scripts directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

# Now import the module
from wait_for_github_run import get_run_status, main


class TestGetRunStatus:
    """Test get_run_status function."""

    @patch("subprocess.run")
    def test_get_run_status_in_progress(self, mock_run):
        """Test fetching status of in-progress run."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"status": "in_progress", "conclusion": null}\n',
        )
        status, conclusion = get_run_status("12345", "owner/repo")
        assert status == "in_progress"
        assert conclusion is None

    @patch("subprocess.run")
    def test_get_run_status_completed_success(self, mock_run):
        """Test fetching status of completed successful run."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"status": "completed", "conclusion": "success"}\n',
        )
        status, conclusion = get_run_status("12345", "owner/repo")
        assert status == "completed"
        assert conclusion == "success"

    @patch("subprocess.run")
    def test_get_run_status_completed_failure(self, mock_run):
        """Test fetching status of completed failed run."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"status": "completed", "conclusion": "failure"}\n',
        )
        status, conclusion = get_run_status("12345", "owner/repo")
        assert status == "completed"
        assert conclusion == "failure"

    @patch("subprocess.run")
    def test_get_run_status_gh_error(self, mock_run):
        """Test handling of gh CLI error."""
        mock_run.return_value = MagicMock(returncode=1, stderr="error")
        status, conclusion = get_run_status("12345", "owner/repo")
        assert status is None
        assert conclusion is None

    @patch("subprocess.run")
    def test_get_run_status_json_parse_error(self, mock_run):
        """Test handling of invalid JSON response."""
        mock_run.return_value = MagicMock(returncode=0, stdout="invalid json\n")
        status, conclusion = get_run_status("12345", "owner/repo")
        assert status is None
        assert conclusion is None

    @patch("subprocess.run")
    def test_get_run_status_timeout(self, mock_run):
        """Test handling of timeout during status fetch."""
        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 10)
        status, conclusion = get_run_status("12345", "owner/repo")
        assert status is None
        assert conclusion is None


class TestMain:
    """Test main polling logic."""

    @patch("wait_for_github_run.get_run_status")
    def test_main_success_immediately(self, mock_get_status, capsys):
        """Test run that completes successfully on first poll."""
        mock_get_status.return_value = ("completed", "success")

        with patch.object(sys, "argv", ["wait_for_github_run.py", "12345"]):
            result = main()

        assert result == 0
        captured = capsys.readouterr()
        assert "✓ Run completed successfully" in captured.out

    @patch("wait_for_github_run.get_run_status")
    def test_main_failure_immediately(self, mock_get_status, capsys):
        """Test run that fails on first poll."""
        mock_get_status.return_value = ("completed", "failure")

        with patch.object(sys, "argv", ["wait_for_github_run.py", "12345"]):
            result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "✗ Run completed with conclusion: failure" in captured.out

    @patch("wait_for_github_run.get_run_status")
    @patch("time.sleep")
    def test_main_success_after_polling(self, mock_sleep, mock_get_status, capsys):
        """Test run that completes successfully after a few polls."""
        # First two polls return in_progress, third returns success
        mock_get_status.side_effect = [
            ("in_progress", None),
            ("in_progress", None),
            ("completed", "success"),
        ]

        with patch.object(sys, "argv", ["wait_for_github_run.py", "12345"]):
            result = main()

        assert result == 0
        assert mock_sleep.call_count == 2  # Called between first and second, second and third

    @patch("wait_for_github_run.get_run_status")
    @patch("time.sleep")
    def test_main_timeout(self, mock_sleep, mock_get_status, capsys):
        """Test timeout is reached before run completes."""
        # Always return in_progress
        mock_get_status.return_value = ("in_progress", None)

        with patch.object(
            sys,
            "argv",
            ["wait_for_github_run.py", "12345", "--timeout-secs", "10", "--interval-secs", "5"],
        ):
            result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "Timeout reached" in captured.out

    @patch("wait_for_github_run.get_run_status")
    def test_main_fetch_error_recovery(self, mock_get_status, capsys):
        """Test that fetch errors don't stop polling."""
        # Returns error, then success
        mock_get_status.side_effect = [
            (None, None),
            ("completed", "success"),
        ]

        with patch.object(
            sys,
            "argv",
            ["wait_for_github_run.py", "12345", "--timeout-secs", "20", "--interval-secs", "5"],
        ):
            with patch("time.sleep"):
                result = main()

        assert result == 0
        captured = capsys.readouterr()
        assert "Could not fetch run status" in captured.out

    @patch("wait_for_github_run.get_run_status")
    def test_main_custom_repo(self, mock_get_status, capsys):
        """Test that custom repo is passed correctly."""
        mock_get_status.return_value = ("completed", "success")

        with patch.object(
            sys,
            "argv",
            ["wait_for_github_run.py", "12345", "--repo", "other/repo"],
        ):
            result = main()

        assert result == 0
        # Verify get_run_status was called with custom repo
        mock_get_status.assert_called_once()
        call_args = mock_get_status.call_args
        # get_run_status(run_id, repo) — check positional args or kwargs
        assert call_args[0][1] == "other/repo" or call_args[1].get("repo") == "other/repo"
