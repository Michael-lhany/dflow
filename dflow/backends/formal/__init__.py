from pathlib import Path

from dflow.backends.result import FlowRunResult
from dflow.config import get_flow_tool, load_flow_config

from .symbiyosys import run_symbiyosys


def run_formal(
    project_root: Path,
    flow_config: dict | None = None,
) -> FlowRunResult | None:
    """Run formal verification using the tool configured in flow.yaml."""
    config = (
        flow_config
        if flow_config is not None
        else load_flow_config(project_root)
    )
    formal_tool = get_flow_tool(config, "formal")

    if not formal_tool:
        print(f"No formal tool is configured in {project_root / 'flow.yaml'}.")
        return None

    if formal_tool in {"sby", "symbiyosys"}:
        return run_symbiyosys(project_root, config)

    print(
        f"Unsupported formal tool '{formal_tool}' configured in "
        f"{project_root / 'flow.yaml'}."
    )
    return None


__all__ = ["run_formal"]
