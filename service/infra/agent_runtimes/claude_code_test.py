import subprocess
from unittest.mock import MagicMock, patch

import pytest

from infra.agent_runtimes.claude_code import ClaudeCodeAgentRuntime


def test_run_invokes_claude_with_prompt_and_workspace() -> None:
    mock_result = MagicMock()
    mock_result.stdout = "plan output"

    with patch("subprocess.run", return_value=mock_result) as mock_run:
        result = ClaudeCodeAgentRuntime().run("do the thing", "/workspace")

    mock_run.assert_called_once_with(
        ["claude", "--print", "do the thing"],
        cwd="/workspace",
        check=True,
        capture_output=True,
        text=True,
    )
    assert result == "plan output"


def test_run_raises_runtime_error_on_failure() -> None:
    error = subprocess.CalledProcessError(1, ["claude"], stderr="something went wrong")

    with patch("subprocess.run", side_effect=error):
        with pytest.raises(RuntimeError, match="claude failed"):
            ClaudeCodeAgentRuntime().run("do the thing", "/workspace")
