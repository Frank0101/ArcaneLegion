from infra.agent_runtime_resolver import AbstractAgentRuntimeAdapter


class StubAgentRuntime(AbstractAgentRuntimeAdapter):
    def run(self, prompt: str, workspace: str) -> str:
        return "Stub plan output"
