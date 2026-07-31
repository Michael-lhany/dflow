from __future__ import annotations

import os
import subprocess
from pathlib import Path

from dflow.backends.result import FlowRunResult


def run_flow_command(
	command: list[str],
	project_root: Path,
	tool_name: str,
	env: dict[str, str] | None = None,
) -> FlowRunResult:
	"""Run a flow command and capture its result for later reporting."""
	command_env = os.environ.copy()
	if env:
		command_env.update(env)

	completed_process = subprocess.run(
		command,
		cwd=project_root,
		text=True,
		capture_output=True,
		env=command_env,
	)
	return FlowRunResult(
		tool_name=tool_name,
		command=command,
		returncode=completed_process.returncode,
		stdout=completed_process.stdout,
		stderr=completed_process.stderr,
	)