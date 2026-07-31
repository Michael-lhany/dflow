from pathlib import Path

from dflow.backends.result import FlowRunResult
from dflow.backends.verilator import run_verilator_rtl_stage

DEFAULT_LINT_OPTIONS = ["--lint-only", "-Wall"]


def run_verilator_lint(project_root: Path, flow_config: dict) -> FlowRunResult | None:
    """Run Verilator lint against the project's RTL sources."""
    return run_verilator_rtl_stage(
        project_root,
        flow_config,
        "lint",
        DEFAULT_LINT_OPTIONS,
        "Verilator lint",
    )
