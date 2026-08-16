from __future__ import annotations

import os
import subprocess
from pathlib import Path

from dflow.backends.result import FlowStepResult


def run_flow_command(
    command: list[str],
    project_root: Path,
    step_name: str,
    env: dict[str, str] | None = None,
    stream_output: bool = False,
) -> FlowStepResult:
    """Run a flow command and capture its result for later reporting."""
    command_env = os.environ.copy()
    if env:
        command_env.update(env)

    if stream_output:
        process = subprocess.Popen(
            command,
            cwd=project_root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=command_env,
            bufsize=1,
        )
        output_lines = []
        if process.stdout:
            for line in process.stdout:
                print(line, end="")
                output_lines.append(line)
        return_code = process.wait()
        return FlowStepResult(
            name=step_name,
            command=command,
            returncode=return_code,
            stdout="".join(output_lines),
            output_streamed=True,
        )

    completed_process = subprocess.run(
        command,
        cwd=project_root,
        text=True,
        capture_output=True,
        env=command_env,
    )
    return FlowStepResult(
        name=step_name,
        command=command,
        returncode=completed_process.returncode,
        stdout=completed_process.stdout,
        stderr=completed_process.stderr,
    )
