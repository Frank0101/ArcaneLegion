import json
import os
import subprocess
import tempfile
from pathlib import Path

from infra.agent_runtime_resolver import AbstractAgentRuntimeAdapter


class CodexApiAgentRuntime(AbstractAgentRuntimeAdapter):
    def __init__(self, api_key: str | None, workspace_base_path: str) -> None:
        self._api_key = api_key
        self._workspace_base_path = workspace_base_path

    def run(self, instructions: str, workspace: str) -> str:
        if self._api_key is None:
            raise ValueError("OPENAI_API_KEY is not configured")

        # Codex CLI reads credentials from an auth.json file in
        # CODEX_HOME, not from CLI arguments or environment variables.
        with tempfile.TemporaryDirectory(prefix="codex_home_", dir=self._workspace_base_path) as codex_home:
            auth_path = Path(codex_home, "auth.json")
            auth_path.write_text(json.dumps({"OPENAI_API_KEY": self._api_key}), encoding="utf-8")
            auth_path.chmod(0o600)

            try:
                result = subprocess.run(
                    ["codex", "exec", "--dangerously-bypass-approvals-and-sandbox", "--ephemeral",
                     "-m", "gpt-5.4-mini", "--color", "never", "-C", workspace, instructions],
                    env=os.environ | {"CODEX_HOME": codex_home},
                    check=True,
                    capture_output=True,
                    text=True,
                )
                return result.stdout
            except subprocess.CalledProcessError as e:
                detail = (e.stderr or e.stdout or "").strip().replace(self._api_key, "***")
                raise RuntimeError(f"codex failed (exit {e.returncode}): {detail}") from None
