"""Deterministic local placeholder for the optional supervisory query interface."""
from .base import PHIGuard


class MockLLM:
    def __init__(self, system_name: str = "Specimen Rejection Analyzer"):
        self.system_name = system_name

    def invoke(self, prompt: str) -> str:
        PHIGuard.assert_no_phi(prompt)
        return (
            f"[{self.system_name} local mock]: No model inference or clinical "
            "verification is performed. Use the rule-based audit or consult "
            "your laboratory's validated procedures."
        )


class LLMFactory:
    """Only the local deterministic mock is implemented."""

    @staticmethod
    def create(provider: str = "mock", system_name: str = "Specimen Rejection Analyzer"):
        prov = str(provider).lower()
        if prov in ("mock", "deterministic", "test"):
            return MockLLM(system_name)
        raise ValueError(
            f"Provider '{provider}' is not implemented. Only the local mock is supported."
        )
