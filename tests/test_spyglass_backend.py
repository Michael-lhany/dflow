from dflow.backends.lint import run_lint
from dflow.backends.lint import spyglass as spyglass_backend
from dflow.backends.result import FlowStepResult


def test_spyglass_generates_project_and_runs_default_goal(monkeypatch, tmp_path):
    rtl_source = tmp_path / "rtl" / "top.sv"
    rtl_source.parent.mkdir()
    rtl_source.write_text("module top; endmodule\n", encoding="utf-8")
    captured_command: list[str] = []

    monkeypatch.setattr(
        spyglass_backend, "is_tool_available", lambda tool_name: True
    )

    def fake_run(command, project_root, step_name, env=None):
        captured_command.extend(command)
        return FlowStepResult(step_name, command, 0)

    monkeypatch.setattr(spyglass_backend, "run_flow_command", fake_run)

    result = run_lint(
        tmp_path,
        {
            "lint": {
                "tool": "spyglass",
                "top": "top",
                "options": ["-64bit"],
            }
        },
    )

    project_file = tmp_path / "build" / "lint" / "spyglass" / "dflow.prj"
    assert result is not None
    assert result.tool_name == "spyglass"
    assert captured_command == [
        "spyglass",
        "-64bit",
        "-batch",
        "-project",
        str(project_file),
        "-goals",
        "lint/lint_rtl",
    ]
    project_text = project_file.read_text(encoding="utf-8")
    assert "set_option enableSV yes" in project_text
    assert f"read_file -type verilog {{{rtl_source}}}" in project_text
    assert "set_option top {top}" in project_text


def test_spyglass_accepts_maintained_project_and_custom_goal(
    monkeypatch, tmp_path
):
    project_file = tmp_path / "scripts" / "lint.prj"
    project_file.parent.mkdir()
    project_file.write_text("set_option top top\n", encoding="utf-8")
    captured_command: list[str] = []

    monkeypatch.setattr(
        spyglass_backend, "is_tool_available", lambda tool_name: True
    )
    monkeypatch.setattr(
        spyglass_backend,
        "run_flow_command",
        lambda command, project_root, step_name: (
            captured_command.extend(command)
            or FlowStepResult(step_name, command, 0)
        ),
    )

    result = spyglass_backend.run_spyglass_lint(
        tmp_path,
        {
            "lint": {
                "tool": "spyglass",
                "project": "scripts/lint.prj",
                "goal": "lint/lint_turbo_rtl",
            }
        },
    )

    assert result is not None
    assert str(project_file) in captured_command
    assert captured_command[-1] == "lint/lint_turbo_rtl"
    assert project_file.is_file()


def test_spyglass_rejects_missing_project_before_cleaning(
    monkeypatch, tmp_path, capsys
):
    stale_output = tmp_path / "build" / "lint" / "spyglass" / "keep.txt"
    stale_output.parent.mkdir(parents=True)
    stale_output.write_text("keep\n", encoding="utf-8")
    monkeypatch.setattr(
        spyglass_backend, "is_tool_available", lambda tool_name: True
    )

    result = spyglass_backend.run_spyglass_lint(
        tmp_path,
        {"lint": {"tool": "spyglass", "project": "scripts/missing.prj"}},
    )

    assert result is None
    assert "SpyGlass project file was not found" in capsys.readouterr().out
    assert stale_output.is_file()


def test_spyglass_requires_executable(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(
        spyglass_backend, "is_tool_available", lambda tool_name: False
    )

    result = spyglass_backend.run_spyglass_lint(
        tmp_path, {"lint": {"tool": "spyglass"}}
    )

    assert result is None
    assert capsys.readouterr().out == (
        "spyglass is required for lint but was not found on PATH.\n"
    )
