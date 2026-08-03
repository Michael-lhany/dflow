from pathlib import Path

from dflow.backends.result import FlowRunResult
from dflow.backends.verilator import run_verilator_rtl_stage

DEFAULT_COMPILE_OPTIONS = ["--cc"]
COMPILE_OUTPUT_DIRECTORY = Path("sim/compile_obj_dir")


def run_verilator_compile(
    project_root: Path,
    flow_config: dict,
) -> FlowRunResult | None:
    """Run Verilator compilation against the project's RTL sources."""
    return run_verilator_rtl_stage(
        project_root,
        flow_config,
        "compile",
        DEFAULT_COMPILE_OPTIONS,
        "Verilator compile",
        project_root / COMPILE_OUTPUT_DIRECTORY,
    )
