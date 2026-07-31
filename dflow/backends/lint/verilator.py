from __future__ import annotations

from pathlib import Path

from dflow.backends.executor import run_flow_command
from dflow.backends.result import FlowRunResult
from dflow.config import get_flow_options
from dflow.core.project import find_rtl_sources
from dflow.utils import is_tool_available

DEFAULT_LINT_OPTIONS = ["--lint-only", "-Wall"]


def run_verilator_lint(project_root: Path, flow_config: dict) -> FlowRunResult | None:
	"""Run Verilator lint against the project's RTL sources."""
	lint_tool = "verilator"

	if not is_tool_available(lint_tool):
		print(f"{lint_tool} is required for linting but was not found on PATH.")
		return None

	rtl_sources = find_rtl_sources(project_root)

	if not rtl_sources:
		print(f"No RTL sources were found under {project_root / 'rtl'}.")
		return None

	lint_options = get_flow_options(flow_config, "lint", DEFAULT_LINT_OPTIONS)
	command = [lint_tool, *lint_options, *[str(source_path) for source_path in rtl_sources]]
	return run_flow_command(command, project_root, lint_tool)