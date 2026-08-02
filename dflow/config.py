from pathlib import Path

import yaml


def load_flow_config(project_root: Path) -> dict:
	"""Load the project's flow.yaml configuration if it exists."""
	config_path = project_root / "flow.yaml"

	if not config_path.exists():
		return {}

	loaded_config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
	return loaded_config or {}


def get_flow_section(flow_config: dict, section_name: str) -> dict:
	"""Return a normalized mapping for a flow section."""
	section_config = flow_config.get(section_name)
	return section_config if isinstance(section_config, dict) else {}


def get_flow_tool(flow_config: dict, section_name: str) -> str | None:
	"""Return the configured tool name for a flow section."""
	section_config = get_flow_section(flow_config, section_name)
	tool_name = section_config.get("tool")

	return tool_name if isinstance(tool_name, str) and tool_name else None


def get_flow_options(flow_config: dict, section_name: str, default: list[str] | None = None) -> list[str]:
    """Return string options configured for a flow section."""
    section_config = get_flow_section(flow_config, section_name)
    configured_options = section_config.get("options")
    cli_options = section_config.get("_cli_options")

    if not isinstance(configured_options, list):
        options = list(default or [])
    else:
        options = [
            option
            for option in configured_options
            if isinstance(option, str) and option
        ]

    if isinstance(cli_options, list):
        options.extend(
            option
            for option in cli_options
            if isinstance(option, str) and option
        )

    return options
