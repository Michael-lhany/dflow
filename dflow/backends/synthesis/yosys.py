from pathlib import Path

from dflow.backends.executor import run_flow_command
from dflow.backends.result import FlowRunResult
from dflow.config import get_flow_options, get_flow_section
from dflow.core.filesystem import create_directory, remove_path
from dflow.core.project import find_rtl_sources
from dflow.utils import is_tool_available


YOSYS = "yosys"
OUTPUT_DIRECTORY = Path("build/synthesis")


def _quote_yosys_argument(value: str | Path) -> str:
    escaped_value = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped_value}"'


def _build_yosys_script(
    project_root: Path,
    flow_config: dict,
    rtl_sources: list[Path],
) -> str:
    synthesis_config = get_flow_section(flow_config, "synthesis")
    configured_top = synthesis_config.get("top")
    top_module = (
        configured_top
        if isinstance(configured_top, str) and configured_top
        else None
    )

    read_sources = " ".join(
        _quote_yosys_argument(source) for source in rtl_sources
    )
    synth_command = (
        f"synth -top {top_module}"
        if top_module
        else "synth -auto-top"
    )
    output_directory = project_root / OUTPUT_DIRECTORY

    return "; ".join(
        (
            f"read_verilog -sv {read_sources}",
            synth_command,
            "write_verilog -noattr "
            f"{_quote_yosys_argument(output_directory / 'netlist.v')}",
            f"write_json {_quote_yosys_argument(output_directory / 'netlist.json')}",
        )
    )


def run_yosys_synthesis(
    project_root: Path,
    flow_config: dict,
) -> FlowRunResult | None:
    """Synthesize project RTL into generic Verilog and JSON netlists."""
    if not is_tool_available(YOSYS):
        print(f"{YOSYS} is required for synthesis but was not found on PATH.")
        return None

    rtl_sources = find_rtl_sources(project_root)
    if not rtl_sources:
        print(f"No RTL sources were found under {project_root / 'rtl'}.")
        return None

    output_directory = project_root / OUTPUT_DIRECTORY
    remove_path(output_directory, project_root)
    create_directory(output_directory)

    options = get_flow_options(flow_config, "synthesis")
    script = _build_yosys_script(project_root, flow_config, rtl_sources)
    command = [YOSYS, *options, "-p", script]
    step = run_flow_command(command, project_root, "Yosys synthesis")
    return FlowRunResult(tool_name=YOSYS, steps=[step])
