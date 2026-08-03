from dflow.backends.result import FlowStepResult
from dflow.backends.synthesis import run_synthesis
from dflow.backends.synthesis import yosys as synthesis_backend


def test_yosys_synthesis_builds_netlist_command(monkeypatch, tmp_path):
    rtl_source = tmp_path / "rtl" / "top.v"
    rtl_source.parent.mkdir()
    rtl_source.write_text("module top; endmodule\n", encoding="utf-8")
    stale_output = tmp_path / "build" / "synthesis" / "old.json"
    stale_output.parent.mkdir(parents=True)
    stale_output.write_text("stale\n", encoding="utf-8")
    captured_command: list[str] = []

    monkeypatch.setattr(
        synthesis_backend,
        "is_tool_available",
        lambda tool_name: True,
    )

    def fake_run(command, project_root, step_name, env=None):
        captured_command.extend(command)
        return FlowStepResult(step_name, command, 0, "synthesis output\n")

    monkeypatch.setattr(synthesis_backend, "run_flow_command", fake_run)

    result = synthesis_backend.run_yosys_synthesis(
        tmp_path,
        {
            "synthesis": {
                "tool": "yosys",
                "top": "top",
                "options": ["-Q"],
            }
        },
    )

    assert result is not None
    assert result.returncode == 0
    assert captured_command[:3] == ["yosys", "-Q", "-p"]
    script = captured_command[3]
    assert f'read_verilog -sv "{rtl_source}"' in script
    assert "synth -top top" in script
    assert 'write_verilog -noattr' in script
    assert 'netlist.v"' in script
    assert 'write_json' in script
    assert 'netlist.json"' in script
    assert not stale_output.exists()
    assert (tmp_path / "build" / "synthesis").is_dir()


def test_yosys_synthesis_uses_auto_top_when_top_is_not_configured(
    monkeypatch,
    tmp_path,
):
    rtl_source = tmp_path / "rtl" / "top.v"
    rtl_source.parent.mkdir()
    rtl_source.write_text("module top; endmodule\n", encoding="utf-8")
    captured_command: list[str] = []

    monkeypatch.setattr(
        synthesis_backend,
        "is_tool_available",
        lambda tool_name: True,
    )

    def fake_run(command, project_root, step_name, env=None):
        captured_command.extend(command)
        return FlowStepResult(step_name, command, 0)

    monkeypatch.setattr(synthesis_backend, "run_flow_command", fake_run)

    synthesis_backend.run_yosys_synthesis(
        tmp_path,
        {"synthesis": {"tool": "yosys"}},
    )

    assert "synth -auto-top" in captured_command[2]


def test_yosys_synthesis_requires_rtl_sources(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(
        synthesis_backend,
        "is_tool_available",
        lambda tool_name: True,
    )

    result = synthesis_backend.run_yosys_synthesis(
        tmp_path,
        {"synthesis": {"tool": "yosys"}},
    )

    assert result is None
    assert capsys.readouterr().out == (
        f"No RTL sources were found under {tmp_path / 'rtl'}.\n"
    )


def test_yosys_synthesis_requires_yosys(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(
        synthesis_backend,
        "is_tool_available",
        lambda tool_name: False,
    )

    result = synthesis_backend.run_yosys_synthesis(
        tmp_path,
        {"synthesis": {"tool": "yosys"}},
    )

    assert result is None
    assert capsys.readouterr().out == (
        "yosys is required for synthesis but was not found on PATH.\n"
    )


def test_yosys_synthesis_preserves_tool_failure(monkeypatch, tmp_path):
    rtl_source = tmp_path / "rtl" / "top.v"
    rtl_source.parent.mkdir()
    rtl_source.write_text("module top; endmodule\n", encoding="utf-8")

    monkeypatch.setattr(
        synthesis_backend,
        "is_tool_available",
        lambda tool_name: True,
    )
    monkeypatch.setattr(
        synthesis_backend,
        "run_flow_command",
        lambda command, project_root, step_name: FlowStepResult(
            step_name,
            command,
            4,
            stderr="synthesis failed\n",
        ),
    )

    result = synthesis_backend.run_yosys_synthesis(
        tmp_path,
        {"synthesis": {"tool": "yosys", "top": "top"}},
    )

    assert result is not None
    assert result.returncode == 4
    assert result.steps[0].stderr == "synthesis failed\n"


def test_synthesis_requires_a_configured_tool(tmp_path, capsys):
    result = run_synthesis(tmp_path, {})

    assert result is None
    assert capsys.readouterr().out == (
        f"No synthesis tool is configured in {tmp_path / 'flow.yaml'}.\n"
    )
