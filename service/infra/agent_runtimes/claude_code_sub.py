import os
import subprocess

from infra.agent_runtime_resolver import AbstractAgentRuntimeAdapter


# Runtime that authenticates via a personal Claude subscription rather than the API.
# For non-production use only — subscription plans have rate limits unsuitable for concurrent workloads.
# Requires CLAUDE_CODE_OAUTH_TOKEN in the environment (obtain via `claude setup-token`).
class ClaudeCodeSubAgentRuntime(AbstractAgentRuntimeAdapter):
    def run(self, instructions: str, workspace: str) -> str:

        # The CLI uses the API when ANTHROPIC_API_KEY is present — we strip it to force subscription auth.
        env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
        try:
            result = subprocess.run(
                ["claude", "--print", "--model", "claude-sonnet-4-6", "--max-turns", "5",
                 "--max-budget-usd", "1.0", "--effort", "medium", instructions],
                cwd=workspace,
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            detail = (e.stderr or e.stdout or "").strip()
            raise RuntimeError(f"claude failed (exit {e.returncode}): {detail}") from None
