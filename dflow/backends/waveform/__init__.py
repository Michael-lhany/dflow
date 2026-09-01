from pathlib import Path

from dflow.config import get_flow_tool, load_flow_config

from .gtkwave import open_latest_waveform as open_latest_gtkwave_waveform
from .verdi import open_latest_waveform as open_latest_verdi_waveform


def open_latest_waveform(
    project_root: Path,
    modified_since_ns: int | None = None,
    flow_config: dict | None = None,
) -> bool:
    """Open the latest waveform with the configured viewer."""
    config = (
        flow_config
        if flow_config is not None
        else load_flow_config(project_root)
    )
    waveform_tool = get_flow_tool(config, "waveform") or "gtkwave"
    if waveform_tool == "gtkwave":
        return open_latest_gtkwave_waveform(project_root, modified_since_ns)
    if waveform_tool == "verdi":
        return open_latest_verdi_waveform(project_root, modified_since_ns)

    print(
        f"Unsupported waveform tool '{waveform_tool}' configured in "
        f"{project_root / 'flow.yaml'}."
    )
    return False


__all__ = ["open_latest_waveform"]
