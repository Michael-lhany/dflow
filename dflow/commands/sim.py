from dflow.backends.simulation import run_simulation
from dflow.commands.common import run_stage_command


def sim():
    """Run simulation."""
    run_stage_command(
        "sim",
        run_simulation,
        "Simulation passed with {tool_name}.",
    )
