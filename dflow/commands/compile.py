import typer

from dflow.backends.compile import run_compile
from dflow.commands.common import run_stage_command


def compile(
    tool_options: list[str] | None = typer.Argument(
        None,
        help="Tool options passed after --.",
    ),
):
    """Compile RTL."""
    run_stage_command(
        "compile",
        run_compile,
        "RTL compile check passed with {tool_name}.",
        tool_options,
    )
