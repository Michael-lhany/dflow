import typer

from dflow.backends.synthesis import run_synthesis
from dflow.commands.common import run_stage_command


def synth(
    tool_options: list[str] | None = typer.Argument(
        None,
        help="Tool options passed after --.",
    ),
) -> None:
    """Synthesize RTL."""
    run_stage_command(
        "synthesis",
        run_synthesis,
        "Synthesis passed with {tool_name}.",
        tool_options,
    )
