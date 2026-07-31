from shutil import which


def is_tool_available(tool_name: str) -> bool:
	"""Return True when the named executable is on PATH."""
	return which(tool_name) is not None


def find_missing_tools(tool_names: list[str]) -> list[str]:
	"""Return the tools from the list that are not available."""
	return [tool_name for tool_name in tool_names if not is_tool_available(tool_name)]
