from pathlib import Path

from dflow.backends.executor import run_flow_command
from dflow.backends.result import FlowRunResult, FlowStepResult
from dflow.backends.vcs import (
    DEFAULT_VCS_OPTIONS,
    VCS,
    build_vcs_command,
    prepare_vcs_output,
    resolve_top_module,
)
from dflow.config import get_flow_section
from dflow.core.filesystem import create_directory
from dflow.core.project import find_rtl_sources, find_tb_sources
from dflow.utils import is_tool_available


DEFAULT_SIM_OPTIONS = [
    *DEFAULT_VCS_OPTIONS,
    "-timescale=1ns/1ps",
    "-debug_access+all",
    "-kdb",
]


def _runtime_options(flow_config: dict) -> list[str]:
    configured = get_flow_section(flow_config, "simulation").get("runtime_options")
    if isinstance(configured, list):
        return [option for option in configured if isinstance(option, str) and option]
    return []


def run_vcs_simulation(
    project_root: Path,
    flow_config: dict,
) -> FlowRunResult | None:
    """Compile, elaborate, and run a VCS simulation."""
    if not is_tool_available(VCS):
        print("vcs is required for simulation but was not found on PATH.")
        return None

    rtl_sources = find_rtl_sources(project_root)
    tb_sources = find_tb_sources(project_root)
    if not rtl_sources:
        print(f"No RTL sources were found under {project_root / 'rtl'}.")
        return None
    if not tb_sources:
        print(f"No testbench sources were found under {project_root / 'tb'}.")
        return None

    top_module = resolve_top_module(flow_config, "simulation")
    if top_module is None:
        if len(tb_sources) == 1:
            top_module = tb_sources[0].stem
        else:
            print(
                "No simulation top module is configured in "
                f"{project_root / 'flow.yaml'}."
            )
            return None

    output_directory = project_root / "sim" / "vcs"
    simulation_binary = prepare_vcs_output(project_root, output_directory)
    wave_directory = project_root / "sim" / "waves"
    create_directory(wave_directory)

    compile_command = build_vcs_command(
        flow_config,
        "simulation",
        output_directory,
        simulation_binary,
        [*rtl_sources, *tb_sources],
        DEFAULT_SIM_OPTIONS,
        top_module,
    )
    steps = [run_flow_command(compile_command, project_root, "VCS build")]
    if steps[-1].returncode != 0:
        return FlowRunResult(tool_name=VCS, steps=steps)

    if not simulation_binary.exists():
        steps.append(
            FlowStepResult(
                name="Simulation binary check",
                command=[],
                returncode=1,
                stderr=(
                    "Expected simulation binary was not found at "
                    f"{simulation_binary}."
                ),
            )
        )
        return FlowRunResult(tool_name=VCS, steps=steps)

    run_command = [str(simulation_binary), *_runtime_options(flow_config)]
    steps.append(run_flow_command(run_command, project_root, "Simulation"))
    return FlowRunResult(tool_name=VCS, steps=steps)
