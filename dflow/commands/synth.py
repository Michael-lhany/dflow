import typer

from dflow.config import get_flow_tool, load_flow_config
from dflow.core.project import find_project_root
from dflow.utils import is_tool_available

app = typer.Typer()


@app.command()
def synth():
	"""Run synthesis."""

	project_root = find_project_root()
	flow_config = load_flow_config(project_root)
	synth_tool = get_flow_tool(flow_config, "synthesis")

	if not synth_tool:
		print(f"No synthesis tool is configured in {project_root / 'flow.yaml'}.")
		raise typer.Exit(code=1)

	if not is_tool_available(synth_tool):
		print(f"{synth_tool} is required for synthesis but was not found on PATH.")
		raise typer.Exit(code=1)

	print(f"Synthesis check passed with {synth_tool}.")