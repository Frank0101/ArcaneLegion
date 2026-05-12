import os
import subprocess

from infra.agent_runtime_resolver import AbstractAgentRuntimeAdapter


class CodexApiAgentRuntime(AbstractAgentRuntimeAdapter):
    def __init__(self, api_key: str | None) -> None:
        self._api_key = api_key

    def run(self, instructions: str, workspace: str) -> str:
        if self._api_key is None:
            raise ValueError("OPENAI_API_KEY is not configured")
        try:
            result = subprocess.run(
                ["codex", "exec", "--dangerously-bypass-approvals-and-sandbox", "--ephemeral",
                 "-m", "codex-1", "--color", "never", "-C", workspace, instructions],
                env=os.environ | {"OPENAI_API_KEY": self._api_key},
                check=True,
                capture_output=True,
                text=True,
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            detail = (e.stderr or e.stdout or "").strip().replace(self._api_key, "***")
            raise RuntimeError(f"codex failed (exit {e.returncode}): {detail}") from None
