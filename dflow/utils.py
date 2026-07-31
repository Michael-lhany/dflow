from shutil import which


def is_tool_available(tool_name: str) -> bool:
    """Return True when the named executable is on PATH."""
    return which(tool_name) is not None
