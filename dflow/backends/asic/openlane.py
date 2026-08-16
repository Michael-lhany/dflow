import os
from pathlib import Path

from dflow.backends.executor import run_flow_command
from dflow.backends.result import FlowRunResult
from dflow.config import get_flow_options, get_flow_section
from dflow.utils import is_tool_available


OPENLANE = "openlane"
NIX = "nix"
DEFAULT_CONFIG = Path("openlane/config.json")


def _resolve_path(project_root: Path, configured_path: str) -> Path:
    expanded_path = os.path.expanduser(os.path.expandvars(configured_path))
    path = Path(expanded_path)
    if not path.is_absolute():
        path = project_root / path
    return path.resolve()


def _configured_path(
    project_root: Path,
    section: dict,
    key: str,
    default: Path | None = None,
) -> Path | None:
    value = section.get(key)
    if value is None and default is not None:
        value = str(default)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"asic.{key} must be a non-empty path.")
    return _resolve_path(project_root, value)


def resolve_openlane_command(
    project_root: Path,
    flow_config: dict,
) -> list[str] | None:
    """Resolve a direct or Nix-provided OpenLane executable command."""
    section = get_flow_section(flow_config, "asic")
    try:
        configured_executable = _configured_path(
            project_root,
            section,
            "executable",
        )
    except ValueError as error:
        print(error)
        return None

    if configured_executable is not None:
        if not configured_executable.is_file() or not os.access(
            configured_executable,
            os.X_OK,
        ):
            print(
                "Configured OpenLane executable was not found or is not "
                f"executable: {configured_executable}"
            )
            return None
        return [str(configured_executable)]

    if is_tool_available(OPENLANE):
        return [OPENLANE]

    try:
        openlane_root = _configured_path(
            project_root,
            section,
            "openlane_root",
        )
    except ValueError as error:
        print(error)
        return None

    if openlane_root is None:
        print(
            "OpenLane was not found on PATH. Configure asic.openlane_root "
            "with the path to an OpenLane 2 Nix checkout."
        )
        return None
    if not (openlane_root / "flake.nix").is_file():
        print(f"OpenLane flake was not found under {openlane_root}.")
        return None
    if not is_tool_available(NIX):
        print("Nix is required to run the configured OpenLane checkout.")
        return None

    return [
        NIX,
        "develop",
        f"{openlane_root}#default",
        "--command",
        OPENLANE,
    ]


def is_openlane_runtime_available(
    project_root: Path,
    flow_config: dict,
) -> bool:
    """Return whether OpenLane can run directly or through its Nix flake."""
    section = get_flow_section(flow_config, "asic")
    try:
        configured_executable = _configured_path(
            project_root,
            section,
            "executable",
        )
    except ValueError:
        return False
    if configured_executable is not None:
        return configured_executable.is_file() and os.access(
            configured_executable,
            os.X_OK,
        )

    if is_tool_available(OPENLANE):
        return True

    try:
        openlane_root = _configured_path(
            project_root,
            section,
            "openlane_root",
        )
    except ValueError:
        return False

    return bool(
        openlane_root is not None
        and (openlane_root / "flake.nix").is_file()
        and is_tool_available(NIX)
    )


def _append_configured_flag(
    command: list[str],
    section: dict,
    key: str,
    flag: str,
) -> None:
    value = section.get(key)
    if value is None:
        return
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"asic.{key} must be a non-empty string.")
    command.extend([flag, value])


def run_openlane(
    project_root: Path,
    flow_config: dict,
) -> FlowRunResult | None:
    """Run an OpenLane 2 flow from a project design configuration."""
    section = get_flow_section(flow_config, "asic")
    command = resolve_openlane_command(project_root, flow_config)
    if command is None:
        return None

    try:
        config_path = _configured_path(
            project_root,
            section,
            "config",
            DEFAULT_CONFIG,
        )
    except ValueError as error:
        print(error)
        return None

    if config_path is None or not config_path.is_file():
        print(f"OpenLane design config was not found: {config_path}")
        return None
    if config_path.suffix.lower() not in {".json", ".yaml", ".yml", ".tcl"}:
        print(
            "OpenLane design config must use JSON, YAML, YML, or Tcl: "
            f"{config_path}"
        )
        return None

    command.extend(get_flow_options(flow_config, "asic"))
    try:
        _append_configured_flag(command, section, "flow", "--flow")
        _append_configured_flag(command, section, "pdk", "--pdk")
        _append_configured_flag(command, section, "scl", "--scl")
        _append_configured_flag(command, section, "run_tag", "--run-tag")
        pdk_root = _configured_path(project_root, section, "pdk_root")
    except ValueError as error:
        print(error)
        return None

    if pdk_root is not None:
        command.extend(["--pdk-root", str(pdk_root)])
    command.append(str(config_path))

    step = run_flow_command(
        command,
        project_root,
        "OpenLane ASIC flow",
        stream_output=True,
    )
    return FlowRunResult(tool_name=OPENLANE, steps=[step])
