from pathlib import Path


def latest_waveform(
    wave_directory: Path,
    suffixes: set[str],
    modified_since_ns: int | None = None,
) -> Path | None:
    """Return the newest supported waveform in a directory tree."""
    waveforms = [
        path
        for path in wave_directory.rglob("*")
        if path.is_file()
        and path.suffix.lower() in suffixes
        and (
            modified_since_ns is None
            or path.stat().st_mtime_ns >= modified_since_ns
        )
    ]
    if not waveforms:
        return None
    return max(waveforms, key=lambda path: (path.stat().st_mtime_ns, str(path)))
