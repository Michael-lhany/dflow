import os
from pathlib import Path

from dflow.backends.executor import run_flow_command
from dflow.backends.result import FlowRunResult
from dflow.config import get_flow_options, get_flow_section
from dflow.core.filesystem import create_directory, create_text_file, remove_path
from dflow.core.project import find_rtl_sources
from dflow.utils import is_tool_available


SPYGLASS = "spyglass"
OUTPUT_DIRECTORY = Path("build/lint/spyglass")
DEFAULT_GOAL = "lint/lint_rtl"


def _quote_spyglass_value(value: str | Path) -> str:
    """Quote one value for a generated SpyGlass project file."""
    escaped = str(value).replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")
    return "{" + escaped + "}"


def _resolve_project_file(project_root: Path, configured_path: object) -> Path:
    if not isinstance(configured_path, str) or not configured_path.strip():
        raise ValueError("lint.project must be a non-empty path.")

    expanded = os.path.expanduser(os.path.expandvars(configured_path))
    project_file = Path(expanded)
    if not project_file.is_absolute():
        project_file = project_root / project_file
    project_file = project_file.resolve()
    if not project_file.is_file():
        raise ValueError(f"SpyGlass project file was not found: {project_file}")
    return project_file


def _build_generated_project(
    output_directory: Path,
    rtl_sources: list[Path],
    top_module: str | None,
) -> str:
    lines = [
        "set_option enableSV yes",
        f"set_option projectwdir {_quote_spyglass_value(output_directory)}",
    ]
    lines.extend(
        f"read_file -type verilog {_quote_spyglass_value(source)}"
        for source in rtl_sources
    )
    if top_module:
        lines.append(f"set_option top {_quote_spyglass_value(top_module)}")
    return "\n".join(lines) + "\n"


def run_spyglass_lint(
    project_root: Path,
    flow_config: dict,
) -> FlowRunResult | None:
    """Run a batch SpyGlass RTL lint goal."""
    if not is_tool_available(SPYGLASS):
        print("spyglass is required for lint but was not found on PATH.")
        return None

    lint_config = get_flow_section(flow_config, "lint")
    configured_project = lint_config.get("project")
    rtl_sources = find_rtl_sources(project_root)
    if configured_project is None and not rtl_sources:
        print(f"No RTL sources were found under {project_root / 'rtl'}.")
        return None

    goal = lint_config.get("goal", DEFAULT_GOAL)
    if not isinstance(goal, str) or not goal.strip():
        print("lint.goal must be a non-empty string.")
        return None

    output_directory = project_root / OUTPUT_DIRECTORY
    try:
        project_file = (
            _resolve_project_file(project_root, configured_project)
            if configured_project is not None
            else output_directory / "dflow.prj"
        )
    except ValueError as error:
        print(error)
        return None

    if configured_project is not None and project_file.is_relative_to(
        output_directory.resolve()
    ):
        print(
            "lint.project must be outside DFlow's generated SpyGlass "
            f"directory: {output_directory}"
        )
        return None

    remove_path(output_directory, project_root)
    create_directory(output_directory)
    if configured_project is None:
        configured_top = lint_config.get("top")
        top_module = (
            configured_top
            if isinstance(configured_top, str) and configured_top
            else None
        )
        create_text_file(
            project_file,
            _build_generated_project(output_directory, rtl_sources, top_module),
        )

    command = [
        SPYGLASS,
        *get_flow_options(flow_config, "lint"),
        "-batch",
        "-project",
        str(project_file),
        "-goals",
        goal,
    ]
    step = run_flow_command(command, project_root, "SpyGlass lint")
    return FlowRunResult(tool_name=SPYGLASS, steps=[step])
