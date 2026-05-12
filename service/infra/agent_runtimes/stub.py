from infra.agent_runtime_resolver import AbstractAgentRuntimeAdapter


class StubAgentRuntime(AbstractAgentRuntimeAdapter):
    def run(self, instructions: str, workspace: str) -> str:
        return "Stub plan output"
