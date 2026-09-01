from pathlib import Path

from dflow.backends.executor import run_flow_command
from dflow.backends.result import FlowRunResult
from dflow.config import get_flow_options, get_flow_section
from dflow.core.filesystem import create_directory, remove_path
from dflow.core.project import find_rtl_sources
from dflow.utils import is_tool_available


VCS = "vcs"
DEFAULT_VCS_OPTIONS = ["-full64", "-sverilog"]


def resolve_top_module(flow_config: dict, section_name: str) -> str | None:
    """Return a non-empty top module configured for a flow stage."""
    configured_top = get_flow_section(flow_config, section_name).get("top")
    if isinstance(configured_top, str) and configured_top:
        return configured_top
    return None


def build_vcs_command(
    flow_config: dict,
    section_name: str,
    output_directory: Path,
    simulation_binary: Path,
    sources: list[Path],
    default_options: list[str] | None = None,
    top_module: str | None = None,
) -> list[str]:
    """Build a VCS compile/elaboration command."""
    options = get_flow_options(
        flow_config,
        section_name,
        default_options or DEFAULT_VCS_OPTIONS,
    )
    command = [
        VCS,
        *options,
        f"-Mdir={output_directory / 'csrc'}",
        "-o",
        str(simulation_binary),
        *map(str, sources),
    ]
    if top_module:
        command.extend(["-top", top_module])
    return command


def prepare_vcs_output(project_root: Path, output_directory: Path) -> Path:
    """Reset a VCS work directory and return its simulation binary path."""
    remove_path(output_directory, project_root)
    create_directory(output_directory)
    return output_directory / "simv"


def run_vcs_rtl_compile(
    project_root: Path,
    flow_config: dict,
) -> FlowRunResult | None:
    """Compile and elaborate project RTL with VCS."""
    if not is_tool_available(VCS):
        print("vcs is required for compile but was not found on PATH.")
        return None

    rtl_sources = find_rtl_sources(project_root)
    if not rtl_sources:
        print(f"No RTL sources were found under {project_root / 'rtl'}.")
        return None

    output_directory = project_root / "sim" / "vcs_compile"
    simulation_binary = prepare_vcs_output(project_root, output_directory)
    command = build_vcs_command(
        flow_config,
        "compile",
        output_directory,
        simulation_binary,
        rtl_sources,
        top_module=resolve_top_module(flow_config, "compile"),
    )
    step = run_flow_command(command, project_root, "VCS compile")
    return FlowRunResult(tool_name=VCS, steps=[step])
