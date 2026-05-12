import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from infra.agent_runtimes.codex_api import CodexApiAgentRuntime

_API_KEY = "test-key"


def test_run_raises_when_api_key_is_none(workspace_base_path: str) -> None:
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        CodexApiAgentRuntime(None, workspace_base_path).run("do the thing", "/workspace")


def test_run_invokes_codex_with_prompt_and_workspace(workspace_base_path: str) -> None:
    captured_auth: dict = {}

    def fake_run(*args, **kwargs):
        codex_home = kwargs["env"]["CODEX_HOME"]
        captured_auth.update(json.loads(Path(codex_home, "auth.json").read_text()))
        result = MagicMock()
        result.stdout = "plan output"
        return result

    with patch("subprocess.run", side_effect=fake_run) as mock_run, \
            patch.dict("os.environ", {"PATH": "/usr/bin"}, clear=True):
        result = CodexApiAgentRuntime(_API_KEY, workspace_base_path).run("do the thing", "/workspace")

    assert captured_auth == {"OPENAI_API_KEY": _API_KEY}
    codex_home = mock_run.call_args.kwargs["env"]["CODEX_HOME"]
    assert codex_home.startswith(workspace_base_path)
    mock_run.assert_called_once_with(
        ["codex", "exec", "--dangerously-bypass-approvals-and-sandbox", "--ephemeral",
         "-m", "gpt-5.4-mini", "--color", "never", "-C", "/workspace", "do the thing"],
        env={"PATH": "/usr/bin", "CODEX_HOME": codex_home},
        check=True,
        capture_output=True,
        text=True,
    )
    assert result == "plan output"


def test_run_creates_codex_home_inside_workspace_base_path(workspace_base_path: str) -> None:
    captured_codex_home: list[str] = []

    def capture_and_succeed(*args, **kwargs):
        captured_codex_home.append(kwargs["env"]["CODEX_HOME"])
        result = MagicMock()
        result.stdout = "plan output"
        return result

    with patch("subprocess.run", side_effect=capture_and_succeed):
        CodexApiAgentRuntime(_API_KEY, workspace_base_path).run("do the thing", "/workspace")

    codex_home = Path(captured_codex_home[0])
    assert codex_home.parent == Path(workspace_base_path)
    assert codex_home.name.startswith("codex_home_")


def test_run_removes_codex_home_after_success(workspace_base_path: str) -> None:
    captured_codex_home: list[str] = []

    def capture_and_succeed(*args, **kwargs):
        captured_codex_home.append(kwargs["env"]["CODEX_HOME"])
        result = MagicMock()
        result.stdout = "plan output"
        return result

    with patch("subprocess.run", side_effect=capture_and_succeed):
        CodexApiAgentRuntime(_API_KEY, workspace_base_path).run("do the thing", "/workspace")

    assert not Path(captured_codex_home[0]).exists()


def test_run_removes_codex_home_on_exception(workspace_base_path: str) -> None:
    captured_codex_home: list[str] = []

    def raise_after_capture(*args, **kwargs):
        captured_codex_home.append(kwargs["env"]["CODEX_HOME"])
        raise subprocess.CalledProcessError(1, [], output="error", stderr="")

    with patch("subprocess.run", side_effect=raise_after_capture):
        with pytest.raises(RuntimeError):
            CodexApiAgentRuntime(_API_KEY, workspace_base_path).run("do the thing", "/workspace")

    assert not Path(captured_codex_home[0]).exists()


@pytest.mark.parametrize("stderr,stdout", [
    ("auth error", ""),
    ("", "auth error"),
])
def test_run_failure_raises_runtime_error(workspace_base_path: str, stderr: str, stdout: str) -> None:
    failure = subprocess.CalledProcessError(1, [], output=stdout, stderr=stderr)
    with patch("subprocess.run", side_effect=failure):
        with pytest.raises(RuntimeError, match="codex failed"):
            CodexApiAgentRuntime(_API_KEY, workspace_base_path).run("do the thing", "/workspace")


@pytest.mark.parametrize("stderr,stdout", [
    (f"auth error: {_API_KEY}", ""),
    ("", f"auth error: {_API_KEY}"),
])
def test_run_failure_does_not_expose_api_key(workspace_base_path: str, stderr: str, stdout: str) -> None:
    failure = subprocess.CalledProcessError(1, [], output=stdout, stderr=stderr)
    with patch("subprocess.run", side_effect=failure):
        with pytest.raises(RuntimeError) as exception_info:
            CodexApiAgentRuntime(_API_KEY, workspace_base_path).run("do the thing", "/workspace")

    error = exception_info.value
    assert "auth error: ***" in str(error)
    assert _API_KEY not in str(error)
    assert error.__cause__ is None
