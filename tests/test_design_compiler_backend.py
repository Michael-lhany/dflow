from dflow.backends.result import FlowStepResult
from dflow.backends.synthesis import run_synthesis
from dflow.backends.synthesis import design_compiler as dc_backend


def test_design_compiler_generates_tcl_and_outputs(monkeypatch, tmp_path):
    rtl_source = tmp_path / "rtl" / "top.sv"
    rtl_source.parent.mkdir()
    rtl_source.write_text("module top; endmodule\n", encoding="utf-8")
    setup_file = tmp_path / "scripts" / "dc_setup.tcl"
    setup_file.parent.mkdir()
    setup_file.write_text(
        "set_app_var hdlin_enable_rtldrc_info true\n", encoding="utf-8"
    )
    constraints_file = tmp_path / "constraints" / "top.sdc"
    constraints_file.parent.mkdir()
    constraints_file.write_text("create_clock -period 10 clk\n", encoding="utf-8")
    captured_command: list[str] = []

    monkeypatch.setattr(dc_backend, "is_tool_available", lambda tool_name: True)

    def fake_run(command, project_root, step_name, env=None):
        captured_command.extend(command)
        return FlowStepResult(step_name, command, 0)

    monkeypatch.setattr(dc_backend, "run_flow_command", fake_run)

    result = run_synthesis(
        tmp_path,
        {
            "synthesis": {
                "tool": "dc",
                "top": "top",
                "setup": "scripts/dc_setup.tcl",
                "constraints": "constraints/top.sdc",
                "target_libraries": ["slow.db"],
                "link_libraries": ["*", "slow.db"],
                "compile_ultra": True,
                "options": ["-no_gui"],
            }
        },
    )

    output_directory = tmp_path / "build" / "synthesis" / "dc"
    script_path = output_directory / "run.tcl"
    assert result is not None
    assert result.tool_name == "dc_shell"
    assert captured_command == [
        "dc_shell",
        "-no_gui",
        "-f",
        str(script_path),
    ]
    script = script_path.read_text(encoding="utf-8")
    assert f"source {{{setup_file}}}" in script
    assert f"analyze -format sverilog [list {{{rtl_source}}}]" in script
    assert "elaborate {top}" in script
    assert "set_app_var target_library [list {slow.db}]" in script
    assert "set_app_var link_library [list {*} {slow.db}]" in script
    assert f"source {{{constraints_file}}}" in script
    assert "compile_ultra" in script
    assert f"{{{output_directory / 'netlist.v'}}}" in script
    assert f"{{{output_directory / 'design.ddc'}}}" in script
    assert "report_qor" in script
    assert "report_area" in script
    assert "report_timing -max_paths 10" in script


def test_design_compiler_defaults_to_compile(monkeypatch, tmp_path):
    rtl_source = tmp_path / "rtl" / "top.v"
    rtl_source.parent.mkdir()
    rtl_source.write_text("module top; endmodule\n", encoding="utf-8")
    monkeypatch.setattr(dc_backend, "is_tool_available", lambda tool_name: True)
    monkeypatch.setattr(
        dc_backend,
        "run_flow_command",
        lambda command, project_root, step_name: FlowStepResult(
            step_name, command, 0
        ),
    )

    result = run_synthesis(
        tmp_path,
        {"synthesis": {"tool": "design_compiler", "top": "top"}},
    )

    script = (
        tmp_path / "build" / "synthesis" / "dc" / "run.tcl"
    ).read_text(encoding="utf-8")
    assert result is not None
    assert "\ncompile\n" in script
    assert "compile_ultra" not in script


def test_design_compiler_requires_top(monkeypatch, tmp_path, capsys):
    rtl_source = tmp_path / "rtl" / "top.v"
    rtl_source.parent.mkdir()
    rtl_source.write_text("module top; endmodule\n", encoding="utf-8")
    monkeypatch.setattr(dc_backend, "is_tool_available", lambda tool_name: True)

    result = dc_backend.run_design_compiler_synthesis(
        tmp_path, {"synthesis": {"tool": "dc"}}
    )

    assert result is None
    assert capsys.readouterr().out == (
        "synthesis.top is required for Design Compiler.\n"
    )


def test_design_compiler_rejects_missing_constraints_before_cleaning(
    monkeypatch, tmp_path, capsys
):
    rtl_source = tmp_path / "rtl" / "top.v"
    rtl_source.parent.mkdir()
    rtl_source.write_text("module top; endmodule\n", encoding="utf-8")
    stale_output = tmp_path / "build" / "synthesis" / "dc" / "netlist.v"
    stale_output.parent.mkdir(parents=True)
    stale_output.write_text("keep\n", encoding="utf-8")
    monkeypatch.setattr(dc_backend, "is_tool_available", lambda tool_name: True)

    result = dc_backend.run_design_compiler_synthesis(
        tmp_path,
        {
            "synthesis": {
                "tool": "dc",
                "top": "top",
                "constraints": "constraints/missing.sdc",
            }
        },
    )

    assert result is None
    assert "constraints file was not found" in capsys.readouterr().out
    assert stale_output.is_file()


def test_design_compiler_accepts_explicit_executable(monkeypatch, tmp_path):
    rtl_source = tmp_path / "rtl" / "top.v"
    rtl_source.parent.mkdir()
    rtl_source.write_text("module top; endmodule\n", encoding="utf-8")
    executable = str(tmp_path / "tools" / "dc_shell")
    checked: list[str] = []
    command: list[str] = []
    monkeypatch.setattr(
        dc_backend,
        "is_tool_available",
        lambda tool_name: checked.append(tool_name) or True,
    )
    monkeypatch.setattr(
        dc_backend,
        "run_flow_command",
        lambda args, project_root, step_name: (
            command.extend(args) or FlowStepResult(step_name, args, 0)
        ),
    )

    result = dc_backend.run_design_compiler_synthesis(
        tmp_path,
        {
            "synthesis": {
                "tool": "dc_shell",
                "top": "top",
                "executable": executable,
            }
        },
    )

    assert result is not None
    assert checked == [executable]
    assert command[0] == executable
