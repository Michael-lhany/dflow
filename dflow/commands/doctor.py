import typer

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
    ]
    required_tools = list(dict.fromkeys(
        tool_name for tool_name in configured_tools if tool_name
    ))
    availability = {
        tool_name: is_tool_available(tool_name)
        for tool_name in required_tools
    }

    for tool_name in required_tools:
        status = "found" if availability[tool_name] else "missing"
        print(f"{tool_name}: {status}")

    if not all(availability.values()):
        raise typer.Exit(code=1)

    print("All required tools are available.")
