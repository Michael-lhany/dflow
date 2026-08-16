from dflow.backends.asic import openlane as openlane_backend


def _write_openlane_config(project_root):
    config_path = project_root / "openlane" / "config.json"
    config_path.parent.mkdir(parents=True)
    config_path.write_text('{"DESIGN_NAME": "top"}\n', encoding="utf-8")
    return config_path


def test_openlane_runs_direct_executable(monkeypatch, tmp_path):
    config_path = _write_openlane_config(tmp_path)
    captured = {}
    flow_config = {
        "asic": {
            "tool": "openlane",
            "config": "openlane/config.json",
            "flow": "Classic",
            "pdk": "sky130A",
            "options": ["--condensed"],
        }
    }

    monkeypatch.setattr(
        openlane_backend,
        "is_tool_available",
        lambda tool_name: tool_name == "openlane",
    )

    def fake_run(command, project_root, step_name, stream_output=False):
        captured["command"] = command
        captured["project_root"] = project_root
        captured["step_name"] = step_name
        captured["stream_output"] = stream_output
        from dflow.backends.result import FlowStepResult

        return FlowStepResult(step_name, command, 0)

    monkeypatch.setattr(openlane_backend, "run_flow_command", fake_run)

    result = openlane_backend.run_openlane(tmp_path, flow_config)

    assert result is not None
    assert result.returncode == 0
    assert captured["command"] == [
        "openlane",
        "--condensed",
        "--flow",
        "Classic",
        "--pdk",
        "sky130A",
        str(config_path),
    ]
    assert captured["project_root"] == tmp_path
    assert captured["step_name"] == "OpenLane ASIC flow"
    assert captured["stream_output"] is True


def test_openlane_uses_configured_nix_flake(monkeypatch, tmp_path):
    config_path = _write_openlane_config(tmp_path)
    openlane_root = tmp_path / "tools" / "openlane2"
    openlane_root.mkdir(parents=True)
    (openlane_root / "flake.nix").write_text("{}\n", encoding="utf-8")
    flow_config = {
        "asic": {
            "tool": "openlane",
            "openlane_root": str(openlane_root),
        }
    }
    captured_commands = []

    monkeypatch.setattr(
        openlane_backend,
        "is_tool_available",
        lambda tool_name: tool_name == "nix",
    )

    def fake_run(command, project_root, step_name, stream_output=False):
        captured_commands.append(command)
        assert stream_output is True
        from dflow.backends.result import FlowStepResult

        return FlowStepResult(step_name, command, 0)

    monkeypatch.setattr(openlane_backend, "run_flow_command", fake_run)

    result = openlane_backend.run_openlane(tmp_path, flow_config)

    assert result is not None
    assert captured_commands == [[
        "nix",
        "develop",
        f"{openlane_root}#default",
        "--command",
        "openlane",
        str(config_path),
    ]]


def test_openlane_uses_configured_executable(monkeypatch, tmp_path):
    executable = tmp_path / "tools" / "openlane"
    executable.parent.mkdir(parents=True)
    executable.write_text("#!/bin/sh\n", encoding="utf-8")
    executable.chmod(0o755)
    flow_config = {
        "asic": {
            "tool": "openlane",
            "executable": str(executable),
        }
    }

    assert openlane_backend.resolve_openlane_command(
        tmp_path,
        flow_config,
    ) == [str(executable)]


def test_openlane_reports_missing_design_config(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(
        openlane_backend,
        "is_tool_available",
        lambda tool_name: tool_name == "openlane",
    )

    assert openlane_backend.run_openlane(
        tmp_path,
        {"asic": {"tool": "openlane"}},
    ) is None
    assert "OpenLane design config was not found" in capsys.readouterr().out
