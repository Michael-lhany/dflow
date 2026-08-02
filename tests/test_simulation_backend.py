from dflow.backends.result import FlowStepResult
from dflow.backends.simulation import verilator as simulation_backend


def _create_sources(project_root):
    rtl_source = project_root / "rtl" / "top.v"
    tb_source = project_root / "tb" / "top_tb.sv"
    rtl_source.parent.mkdir(parents=True)
    tb_source.parent.mkdir(parents=True)
    rtl_source.write_text("module top; endmodule\n", encoding="utf-8")
    tb_source.write_text("module top_tb; endmodule\n", encoding="utf-8")


def test_simulation_returns_each_completed_step(monkeypatch, tmp_path):
    _create_sources(tmp_path)
    calls: list[str] = []

    monkeypatch.setattr(
        simulation_backend,
        "is_tool_available",
        lambda tool_name: True,
    )

    def fake_run(command, project_root, step_name, env=None):
        calls.append(step_name)
        if step_name == "Make build":
            binary = project_root / "sim" / "obj_dir" / "Vtop_tb"
            binary.touch()
        return FlowStepResult(step_name, command, 0, f"{step_name} output\n")

    monkeypatch.setattr(simulation_backend, "run_flow_command", fake_run)

    result = simulation_backend.run_verilator_simulation(
        tmp_path,
        {"simulation": {"tool": "verilator", "top": "top_tb"}},
    )

    assert result is not None
    assert result.returncode == 0
    assert calls == ["Verilator build", "Make build", "Simulation"]
    assert [step.name for step in result.steps] == calls
    assert (tmp_path / "sim" / "waves").is_dir()


def test_simulation_stops_after_failed_make(monkeypatch, tmp_path):
    _create_sources(tmp_path)

    monkeypatch.setattr(
        simulation_backend,
        "is_tool_available",
        lambda tool_name: True,
    )

    def fake_run(command, project_root, step_name, env=None):
        return FlowStepResult(
            step_name,
            command,
            2 if step_name == "Make build" else 0,
        )

    monkeypatch.setattr(simulation_backend, "run_flow_command", fake_run)

    result = simulation_backend.run_verilator_simulation(
        tmp_path,
        {"simulation": {"tool": "verilator", "top": "top_tb"}},
    )

    assert result is not None
    assert result.returncode == 2
    assert [step.name for step in result.steps] == [
        "Verilator build",
        "Make build",
    ]
