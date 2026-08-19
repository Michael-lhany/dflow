from pathlib import Path

from dflow.backends.formal import run_formal
from dflow.backends.formal import symbiyosys as sby_module
from dflow.backends.result import FlowStepResult


def test_symbiyosys_builds_timestamped_task_command(monkeypatch, tmp_path):
    config_path = tmp_path / "formal" / "counter.sby"
    config_path.parent.mkdir()
    config_path.write_text("[options]\nmode prove\n", encoding="utf-8")
    captured: dict = {}

    monkeypatch.setattr(sby_module, "is_tool_available", lambda tool: True)

    def fake_run(command, project_root, step_name, stream_output=False):
        captured["command"] = command
        captured["project_root"] = project_root
        captured["step_name"] = step_name
        captured["stream_output"] = stream_output
        return FlowStepResult(step_name, command, 0, "PASS\n")

    monkeypatch.setattr(sby_module, "run_flow_command", fake_run)
    result = run_formal(
        tmp_path,
        {
            "formal": {
                "tool": "sby",
                "config": "formal/counter.sby",
                "tasks": ["prove", "cover"],
                "options": ["-j", "2"],
            }
        },
    )

    assert result is not None
    assert result.returncode == 0
    assert result.tool_name == "sby"
    command = captured["command"]
    assert command[:3] == ["sby", "-j", "2"]
    assert command[3] == "--prefix"
    assert Path(command[4]).parent == tmp_path / "formal" / "runs"
    assert Path(command[4]).name.startswith("counter_")
    assert command[5:] == [str(config_path), "prove", "cover"]
    assert captured["project_root"] == tmp_path
    assert captured["stream_output"] is True
    assert (tmp_path / "formal" / "runs").is_dir()


def test_symbiyosys_accepts_explicit_executable(monkeypatch, tmp_path):
    executable = tmp_path / "tools" / "sby"
    executable.parent.mkdir()
    executable.write_text("#!/bin/sh\n", encoding="utf-8")
    executable.chmod(0o755)
    config_path = tmp_path / "formal" / "job.sby"
    config_path.parent.mkdir()
    config_path.write_text("[options]\nmode prove\n", encoding="utf-8")
    commands: list[list[str]] = []

    def fake_run(command, project_root, step_name, stream_output=False):
        commands.append(command)
        return FlowStepResult(step_name, command, 0)

    monkeypatch.setattr(sby_module, "run_flow_command", fake_run)
    result = run_formal(
        tmp_path,
        {
            "formal": {
                "tool": "symbiyosys",
                "executable": str(executable),
                "config": str(config_path),
            }
        },
    )

    assert result is not None
    assert commands[0][0] == str(executable)


def test_symbiyosys_reports_missing_config(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(sby_module, "is_tool_available", lambda tool: True)

    result = run_formal(
        tmp_path,
        {"formal": {"tool": "sby", "config": "formal/missing.sby"}},
    )

    assert result is None
    assert "SymbiYosys configuration was not found" in capsys.readouterr().out


def test_symbiyosys_rejects_invalid_tasks(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(sby_module, "is_tool_available", lambda tool: True)

    result = run_formal(
        tmp_path,
        {"formal": {"tool": "sby", "tasks": "prove"}},
    )

    assert result is None
    assert "formal.tasks must be a list" in capsys.readouterr().out


def test_formal_reports_unsupported_tool(tmp_path, capsys):
    result = run_formal(tmp_path, {"formal": {"tool": "other"}})

    assert result is None
    assert "Unsupported formal tool 'other'" in capsys.readouterr().out
