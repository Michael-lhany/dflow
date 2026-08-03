from pathlib import Path

from dflow.config import get_flow_section, get_flow_tool, load_flow_config
from dflow.core.project import (
    find_project_root,
    find_rtl_sources,
    find_tb_sources,
)


def _report_status(project_root: Path, stage: str, tool_name: str) -> str:
    report_path = project_root / "reports" / stage / f"{tool_name}.log"
    if not report_path.is_file():
        return "not run"

    try:
        report_lines = report_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return "unknown"

    for line in reversed(report_lines):
        if not line.startswith("Return code:"):
            continue

        try:
            return_code = int(line.partition(":")[2].strip())
        except ValueError:
            return "unknown"

        if return_code == 0:
            return "passed"
        return f"failed (exit code {return_code})"

    return "unknown"


def _has_files(directory: Path) -> bool:
    return directory.is_dir() and any(
        path.is_file() for path in directory.rglob("*")
    )


def status() -> None:
    """Show a read-only summary of the current project."""
    project_root = find_project_root()
    flow_config = load_flow_config(project_root)
    project_config = get_flow_section(flow_config, "project")
    configured_name = project_config.get("name")
    project_name = (
        configured_name
        if isinstance(configured_name, str) and configured_name
        else project_root.name
    )

    rtl_count = len(find_rtl_sources(project_root))
    testbench_count = len(find_tb_sources(project_root))

    print(f"Project: {project_name}")
    print(f"Root: {project_root}")
    print("\nSources:")
    print(f"  RTL: {rtl_count} {'file' if rtl_count == 1 else 'files'}")
    print(
        "  Testbench: "
        f"{testbench_count} {'file' if testbench_count == 1 else 'files'}"
    )

    print("\nFlows:")
    for label, stage in (
        ("Compile", "compile"),
        ("Lint", "lint"),
        ("Simulation", "simulation"),
        ("Synthesis", "synthesis"),
    ):
        tool_name = get_flow_tool(flow_config, stage)
        displayed_tool = tool_name or "not configured"
        if stage == "synthesis":
            result = "not implemented yet"
        elif tool_name:
            report_stage = "sim" if stage == "simulation" else stage
            last_result = _report_status(project_root, report_stage, tool_name)
            result = f"last run: {last_result}"
        else:
            result = "not run"
        print(f"  {label + ':':<12}{displayed_tool:<16}{result}")

    has_build_files = _has_files(project_root / "obj_dir") or _has_files(
        project_root / "sim" / "obj_dir"
    )
    artifacts = (
        ("Reports", _has_files(project_root / "reports")),
        ("Waveforms", _has_files(project_root / "sim" / "waves")),
        ("Build files", has_build_files),
    )

    print("\nGenerated artifacts:")
    for label, available in artifacts:
        state = "available" if available else "none"
        print(f"  {label}: {state}")
