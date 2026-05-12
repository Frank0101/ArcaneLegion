import subprocess
from unittest.mock import MagicMock, patch

import pytest

from infra.agent_runtimes.claude_code import ClaudeCodeAgentRuntime

_API_KEY = "test-key"


def test_run_raises_when_api_key_is_none() -> None:
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        ClaudeCodeAgentRuntime(None).run("do the thing", "/workspace")


def test_run_invokes_claude_with_prompt_and_workspace() -> None:
    mock_result = MagicMock()
    mock_result.stdout = "plan output"

    with patch("subprocess.run", return_value=mock_result) as mock_run, \
            patch.dict("os.environ", {"PATH": "/usr/bin"}, clear=True):
        result = ClaudeCodeAgentRuntime(_API_KEY).run("do the thing", "/workspace")

    mock_run.assert_called_once_with(
        ["claude", "--print", "do the thing"],
        cwd="/workspace",
        env={"PATH": "/usr/bin", "ANTHROPIC_API_KEY": _API_KEY},
        check=True,
        capture_output=True,
        text=True,
    )
    assert result == "plan output"


def test_run_failure_does_not_expose_api_key() -> None:
    failure = subprocess.CalledProcessError(
        1, [], stderr=f"auth error: {_API_KEY}")
    with patch("subprocess.run", side_effect=failure):
        with pytest.raises(RuntimeError) as exception_info:
            ClaudeCodeAgentRuntime(_API_KEY).run("do the thing", "/workspace")

    error = exception_info.value
    assert "auth error: ***" in str(error)
    assert _API_KEY not in str(error)
    assert error.__cause__ is None
