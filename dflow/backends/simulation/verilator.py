import shutil
from pathlib import Path

from dflow.backends.executor import run_flow_command
from dflow.backends.result import FlowRunResult, FlowStepResult
from dflow.config import get_flow_options, get_flow_section
from dflow.core.filesystem import create_directory
from dflow.core.project import find_rtl_sources, find_tb_sources
from dflow.utils import is_tool_available


VERILATOR = "verilator"
MAKE = "make"
DEFAULT_SIM_OPTIONS = [
    "--cc",
    "--exe",
    "--main",
    "--trace",
    "--timing",
]
MAKE_TOOLCHAIN_ARGUMENTS = [
    "CXX=clang++",
    "LINK=clang++",
    "CXXFLAGS=-std=c++20 -stdlib=libc++ -I/usr/lib/llvm-18/include/c++/v1",
    "LDFLAGS=-stdlib=libc++ -L/usr/lib/llvm-18/lib",
]


def _resolve_top_module(
    project_root: Path,
    flow_config: dict,
    tb_sources: list[Path],
) -> str | None:
    simulation_section = get_flow_section(flow_config, "simulation")
    configured_top = simulation_section.get("top")
    if isinstance(configured_top, str) and configured_top:
        return configured_top

    if len(tb_sources) == 1:
        return tb_sources[0].stem

    print(f"No simulation top module is configured in {project_root / 'flow.yaml'}.")
    return None


def _prepare_object_directory(project_root: Path) -> Path:
    object_directory = project_root / "sim" / "obj_dir"
    if object_directory.exists():
        shutil.rmtree(object_directory)

    create_directory(project_root / "sim" / "waves")
    create_directory(object_directory)
    return object_directory


def _build_verilator_command(
    flow_config: dict,
    top_module: str,
    object_directory: Path,
    rtl_sources: list[Path],
    tb_sources: list[Path],
) -> list[str]:
    options = get_flow_options(flow_config, "simulation", DEFAULT_SIM_OPTIONS)
    return [
        VERILATOR,
        *options,
        "--Mdir",
        str(object_directory),
        "--top-module",
        top_module,
        *map(str, rtl_sources),
        *map(str, tb_sources),
    ]


def _build_make_command(object_directory: Path, top_module: str) -> list[str]:
    return [
        MAKE,
        "-C",
        str(object_directory),
        "-f",
        f"V{top_module}.mk",
        *MAKE_TOOLCHAIN_ARGUMENTS,
    ]


def _flow_result(steps: list[FlowStepResult]) -> FlowRunResult:
    return FlowRunResult(tool_name=VERILATOR, steps=steps)


def run_verilator_simulation(
    project_root: Path,
    flow_config: dict,
) -> FlowRunResult | None:
    """Build and run a Verilator simulation."""
    if not is_tool_available(VERILATOR):
        print(f"{VERILATOR} is required for simulation but was not found on PATH.")
        return None

    rtl_sources = find_rtl_sources(project_root)
    tb_sources = find_tb_sources(project_root)
    if not rtl_sources:
        print(f"No RTL sources were found under {project_root / 'rtl'}.")
        return None
    if not tb_sources:
        print(f"No testbench sources were found under {project_root / 'tb'}.")
        return None

    top_module = _resolve_top_module(project_root, flow_config, tb_sources)
    if top_module is None:
        return None

    object_directory = _prepare_object_directory(project_root)
    build_command = _build_verilator_command(
        flow_config,
        top_module,
        object_directory,
        rtl_sources,
        tb_sources,
    )

    steps = [
        run_flow_command(build_command, project_root, "Verilator build"),
    ]
    if steps[-1].returncode != 0:
        return _flow_result(steps)

    make_command = _build_make_command(object_directory, top_module)
    steps.append(run_flow_command(make_command, project_root, "Make build"))
    if steps[-1].returncode != 0:
        return _flow_result(steps)

    simulation_binary = object_directory / f"V{top_module}"
    if not simulation_binary.exists():
        steps.append(
            FlowStepResult(
                name="Simulation binary check",
                command=[],
                returncode=1,
                stderr=f"Expected simulation binary was not found at {simulation_binary}.",
            )
        )
        return _flow_result(steps)

    steps.append(
        run_flow_command(
            [str(simulation_binary)],
            project_root,
            "Simulation",
        )
    )
    return _flow_result(steps)
