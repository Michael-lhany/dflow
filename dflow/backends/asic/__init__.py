from pathlib import Path

from dflow.backends.result import FlowRunResult
from dflow.config import get_flow_tool, load_flow_config

from .openlane import run_openlane


def run_asic(
    project_root: Path,
    flow_config: dict | None = None,
) -> FlowRunResult | None:
    """Run the configured RTL-to-GDS ASIC flow."""
    config = (
        flow_config
        if flow_config is not None
        else load_flow_config(project_root)
    )
    asic_tool = get_flow_tool(config, "asic")

    if not asic_tool:
        print(f"No ASIC tool is configured in {project_root / 'flow.yaml'}.")
        return None

    if asic_tool == "openlane":
        return run_openlane(project_root, config)

    print(
        f"Unsupported ASIC tool '{asic_tool}' configured in "
        f"{project_root / 'flow.yaml'}."
    )
    return None


__all__ = ["run_asic"]
