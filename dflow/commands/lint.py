from dflow.backends.lint import run_lint
from dflow.commands.common import run_stage_command


def lint():
    """Run lint."""
    run_stage_command(
        "lint",
        run_lint,
        "Lint check passed with {tool_name}.",
    )
