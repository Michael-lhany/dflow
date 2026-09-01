import subprocess
from pathlib import Path

from dflow.backends.waveform.common import latest_waveform
from dflow.utils import is_tool_available


VERDI = "verdi"
SUPPORTED_SUFFIXES = {".fsdb"}


def open_latest_waveform(
    project_root: Path,
    modified_since_ns: int | None = None,
) -> bool:
    """Open the newest supported waveform in a detached Verdi process."""
    wave_directory = project_root / "sim" / "waves"
    waveform = latest_waveform(
        wave_directory,
        SUPPORTED_SUFFIXES,
        modified_since_ns,
    )
    if waveform is None:
        qualifier = "new " if modified_since_ns is not None else ""
        print(f"No {qualifier}Verdi waveform was found under {wave_directory}.")
        return False

    if not is_tool_available(VERDI):
        print("Verdi is required for --wave but was not found on PATH.")
        return False

    try:
        subprocess.Popen(
            [VERDI, "-ssf", str(waveform)],
            cwd=project_root,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError as error:
        print(f"Failed to open {waveform} with Verdi: {error}")
        return False

    print(f"Opening {waveform.relative_to(project_root)} with Verdi.")
    return True
