from __future__ import annotations

import subprocess
from pathlib import Path

from dflow.backends.result import FlowRunResult


def run_flow_command(command: list[str], project_root: Path, tool_name: str) -> FlowRunResult:
	"""Run a flow command and capture its result for later reporting."""
	completed_process = subprocess.run(
		command,
		cwd=project_root,
		text=True,
		capture_output=True,
	)
	return FlowRunResult(
		tool_name=tool_name,
		command=command,
		returncode=completed_process.returncode,
		stdout=completed_process.stdout,
		stderr=completed_process.stderr,
	)