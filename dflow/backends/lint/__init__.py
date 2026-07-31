from pathlib import Path

from dflow.backends.result import FlowRunResult
from dflow.config import get_flow_tool, load_flow_config

from .verilator import run_verilator_lint


def run_lint(project_root: Path, flow_config: dict | None = None) -> FlowRunResult | None:
	"""Run lint using the tool configured in flow.yaml."""
	config = flow_config if flow_config is not None else load_flow_config(project_root)
	lint_tool = get_flow_tool(config, "lint")

	if not lint_tool:
		print(f"No lint tool is configured in {project_root / 'flow.yaml'}.")
		return None

	if lint_tool == "verilator":
		return run_verilator_lint(project_root, config)

	print(f"Unsupported lint tool '{lint_tool}' configured in {project_root / 'flow.yaml'}.")
	return None