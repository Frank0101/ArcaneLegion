import subprocess
from unittest.mock import MagicMock, patch

import pytest

from infra.agent_runtimes.claude_code_sub import ClaudeCodeSubAgentRuntime


def test_run_invokes_claude_with_prompt_and_workspace() -> None:
    mock_result = MagicMock()
    mock_result.stdout = "plan output"

    with patch("subprocess.run", return_value=mock_result) as mock_run, \
            patch.dict("os.environ", {"PATH": "/usr/bin"}, clear=True):
        result = ClaudeCodeSubAgentRuntime().run("do the thing", "/workspace")

    mock_run.assert_called_once_with(
        ["claude", "--print", "--model", "claude-sonnet-4-6", "--max-turns", "15", "do the thing"],
        cwd="/workspace",
        env={"PATH": "/usr/bin"},
        check=True,
        capture_output=True,
        text=True,
    )
    assert result == "plan output"


def test_run_strips_api_key_from_environment() -> None:
    mock_result = MagicMock()
    mock_result.stdout = "plan output"

    with patch("subprocess.run", return_value=mock_result) as mock_run, \
            patch.dict("os.environ", {"PATH": "/usr/bin", "ANTHROPIC_API_KEY": "secret"}, clear=True):
        ClaudeCodeSubAgentRuntime().run("do the thing", "/workspace")

    env_passed = mock_run.call_args.kwargs["env"]
    assert "ANTHROPIC_API_KEY" not in env_passed


def test_run_failure_raises_runtime_error() -> None:
    failure = subprocess.CalledProcessError(1, [], stderr="auth error")
    with patch("subprocess.run", side_effect=failure):
        with pytest.raises(RuntimeError, match="claude failed"):
            ClaudeCodeSubAgentRuntime().run("do the thing", "/workspace")
