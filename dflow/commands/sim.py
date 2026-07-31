import typer
import sys

from dflow.backends.simulation import run_simulation
from dflow.config import load_flow_config
from dflow.core.project import find_project_root
from dflow.core.project import save_sim_report

app = typer.Typer()


@app.command()
def sim():
    """Run simulation."""

    project_root = find_project_root()
    flow_config = load_flow_config(project_root)
    result = run_simulation(project_root, flow_config)

    if result is None:
        raise typer.Exit(code=1)

    save_sim_report(
        project_root,
        result.tool_name,
        result.command,
        result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )

    if result.stdout:
        print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")

    if result.stderr:
        print(result.stderr, end="" if result.stderr.endswith("\n") else "\n", file=sys.stderr)

    if result.returncode == 0:
        print(f"Simulation passed with {result.tool_name}.")

    raise typer.Exit(code=result.returncode)
