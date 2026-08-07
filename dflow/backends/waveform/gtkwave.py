import subprocess
from pathlib import Path

from dflow.utils import is_tool_available


GTKWAVE = "gtkwave"


def _latest_vcd(
    wave_directory: Path,
    modified_since_ns: int | None = None,
) -> Path | None:
    waveforms = [
        path
        for path in wave_directory.rglob("*.vcd")
        if path.is_file()
        and (
            modified_since_ns is None
            or path.stat().st_mtime_ns >= modified_since_ns
        )
    ]
    if not waveforms:
        return None
    return max(waveforms, key=lambda path: (path.stat().st_mtime_ns, str(path)))


def open_latest_waveform(
    project_root: Path,
    modified_since_ns: int | None = None,
) -> bool:
    """Open the newest project VCD in a detached GTKWave process."""
    waveform = _latest_vcd(
        project_root / "sim" / "waves",
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
