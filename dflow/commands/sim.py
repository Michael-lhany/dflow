import time
from pathlib import Path

import typer

from dflow.backends.simulation import run_simulation
from dflow.backends.waveform import open_latest_waveform
from dflow.commands.common import run_stage_command
from dflow.core.project import find_project_root


def sim(
    wave: bool = typer.Option(
        False,
        "--wave",
        "-w",
        help="Open the newest generated VCD in GTKWave after simulation.",
    ),
    wave_only: bool = typer.Option(
        False,
        "--wave-only",
        help="Open the newest existing VCD in GTKWave without simulating.",
    ),
    tool_options: list[str] | None = typer.Argument(
        None,
        help="Tool options passed after --.",
    ),
):
    """Run simulation."""
    if wave_only:
        opened = open_latest_waveform(find_project_root())
        raise typer.Exit(code=0 if opened else 1)

    simulation_started_ns = time.time_ns()

    def open_generated_waveform(project_root: Path) -> bool:
        return open_latest_waveform(project_root, modified_since_ns=simulation_started_ns)

    run_stage_command(
        "sim",
        run_simulation,
        "Simulation passed with {tool_name}.",
        tool_options,
        success_action=open_generated_waveform if wave else None,
        timestamp_report=True,
    )
