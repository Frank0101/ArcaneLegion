import os
import subprocess

from infra.agent_runtime_resolver import AbstractAgentRuntimeAdapter


class ClaudeCodeApiAgentRuntime(AbstractAgentRuntimeAdapter):
    def __init__(self, api_key: str | None) -> None:
        self._api_key = api_key

    def run(self, prompt: str, workspace: str) -> str:
        if self._api_key is None:
            raise ValueError("ANTHROPIC_API_KEY is not configured")
        try:
            result = subprocess.run(
                ["claude", "--print", "--model", "claude-sonnet-4-6", "--max-turns", "15", prompt],
                cwd=workspace,
                env=os.environ | {"ANTHROPIC_API_KEY": self._api_key},
                check=True,
                capture_output=True,
                text=True,
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            stderr = (
                (e.stderr or "")
                .strip()
                .replace(self._api_key, "***")
            )
            raise RuntimeError(f"claude failed (exit {e.returncode}): {stderr}") from None
