from typer.testing import CliRunner

from dflow.cli import app
from dflow.commands import doctor as doctor_module


def test_placeholder_commands_explain_they_are_not_implemented():
    runner = CliRunner()

    clean_result = runner.invoke(app, ["clean"])
    status_result = runner.invoke(app, ["status"])

    assert clean_result.exit_code == 0
    assert clean_result.stdout == "Clean is not implemented yet.\n"
    assert status_result.exit_code == 0
    assert status_result.stdout == "Status is not implemented yet.\n"


def test_doctor_checks_each_unique_tool_once(monkeypatch, tmp_path, capsys):
    checks: list[str] = []
    flow_config = {
        "compile": {"tool": "verilator"},
        "lint": {"tool": "verilator"},
        "simulation": {"tool": "verilator"},
        "synthesis": {"tool": "yosys"},
    }

    monkeypatch.setattr(doctor_module, "find_project_root", lambda: tmp_path)
    monkeypatch.setattr(
        doctor_module,
        "load_flow_config",
        lambda project_root: flow_config,
    )

    def fake_is_tool_available(tool_name: str) -> bool:
        checks.append(tool_name)
        return True

    monkeypatch.setattr(
        doctor_module,
        "is_tool_available",
        fake_is_tool_available,
    )

    doctor_module.doctor()

    assert checks == ["verilator", "yosys"]
    assert capsys.readouterr().out.splitlines() == [
        "verilator: found",
        "yosys: found",
        "All required tools are available.",
    ]
