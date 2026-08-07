import sys
from collections.abc import Callable
from pathlib import Path

import typer

from dflow.backends.result import FlowRunResult, FlowStepResult
from dflow.config import load_flow_config
from dflow.core.project import find_project_root, save_flow_report


BackendRunner = Callable[[Path, dict], FlowRunResult | None]
SuccessAction = Callable[[Path], bool]


def _print_step_output(step: FlowStepResult, show_heading: bool) -> None:
    if step.stdout:
        if show_heading:
            print(f"=== {step.name} output ===")
        print(step.stdout, end="" if step.stdout.endswith("\n") else "\n")

    if step.stderr:
        if show_heading:
            print(f"=== {step.name} errors ===", file=sys.stderr)
        print(
            step.stderr,
            end="" if step.stderr.endswith("\n") else "\n",
            file=sys.stderr,
        )


def run_stage_command(
    stage_name: str,
    backend_runner: BackendRunner,
    success_message: str,
    tool_options: list[str] | None = None,
    success_action: SuccessAction | None = None,
    timestamp_report: bool = False,
) -> None:
    """Run a configured backend and handle its common CLI lifecycle."""
    project_root = find_project_root()
    flow_config = load_flow_config(project_root)
    if tool_options:
        section_config = dict(flow_config.get(stage_name) or {})
        section_config["_cli_options"] = tool_options
        flow_config = {**flow_config, stage_name: section_config}

    result = backend_runner(project_root, flow_config)

    if result is None:
        raise typer.Exit(code=1)

    save_flow_report(
        project_root,
        stage_name,
        result.tool_name,
        result.steps,
        timestamped=timestamp_report,
    )

    show_headings = len(result.steps) > 1
    for step in result.steps:
        _print_step_output(step, show_headings)

    if result.returncode == 0:
        print(success_message.format(tool_name=result.tool_name))
        if success_action is not None and not success_action(project_root):
            raise typer.Exit(code=1)

    raise typer.Exit(code=result.returncode)
