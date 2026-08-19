import typer

from dflow.backends.asic.openlane import is_openlane_runtime_available
from dflow.backends.formal.symbiyosys import is_symbiyosys_runtime_available
from dflow.config import get_flow_tool, load_flow_config
from dflow.core.project import find_project_root
from dflow.utils import is_tool_available


def doctor():
    """Check whether required flow tools are installed."""

    project_root = find_project_root()
    flow_config = load_flow_config(project_root)
    configured_tools = [
        get_flow_tool(flow_config, "compile"),
        get_flow_tool(flow_config, "lint"),
        get_flow_tool(flow_config, "simulation"),
        get_flow_tool(flow_config, "synthesis"),
        get_flow_tool(flow_config, "asic"),
        get_flow_tool(flow_config, "formal"),
    ]
    required_tools = list(dict.fromkeys(
        tool_name for tool_name in configured_tools if tool_name
    ))
    availability = {}
    for tool_name in required_tools:
        if tool_name == "openlane":
            availability[tool_name] = is_openlane_runtime_available(
                project_root,
                flow_config,
            )
        elif tool_name in {"sby", "symbiyosys"}:
            availability[tool_name] = is_symbiyosys_runtime_available(
                project_root,
                flow_config,
            )
        else:
            availability[tool_name] = is_tool_available(tool_name)

    for tool_name in required_tools:
        status = "found" if availability[tool_name] else "missing"
        print(f"{tool_name}: {status}")

    if not all(availability.values()):
        raise typer.Exit(code=1)

    print("All required tools are available.")
