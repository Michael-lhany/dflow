import os
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


def _resolve_liberty_file(
    project_root: Path,
    flow_config: dict,
) -> Path | None:
    synthesis_config = get_flow_section(flow_config, "synthesis")
    configured_liberty = synthesis_config.get("liberty")
    if configured_liberty is None:
        return None
    if not isinstance(configured_liberty, str) or not configured_liberty.strip():
        raise ValueError("synthesis.liberty must be a non-empty path.")

    expanded_path = os.path.expanduser(os.path.expandvars(configured_liberty))
    liberty_file = Path(expanded_path)
    if not liberty_file.is_absolute():
        liberty_file = project_root / liberty_file
    liberty_file = liberty_file.resolve()

    if not liberty_file.is_file():
        raise ValueError(f"Liberty file was not found: {liberty_file}")
    return liberty_file


def _build_yosys_script(
    project_root: Path,
    flow_config: dict,
    rtl_sources: list[Path],
    liberty_file: Path | None,
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
    synth_target = (
        f"synth -top {top_module}"
        if top_module
        else "synth -auto-top"
    )
    synth_command = f"{synth_target} -noabc" if liberty_file else synth_target
    output_directory = project_root / OUTPUT_DIRECTORY

    commands = []
    if liberty_file:
        quoted_liberty = _quote_yosys_argument(liberty_file)
        commands.append(f"read_liberty -lib {quoted_liberty}")

    commands.extend((f"read_verilog -sv {read_sources}", synth_command))
    if liberty_file:
        commands.extend(
            (
                f"dfflibmap -liberty {quoted_liberty}",
                f"abc -liberty {quoted_liberty}",
                "clean",
                f"stat -liberty {quoted_liberty}",
            )
        )

    commands.extend(
        (
            "write_verilog -noattr "
            f"{_quote_yosys_argument(output_directory / 'netlist.v')}",
            f"write_json {_quote_yosys_argument(output_directory / 'netlist.json')}",
        )
    )
    return "; ".join(commands)


def run_yosys_synthesis(
    project_root: Path,
    flow_config: dict,
) -> FlowRunResult | None:
    """Synthesize project RTL into Verilog and JSON netlists."""
    if not is_tool_available(YOSYS):
        print(f"{YOSYS} is required for synthesis but was not found on PATH.")
        return None

    rtl_sources = find_rtl_sources(project_root)
    if not rtl_sources:
        print(f"No RTL sources were found under {project_root / 'rtl'}.")
        return None

    try:
        liberty_file = _resolve_liberty_file(project_root, flow_config)
    except ValueError as error:
        print(error)
        return None

    output_directory = project_root / OUTPUT_DIRECTORY
    remove_path(output_directory, project_root)
    create_directory(output_directory)

    options = get_flow_options(flow_config, "synthesis")
    script = _build_yosys_script(
        project_root,
        flow_config,
        rtl_sources,
        liberty_file,
    )
    command = [YOSYS, *options, "-p", script]
    step = run_flow_command(command, project_root, "Yosys synthesis")
    return FlowRunResult(tool_name=YOSYS, steps=[step])
