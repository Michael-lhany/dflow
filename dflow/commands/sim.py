import typer

from dflow.backends.simulation import run_simulation
from dflow.commands.common import run_stage_command


def sim(
    tool_options: list[str] | None = typer.Argument(
        None,
        help="Tool options passed after --.",
    ),
):
    """Run simulation."""
    run_stage_command(
        "sim",
        run_simulation,
        "Simulation passed with {tool_name}.",
        tool_options,
    )
