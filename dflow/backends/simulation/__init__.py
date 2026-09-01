from pathlib import Path

from dflow.backends.result import FlowRunResult
from dflow.config import get_flow_tool, load_flow_config

from .verilator import run_verilator_simulation
from .vcs import run_vcs_simulation


def run_simulation(project_root: Path, flow_config: dict | None = None) -> FlowRunResult | None:
	"""Run simulation using the tool configured in flow.yaml."""
	config = flow_config if flow_config is not None else load_flow_config(project_root)
	simulation_tool = get_flow_tool(config, "simulation")

	if not simulation_tool:
		print(f"No simulation tool is configured in {project_root / 'flow.yaml'}.")
		return None

	if simulation_tool == "verilator":
		return run_verilator_simulation(project_root, config)
	if simulation_tool == "vcs":
		return run_vcs_simulation(project_root, config)

	print(f"Unsupported simulation tool '{simulation_tool}' configured in {project_root / 'flow.yaml'}.")
	return None
