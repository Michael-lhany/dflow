from dflow.backends import vcs as shared_backend
from dflow.backends.compile import run_compile
from dflow.backends.result import FlowStepResult
from dflow.backends.simulation import run_simulation
from dflow.backends.simulation import vcs as simulation_backend


def _create_sources(project_root):
    rtl_source = project_root / "rtl" / "top.sv"
    tb_source = project_root / "tb" / "top_tb.sv"
    rtl_source.parent.mkdir(parents=True)
    tb_source.parent.mkdir(parents=True)
    rtl_source.write_text("module top; endmodule\n", encoding="utf-8")
    tb_source.write_text("module top_tb; endmodule\n", encoding="utf-8")
    return rtl_source, tb_source


def test_compile_dispatches_to_vcs_and_builds_project_owned_binary(
    monkeypatch,
    tmp_path,
):
    rtl_source, _ = _create_sources(tmp_path)
    captured_command: list[str] = []
    monkeypatch.setattr(shared_backend, "is_tool_available", lambda tool: True)

    def fake_run(command, project_root, step_name, env=None):
        captured_command.extend(command)
        return FlowStepResult(step_name, command, 0)

    monkeypatch.setattr(shared_backend, "run_flow_command", fake_run)
    result = run_compile(
        tmp_path,
        {"compile": {"tool": "vcs", "top": "top"}},
    )

    output_directory = tmp_path / "sim" / "vcs_compile"
    assert result is not None
    assert result.tool_name == "vcs"
    assert captured_command == [
        "vcs",
        "-full64",
        "-sverilog",
        f"-Mdir={output_directory / 'csrc'}",
        "-o",
        str(output_directory / "simv"),
        str(rtl_source),
        "-top",
        "top",
    ]
    assert output_directory.is_dir()


def test_simulation_dispatches_to_vcs_builds_and_runs(monkeypatch, tmp_path):
    rtl_source, tb_source = _create_sources(tmp_path)
    calls: list[str] = []
    commands: dict[str, list[str]] = {}
    monkeypatch.setattr(simulation_backend, "is_tool_available", lambda tool: True)

    def fake_run(command, project_root, step_name, env=None):
        calls.append(step_name)
        commands[step_name] = command
        if step_name == "VCS build":
            (project_root / "sim" / "vcs" / "simv").touch()
        return FlowStepResult(step_name, command, 0)

    monkeypatch.setattr(simulation_backend, "run_flow_command", fake_run)
    result = run_simulation(
        tmp_path,
        {"simulation": {"tool": "vcs", "top": "top_tb"}},
    )

    output_directory = tmp_path / "sim" / "vcs"
    assert result is not None
    assert result.returncode == 0
    assert calls == ["VCS build", "Simulation"]
    assert commands["VCS build"] == [
        "vcs",
        "-full64",
        "-sverilog",
        "-timescale=1ns/1ps",
        "-debug_access+all",
        "-kdb",
        f"-Mdir={output_directory / 'csrc'}",
        "-o",
        str(output_directory / "simv"),
        str(rtl_source),
        str(tb_source),
        "-top",
        "top_tb",
    ]
    assert commands["Simulation"] == [str(output_directory / "simv")]


def test_simulation_uses_configured_compile_and_runtime_options(
    monkeypatch,
    tmp_path,
):
    _create_sources(tmp_path)
    commands: dict[str, list[str]] = {}
    monkeypatch.setattr(simulation_backend, "is_tool_available", lambda tool: True)

    def fake_run(command, project_root, step_name, env=None):
        commands[step_name] = command
        if step_name == "VCS build":
            (project_root / "sim" / "vcs" / "simv").touch()
        return FlowStepResult(step_name, command, 0)

    monkeypatch.setattr(simulation_backend, "run_flow_command", fake_run)
    result = run_simulation(
        tmp_path,
        {
            "simulation": {
                "tool": "vcs",
                "top": "top_tb",
                "options": ["-sverilog", "+define+RTL_SIM"],
                "runtime_options": ["+UVM_TESTNAME=smoke"],
            }
        },
    )

    assert result is not None
    assert "+define+RTL_SIM" in commands["VCS build"]
    assert "-debug_access+all" not in commands["VCS build"]
    assert commands["Simulation"][1:] == ["+UVM_TESTNAME=smoke"]


def test_simulation_stops_after_failed_vcs_build(monkeypatch, tmp_path):
    _create_sources(tmp_path)
    calls: list[str] = []
    monkeypatch.setattr(simulation_backend, "is_tool_available", lambda tool: True)

    def fake_run(command, project_root, step_name, env=None):
        calls.append(step_name)
        return FlowStepResult(step_name, command, 2)

    monkeypatch.setattr(simulation_backend, "run_flow_command", fake_run)
    result = run_simulation(
        tmp_path,
        {"simulation": {"tool": "vcs", "top": "top_tb"}},
    )

    assert result is not None
    assert result.returncode == 2
    assert calls == ["VCS build"]
