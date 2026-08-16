import typer

from dflow.backends.asic import run_asic
from dflow.commands.common import run_stage_command


def asic(
    tool_options: list[str] | None = typer.Argument(
        None,
        help="OpenLane options passed after --.",
    ),
) -> None:
    """Run the configured RTL-to-GDS ASIC flow."""
    run_stage_command(
        "asic",
        run_asic,
        "ASIC flow passed with {tool_name}.",
        tool_options,
        timestamp_report=True,
    )
