import typer

from dflow.backends.lint import run_lint
from dflow.commands.common import run_stage_command


def lint(
    tool_options: list[str] | None = typer.Argument(
        None,
        help="Tool options passed after --.",
    ),
):
    """Run lint."""
    run_stage_command(
        "lint",
        run_lint,
        "Lint check passed with {tool_name}.",
        tool_options,
    )
