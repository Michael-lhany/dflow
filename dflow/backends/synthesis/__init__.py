from pathlib import Path

from dflow.backends.result import FlowRunResult
from dflow.config import get_flow_tool, load_flow_config

from .yosys import run_yosys_synthesis


def run_synthesis(
    project_root: Path,
    flow_config: dict | None = None,
) -> FlowRunResult | None:
    """Run synthesis using the tool configured in flow.yaml."""
    config = (
        flow_config
        if flow_config is not None
        else load_flow_config(project_root)
    )
    synthesis_tool = get_flow_tool(config, "synthesis")

    if not synthesis_tool:
        print(
            f"No synthesis tool is configured in "
            f"{project_root / 'flow.yaml'}."
        )
        return None

    if synthesis_tool == "yosys":
        return run_yosys_synthesis(project_root, config)

    print(
        f"Unsupported synthesis tool '{synthesis_tool}' configured in "
        f"{project_root / 'flow.yaml'}."
    )
    return None
