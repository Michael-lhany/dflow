from dataclasses import dataclass


@dataclass
class FlowStepResult:
    """Captured result for one command in a flow."""

    name: str
    command: list[str]
    returncode: int
    stdout: str = ""
    stderr: str = ""
    output_streamed: bool = False


@dataclass
class FlowRunResult:
    """Result of a flow made up of one or more command steps."""

    tool_name: str
    steps: list[FlowStepResult]

    @property
    def returncode(self) -> int:
        """Return the final step's code, or failure for an empty flow."""
        return self.steps[-1].returncode if self.steps else 1
