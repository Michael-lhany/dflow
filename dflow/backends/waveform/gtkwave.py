import subprocess
from pathlib import Path

from dflow.backends.waveform.common import latest_waveform
from dflow.utils import is_tool_available


GTKWAVE = "gtkwave"


def open_latest_waveform(
    project_root: Path,
    modified_since_ns: int | None = None,
) -> bool:
    """Open the newest project VCD in a detached GTKWave process."""
    waveform = latest_waveform(
        project_root / "sim" / "waves",
        {".vcd"},
        modified_since_ns,
    )
    if waveform is None:
        wave_directory = project_root / "sim" / "waves"
        if modified_since_ns is None:
            print(f"No VCD waveform was found under {wave_directory}.")
        else:
            print(f"No new VCD waveform was generated under {wave_directory}.")
        return False

    if not is_tool_available(GTKWAVE):
        print("GTKWave is required for --wave but was not found on PATH.")
        return False

    try:
        subprocess.Popen(
            [GTKWAVE, str(waveform)],
            cwd=project_root,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError as error:
        print(f"Failed to open {waveform} with GTKWave: {error}")
        return False

    print(f"Opening {waveform.relative_to(project_root)} with GTKWave.")
    return True
