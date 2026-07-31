from pathlib import Path

from dflow.backends.executor import run_flow_command
from dflow.backends.result import FlowRunResult
from dflow.config import get_flow_options
from dflow.core.project import find_rtl_sources
from dflow.utils import is_tool_available


VERILATOR = "verilator"


def run_verilator_rtl_stage(
    project_root: Path,
    flow_config: dict,
    section_name: str,
    default_options: list[str],
    step_name: str,
) -> FlowRunResult | None:
    """Run a single-step Verilator flow against project RTL sources."""
    if not is_tool_available(VERILATOR):
        print(
            f"{VERILATOR} is required for {section_name} "
            "but was not found on PATH."
        )
        return None

    rtl_sources = find_rtl_sources(project_root)
    if not rtl_sources:
        print(f"No RTL sources were found under {project_root / 'rtl'}.")
        return None

    options = get_flow_options(flow_config, section_name, default_options)
    command = [VERILATOR, *options, *map(str, rtl_sources)]
    step = run_flow_command(command, project_root, step_name)
    return FlowRunResult(tool_name=VERILATOR, steps=[step])
