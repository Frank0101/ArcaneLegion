import os
import subprocess

from infra.agent_runtime_resolver import AbstractAgentRuntimeAdapter


# Development-only runtime that authenticates via a personal Claude subscription rather than the API.
# Not intended for production use — subscription plans have rate limits unsuitable for concurrent workloads.
#
# Prerequisites:
#   1. Install the Claude CLI: https://claude.ai/download
#   2. Log in with your subscription: `claude auth login`
#      Credentials are stored in the macOS Keychain and picked up automatically at runtime.
#      Because the Keychain is not accessible inside Docker, this runtime only works when the
#      service is run locally via dev-start.sh.
class ClaudeCodeSubAgentRuntime(AbstractAgentRuntimeAdapter):
    def run(self, instructions: str, workspace: str) -> str:

        # The CLI chooses between API and subscription based solely on the presence of ANTHROPIC_API_KEY.
        # Stripping it ensures the subscription credentials (stored in the system keychain) are always used.
        env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
        try:
            result = subprocess.run(
                ["claude", "--print", "--model", "claude-sonnet-4-6", "--max-turns", "5", instructions],
                cwd=workspace,
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"claude failed (exit {e.returncode}): {e.stderr.strip()}") from None
