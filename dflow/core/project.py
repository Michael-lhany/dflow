from pathlib import Path
from typing import TYPE_CHECKING, Sequence

from dflow.core.filesystem import create_directory, create_text_file

if TYPE_CHECKING:
    from dflow.backends.result import FlowStepResult

PROJECT_DIRECTORIES = [
    "rtl",
    "tb",
    "scripts",
    "constraints",
    "docs",
    "reports",
    "formal",
    "openlane",
    "sim",
    "sim/logs",
    "sim/waves",
]

PROJECT_MARKER = ".dflow"
DEFAULT_FLOW_CONFIG = """project:
    name: {project_name}

compile:
    tool: verilator
    options:
        - --cc

lint:
    tool: verilator
    options:
        - --lint-only
        - -Wall

simulation:
    tool: verilator

synthesis:
    tool: yosys
"""


def create_project(project_name: str):
    """
    Create a new DFM project.
    """

    root = Path(project_name)

    create_directory(root)

    create_text_file(root / PROJECT_MARKER, "version: 0.1.0\n")
    create_text_file(
        root / "flow.yaml",
        DEFAULT_FLOW_CONFIG.format(project_name=project_name),
    )

    for directory in PROJECT_DIRECTORIES:
        create_directory(root / directory)

    print(f"Project '{project_name}' created successfully.")


def find_project_root(start_path: Path | None = None) -> Path:
    """Find the nearest parent directory containing the project marker."""
    current_path = (start_path or Path.cwd()).resolve()

    for candidate_path in (current_path, *current_path.parents):
        if (candidate_path / PROJECT_MARKER).exists():
            return candidate_path

    raise FileNotFoundError("Could not find a DFlow project root.")


def find_rtl_sources(project_root: Path) -> list[Path]:
    """Return RTL source files under the project's rtl directory."""
    rtl_root = project_root / "rtl"
    if not rtl_root.exists():
        return []

    return sorted(
        path
        for path in rtl_root.rglob("*")
        if path.is_file() and path.suffix in {".v", ".sv", ".svh"}
    )


def find_tb_sources(project_root: Path) -> list[Path]:
    """Return testbench source files under the project's tb directory."""
    tb_root = project_root / "tb"
    if not tb_root.exists():
        return []

    return sorted(
        path
        for path in tb_root.rglob("*")
        if path.is_file() and path.suffix in {".v", ".sv", ".svh", ".cpp", ".cc", ".cxx"}
    )


def save_flow_report(
    project_root: Path,
    report_name: str,
    tool_name: str,
    steps: Sequence["FlowStepResult"],
) -> Path:
    """Persist flow output under the project's reports directory."""
    report_dir = project_root / "reports" / report_name
    report_path = report_dir / f"{tool_name}.log"
    create_directory(report_dir)

    report_lines: list[str] = []
    for index, step in enumerate(steps, start=1):
        if report_lines:
            report_lines.append("")

        report_lines.extend(
            [
                f"Step {index}: {step.name}",
                "Command: " + (" ".join(step.command) if step.command else "<none>"),
                f"Return code: {step.returncode}",
            ]
        )

        if step.stdout:
            report_lines.extend(["", "STDOUT:", step.stdout.rstrip("\n")])

        if step.stderr:
            report_lines.extend(["", "STDERR:", step.stderr.rstrip("\n")])

    create_text_file(report_path, "\n".join(report_lines) + "\n")
    return report_path
