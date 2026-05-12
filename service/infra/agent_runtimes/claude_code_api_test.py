import subprocess
from unittest.mock import MagicMock, patch

import pytest

from infra.agent_runtimes.claude_code_api import ClaudeCodeApiAgentRuntime

_API_KEY = "test-key"


def test_run_raises_when_api_key_is_none() -> None:
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        ClaudeCodeApiAgentRuntime(None).run("do the thing", "/workspace")


def test_run_invokes_claude_with_prompt_and_workspace() -> None:
    mock_result = MagicMock()
    mock_result.stdout = "plan output"

    with patch("subprocess.run", return_value=mock_result) as mock_run, \
            patch.dict("os.environ", {"PATH": "/usr/bin"}, clear=True):
        result = ClaudeCodeApiAgentRuntime(_API_KEY).run("do the thing", "/workspace")

    mock_run.assert_called_once_with(
        ["claude", "--print", "--model", "claude-sonnet-4-6", "--max-turns", "4",
         "--max-budget-usd", "0.3", "--effort", "low", "do the thing"],
        cwd="/workspace",
        env={"PATH": "/usr/bin", "ANTHROPIC_API_KEY": _API_KEY},
        check=True,
        capture_output=True,
        text=True,
    )
    assert result == "plan output"


@pytest.mark.parametrize("stderr,stdout", [
    ("auth error", ""),
    ("", "auth error"),
])
def test_run_failure_raises_runtime_error(stderr: str, stdout: str) -> None:
    failure = subprocess.CalledProcessError(1, [], output=stdout, stderr=stderr)
    with patch("subprocess.run", side_effect=failure):
        with pytest.raises(RuntimeError, match="claude failed"):
            ClaudeCodeApiAgentRuntime(_API_KEY).run("do the thing", "/workspace")


@pytest.mark.parametrize("stderr,stdout", [
    (f"auth error: {_API_KEY}", ""),
    ("", f"auth error: {_API_KEY}"),
])
def test_run_failure_does_not_expose_api_key(stderr: str, stdout: str) -> None:
    failure = subprocess.CalledProcessError(1, [], output=stdout, stderr=stderr)
    with patch("subprocess.run", side_effect=failure):
        with pytest.raises(RuntimeError) as exception_info:
            ClaudeCodeApiAgentRuntime(_API_KEY).run("do the thing", "/workspace")

    error = exception_info.value
    assert "auth error: ***" in str(error)
    assert _API_KEY not in str(error)
    assert error.__cause__ is None
