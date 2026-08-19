import os
from datetime import datetime
from pathlib import Path

from dflow.backends.executor import run_flow_command
from dflow.backends.result import FlowRunResult
from dflow.config import get_flow_options, get_flow_section
from dflow.core.filesystem import create_directory
from dflow.utils import is_tool_available


SBY = "sby"
DEFAULT_CONFIG = Path("formal/design.sby")
DEFAULT_OUTPUT_DIRECTORY = Path("formal/runs")


def _resolve_path(project_root: Path, value: str) -> Path:
    expanded = os.path.expanduser(os.path.expandvars(value))
    path = Path(expanded)
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
        raise ValueError(f"formal.{key} must be a non-empty path.")
    return _resolve_path(project_root, value)


def _configured_tasks(section: dict) -> list[str]:
    value = section.get("tasks")
    if value is None:
        return []
    if not isinstance(value, list) or any(
        not isinstance(task, str) or not task.strip() for task in value
    ):
        raise ValueError("formal.tasks must be a list of non-empty task names.")
    return [task.strip() for task in value]


def _resolve_executable(project_root: Path, section: dict) -> str | None:
    configured = _configured_path(project_root, section, "executable")
    if configured is not None:
        if configured.is_file() and os.access(configured, os.X_OK):
            return str(configured)
        raise ValueError(
            "Configured SymbiYosys executable was not found or is not "
            f"executable: {configured}"
        )
    if is_tool_available(SBY):
        return SBY
    return None


def is_symbiyosys_runtime_available(
    project_root: Path,
    flow_config: dict,
) -> bool:
    """Return whether the configured SymbiYosys executable is available."""
    try:
        return _resolve_executable(
            project_root,
            get_flow_section(flow_config, "formal"),
        ) is not None
    except ValueError:
        return False


def _new_run_prefix(output_directory: Path, config_stem: str) -> Path:
    timestamp = datetime.now().astimezone().strftime("%Y-%m-%d_%H-%M-%S_%f%z")
    prefix = output_directory / f"{config_stem}_{timestamp}"
    collision_index = 1
    while prefix.exists() or any(prefix.parent.glob(f"{prefix.name}_*")):
        prefix = output_directory / (
            f"{config_stem}_{timestamp}_{collision_index}"
        )
        collision_index += 1
    return prefix


def run_symbiyosys(
    project_root: Path,
    flow_config: dict,
) -> FlowRunResult | None:
    """Run an SBY job in a timestamped formal output directory."""
    section = get_flow_section(flow_config, "formal")
    try:
        executable = _resolve_executable(project_root, section)
        config_path = _configured_path(
            project_root,
            section,
            "config",
            DEFAULT_CONFIG,
        )
        output_directory = _configured_path(
            project_root,
            section,
            "output_directory",
            DEFAULT_OUTPUT_DIRECTORY,
        )
        tasks = _configured_tasks(section)
    except ValueError as error:
        print(error)
        return None

    if executable is None:
        print("sby is required for formal verification but was not found on PATH.")
        return None
    if config_path is None or not config_path.is_file():
        print(f"SymbiYosys configuration was not found: {config_path}")
        return None
    if config_path.suffix.lower() != ".sby":
        print(f"SymbiYosys configuration must use the .sby extension: {config_path}")
        return None
    if output_directory is None:
        return None

    create_directory(output_directory)
    run_prefix = _new_run_prefix(output_directory, config_path.stem)
    command = [
        executable,
        *get_flow_options(flow_config, "formal"),
        "--prefix",
        str(run_prefix),
        str(config_path),
        *tasks,
    ]
    step = run_flow_command(
        command,
        project_root,
        "SymbiYosys formal verification",
        stream_output=True,
    )
    return FlowRunResult(tool_name=SBY, steps=[step])
