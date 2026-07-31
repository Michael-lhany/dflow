from pathlib import Path

from dflow.backends.result import FlowRunResult
from dflow.config import get_flow_tool, load_flow_config

from .verilator import run_verilator_compile


def run_compile(project_root: Path, flow_config: dict | None = None) -> FlowRunResult | None:
	"""Run compile using the tool configured in flow.yaml."""
	config = flow_config if flow_config is not None else load_flow_config(project_root)
	compile_tool = get_flow_tool(config, "compile")

	if not compile_tool:
		print(f"No compile tool is configured in {project_root / 'flow.yaml'}.")
		return None

	if compile_tool == "verilator":
		return run_verilator_compile(project_root, config)

	print(f"Unsupported compile tool '{compile_tool}' configured in {project_root / 'flow.yaml'}.")
	return None