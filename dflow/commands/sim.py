import typer

from dflow.config import get_flow_tool, load_flow_config
from dflow.core.project import find_project_root
from dflow.utils import is_tool_available

app = typer.Typer()


@app.command()
def sim():
    """Run simulation."""

    project_root = find_project_root()
    flow_config = load_flow_config(project_root)
    sim_tool = get_flow_tool(flow_config, "simulation")

    if not sim_tool:
        print(f"No simulation tool is configured in {project_root / 'flow.yaml'}.")
        raise typer.Exit(code=1)

    if not is_tool_available(sim_tool):
        print(f"{sim_tool} is required for simulation but was not found on PATH.")
        raise typer.Exit(code=1)

    print(f"Simulation check passed with {sim_tool}.")
