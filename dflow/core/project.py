from pathlib import Path

from dflow.core.filesystem import create_directory, create_text_file


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


def save_flow_report(
    project_root: Path,
    report_name: str,
    tool_name: str,
    command: list[str],
    returncode: int,
    stdout: str = "",
    stderr: str = "",
) -> Path:
    """Persist flow output under the project's reports directory."""
    report_dir = project_root / "reports" / report_name
    report_path = report_dir / f"{tool_name}.log"
    create_directory(report_dir)

    report_lines = [
        "Command: " + " ".join(command),
        f"Return code: {returncode}",
    ]

    if stdout:
        report_lines.extend(["", "STDOUT:", stdout.rstrip("\n")])

    if stderr:
        report_lines.extend(["", "STDERR:", stderr.rstrip("\n")])

    create_text_file(report_path, "\n".join(report_lines) + "\n")
    return report_path


def save_lint_report(
    project_root: Path,
    tool_name: str,
    command: list[str],
    returncode: int,
    stdout: str = "",
    stderr: str = "",
) -> Path:
    """Persist lint output under the project's reports directory."""
    return save_flow_report(
        project_root,
        "lint",
        tool_name,
        command,
        returncode,
        stdout=stdout,
        stderr=stderr,
    )


def save_compile_report(
    project_root: Path,
    tool_name: str,
    command: list[str],
    returncode: int,
    stdout: str = "",
    stderr: str = "",
) -> Path:
    """Persist compile output under the project's reports directory."""
    return save_flow_report(
        project_root,
        "compile",
        tool_name,
        command,
        returncode,
        stdout=stdout,
        stderr=stderr,
    )
