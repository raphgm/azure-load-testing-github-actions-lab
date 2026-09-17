"""
Unit tests for check_run.py's polling loop signal — the part that decides
whether the workflow's exit code means "PR can merge" or "PR blocked".
Mocks the REST response instead of hitting the real Load Testing data plane.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent))

from check_run import exit_code_for_result, get_latest_test_run, is_terminal_status


def test_is_terminal_status_true_for_done_failed_cancelled():
    assert is_terminal_status("DONE")
    assert is_terminal_status("FAILED")
    assert is_terminal_status("CANCELLED")


def test_is_terminal_status_false_for_in_progress():
    assert not is_terminal_status("EXECUTING")
    assert not is_terminal_status("PROVISIONING")


def test_exit_code_for_result_passed_is_zero():
    assert exit_code_for_result("PASSED") == 0


def test_exit_code_for_result_failed_is_nonzero():
    assert exit_code_for_result("FAILED") == 1


def test_exit_code_for_result_unknown_is_nonzero():
    # An unrecognized result must fail closed, not silently pass the check.
    assert exit_code_for_result("UNKNOWN") == 1


@patch("check_run.requests.get")
def test_get_latest_test_run_returns_most_recent_by_start_time(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "value": [
            {"testRunId": "older", "startDateTime": "2026-09-16T10:00:00Z", "status": "DONE"},
            {"testRunId": "newest", "startDateTime": "2026-09-17T10:00:00Z", "status": "EXECUTING"},
        ]
    }
    mock_get.return_value = mock_response

    run = get_latest_test_run("fake-data-plane-uri", "test-id", "fake-token")

    assert run["testRunId"] == "newest"


@patch("check_run.requests.get")
def test_get_latest_test_run_raises_when_no_runs_found(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {"value": []}
    mock_get.return_value = mock_response

    try:
        get_latest_test_run("fake-data-plane-uri", "test-id", "fake-token")
        assert False, "expected SystemExit"
    except SystemExit:
        pass
