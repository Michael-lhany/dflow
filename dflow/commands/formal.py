import typer

from dflow.backends.formal import run_formal
from dflow.commands.common import run_stage_command


def formal(
    task: list[str] | None = typer.Option(
        None,
        "--task",
        "-t",
        help="Run only this SBY task; repeat to select multiple tasks.",
    ),
    config: str | None = typer.Option(
        None,
        "--config",
        "-c",
        help="Temporarily override the .sby configuration path.",
    ),
    tool_options: list[str] | None = typer.Argument(
        None,
        help="SymbiYosys options passed after --.",
    ),
) -> None:
    """Run the configured formal verification flow."""
    overrides: dict = {}
    if task:
        overrides["tasks"] = task
    if config:
        overrides["config"] = config

    run_stage_command(
        "formal",
        run_formal,
        "Formal verification passed with {tool_name}.",
        tool_options,
        timestamp_report=True,
        section_overrides=overrides,
    )
