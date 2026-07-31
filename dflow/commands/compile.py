from dflow.backends.compile import run_compile
from dflow.commands.common import run_stage_command


def compile():
    """Compile RTL."""
    run_stage_command(
        "compile",
        run_compile,
        "RTL compile check passed with {tool_name}.",
    )
