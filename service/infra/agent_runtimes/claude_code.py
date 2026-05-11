import subprocess

from infra.agent_runtime_resolver import AbstractAgentRuntimeAdapter


class ClaudeCodeAgentRuntime(AbstractAgentRuntimeAdapter):
    def run(self, prompt: str, workspace: str) -> str:
        try:
            result = subprocess.run(
                ["claude", "--print", prompt],
                cwd=workspace,
                check=True,
                capture_output=True,
                text=True,
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"claude failed (exit {e.returncode}): {(e.stderr or '').strip()}"
            ) from None
