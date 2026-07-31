from __future__ import annotations

from pathlib import Path

from dflow.backends.executor import run_flow_command
from dflow.config import get_flow_options
from dflow.core.project import find_rtl_sources
from dflow.backends.result import FlowRunResult
from dflow.utils import is_tool_available

DEFAULT_COMPILE_OPTIONS = ["--cc"]


def run_verilator_compile(project_root: Path, flow_config: dict) -> FlowRunResult | None:
	"""Run Verilator compilation against the project's RTL sources."""
	compile_tool = "verilator"

	if not is_tool_available(compile_tool):
		print(f"{compile_tool} is required for RTL compilation but was not found on PATH.")
		return None

	rtl_sources = find_rtl_sources(project_root)

	if not rtl_sources:
		print(f"No RTL sources were found under {project_root / 'rtl'}.")
		return None

	compile_options = get_flow_options(flow_config, "compile", DEFAULT_COMPILE_OPTIONS)
	command = [compile_tool, *compile_options, *[str(source_path) for source_path in rtl_sources]]
	return run_flow_command(command, project_root, compile_tool)