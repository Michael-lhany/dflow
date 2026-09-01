from pathlib import Path

from dflow.backends.result import FlowRunResult
from dflow.backends.vcs import run_vcs_rtl_compile


def run_vcs_compile(
    project_root: Path,
    flow_config: dict,
) -> FlowRunResult | None:
    """Run VCS compilation against the project's RTL sources."""
    return run_vcs_rtl_compile(project_root, flow_config)
