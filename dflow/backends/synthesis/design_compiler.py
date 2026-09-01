import os
from pathlib import Path

from dflow.backends.executor import run_flow_command
from dflow.backends.result import FlowRunResult
from dflow.config import get_flow_options, get_flow_section
from dflow.core.filesystem import create_directory, create_text_file, remove_path
from dflow.core.project import find_rtl_sources
from dflow.utils import is_tool_available


DC_SHELL = "dc_shell"
OUTPUT_DIRECTORY = Path("build/synthesis/dc")


def _quote_tcl_value(value: str | Path) -> str:
    """Quote one literal value for a generated Tcl script."""
    escaped = str(value).replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")
    return "{" + escaped + "}"


def _resolve_optional_file(
    project_root: Path,
    configured_path: object,
    field_name: str,
) -> Path | None:
    if configured_path is None:
        return None
    if not isinstance(configured_path, str) or not configured_path.strip():
        raise ValueError(f"synthesis.{field_name} must be a non-empty path.")

    expanded = os.path.expanduser(os.path.expandvars(configured_path))
    path = Path(expanded)
    if not path.is_absolute():
        path = project_root / path
    path = path.resolve()
    if not path.is_file():
        raise ValueError(f"Design Compiler {field_name} file was not found: {path}")
    return path


def _get_string_list(config: dict, field_name: str) -> list[str]:
    value = config.get(field_name)
    if value is None:
        return []
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item for item in value
    ):
        raise ValueError(
            f"synthesis.{field_name} must be a list of non-empty strings."
        )
    return value


def is_design_compiler_runtime_available(flow_config: dict) -> bool:
    """Return whether the configured Design Compiler executable is available."""
    synthesis_config = get_flow_section(flow_config, "synthesis")
    executable = synthesis_config.get("executable", DC_SHELL)
    return (
        isinstance(executable, str)
        and bool(executable.strip())
        and is_tool_available(executable)
    )


def _build_dc_script(
    rtl_sources: list[Path],
    top_module: str,
    output_directory: Path,
    setup_file: Path | None,
    constraints_file: Path | None,
    target_libraries: list[str],
    link_libraries: list[str],
    compile_ultra: bool,
) -> str:
    work_directory = output_directory / "work"
    reports_directory = output_directory / "reports"
    source_list = " ".join(_quote_tcl_value(source) for source in rtl_sources)
    lines = [
        "set_app_var sh_continue_on_error false",
        f"file mkdir {_quote_tcl_value(work_directory)}",
        f"file mkdir {_quote_tcl_value(reports_directory)}",
        f"define_design_lib WORK -path {_quote_tcl_value(work_directory)}",
    ]
    if setup_file:
        lines.append(f"source {_quote_tcl_value(setup_file)}")
    if target_libraries:
        libraries = " ".join(_quote_tcl_value(item) for item in target_libraries)
        lines.append(f"set_app_var target_library [list {libraries}]")
    if link_libraries:
        libraries = " ".join(_quote_tcl_value(item) for item in link_libraries)
        lines.append(f"set_app_var link_library [list {libraries}]")
    lines.extend(
        (
            f"analyze -format sverilog [list {source_list}]",
            f"elaborate {_quote_tcl_value(top_module)}",
            f"current_design {_quote_tcl_value(top_module)}",
            "link",
        )
    )
    if constraints_file:
        lines.append(f"source {_quote_tcl_value(constraints_file)}")
    lines.extend(
        (
            "check_design",
            "compile_ultra" if compile_ultra else "compile",
            "change_names -rules verilog -hierarchy",
            "write -format verilog -hierarchy -output "
            f"{_quote_tcl_value(output_directory / 'netlist.v')}",
            "write -format ddc -hierarchy -output "
            f"{_quote_tcl_value(output_directory / 'design.ddc')}",
            "write_sdc " + _quote_tcl_value(output_directory / "constraints.sdc"),
            "redirect -file "
            f"{_quote_tcl_value(reports_directory / 'qor.rpt')} {{ report_qor }}",
            "redirect -file "
            f"{_quote_tcl_value(reports_directory / 'area.rpt')} {{ report_area }}",
            "redirect -file "
            f"{_quote_tcl_value(reports_directory / 'timing.rpt')} "
            "{ report_timing -max_paths 10 }",
            "exit",
        )
    )
    return "\n".join(lines) + "\n"


def run_design_compiler_synthesis(
    project_root: Path,
    flow_config: dict,
) -> FlowRunResult | None:
    """Synthesize RTL with Synopsys Design Compiler."""
    synthesis_config = get_flow_section(flow_config, "synthesis")
    executable = synthesis_config.get("executable", DC_SHELL)
    if not isinstance(executable, str) or not executable.strip():
        print("synthesis.executable must be a non-empty string.")
        return None
    if not is_design_compiler_runtime_available(flow_config):
        print(f"{executable} is required for synthesis but was not found on PATH.")
        return None

    rtl_sources = find_rtl_sources(project_root)
    if not rtl_sources:
        print(f"No RTL sources were found under {project_root / 'rtl'}.")
        return None

    configured_top = synthesis_config.get("top")
    if not isinstance(configured_top, str) or not configured_top.strip():
        print("synthesis.top is required for Design Compiler.")
        return None

    compile_ultra = synthesis_config.get("compile_ultra", False)
    if not isinstance(compile_ultra, bool):
        print("synthesis.compile_ultra must be true or false.")
        return None

    try:
        setup_file = _resolve_optional_file(
            project_root, synthesis_config.get("setup"), "setup"
        )
        constraints_file = _resolve_optional_file(
            project_root, synthesis_config.get("constraints"), "constraints"
        )
        target_libraries = _get_string_list(
            synthesis_config, "target_libraries"
        )
        link_libraries = _get_string_list(synthesis_config, "link_libraries")
    except ValueError as error:
        print(error)
        return None

    output_directory = project_root / OUTPUT_DIRECTORY
    resolved_output = output_directory.resolve()
    generated_inputs = [
        ("setup", setup_file),
        ("constraints", constraints_file),
    ]
    for field_name, input_file in generated_inputs:
        if input_file is not None and input_file.is_relative_to(resolved_output):
            print(
                f"synthesis.{field_name} must be outside DFlow's generated "
                f"Design Compiler directory: {output_directory}"
            )
            return None

    remove_path(output_directory, project_root)
    create_directory(output_directory)
    script_path = output_directory / "run.tcl"
    create_text_file(
        script_path,
        _build_dc_script(
            rtl_sources,
            configured_top,
            output_directory,
            setup_file,
            constraints_file,
            target_libraries,
            link_libraries,
            compile_ultra,
        ),
    )
    command = [
        executable,
        *get_flow_options(flow_config, "synthesis"),
        "-f",
        str(script_path),
    ]
    step = run_flow_command(command, project_root, "Design Compiler synthesis")
    return FlowRunResult(tool_name=DC_SHELL, steps=[step])
