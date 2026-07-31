from dataclasses import dataclass


@dataclass(frozen=True)
class FlowRunResult:
	"""Result of running a flow tool."""

	tool_name: str
	command: list[str]
	returncode: int
	stdout: str = ""
	stderr: str = ""