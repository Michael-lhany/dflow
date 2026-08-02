from typer.testing import CliRunner

from dflow.backends.result import FlowRunResult, FlowStepResult
from dflow.cli import app
from dflow.commands import clean as clean_module
from dflow.commands import doctor as doctor_module
from dflow.commands import lint as lint_module
from dflow.config import get_flow_options
from dflow.core.project import PROJECT_MARKER


def test_clean_removes_generated_artifacts(tmp_path, monkeypatch):
    project_root = tmp_path
    (project_root / PROJECT_MARKER).write_text("version: 0.1.0\n", encoding="utf-8")
    (project_root / "flow.yaml").write_text("project: {}\n", encoding="utf-8")
    rtl_source = project_root / "rtl" / "top.v"
    rtl_source.parent.mkdir()
    rtl_source.write_text("module top; endmodule\n", encoding="utf-8")

    removable_paths = [
        project_root / "obj_dir",
        project_root / "sim" / "obj_dir",
        project_root / "sim" / "logs",
    ]
    preserved_directories = [
        project_root / "reports",
        project_root / "sim" / "waves",
    ]
    for path in [*removable_paths, *preserved_directories]:
        path.mkdir(parents=True)
        (path / "artifact.txt").write_text("generated\n", encoding="utf-8")

    nested_directory = project_root / "rtl" / "nested"
    nested_directory.mkdir()
    monkeypatch.chdir(nested_directory)
    runner = CliRunner()
    result = runner.invoke(app, ["clean"], catch_exceptions=False)

    assert result.exit_code == 0
    assert result.stdout.splitlines() == [
        "Removed obj_dir",
        "Removed sim/obj_dir",
        "Removed sim/logs",
        "Cleared reports",
        "Cleared sim/waves",
    ]
    assert not any(path.exists() for path in removable_paths)
    assert all(path.is_dir() and not any(path.iterdir()) for path in preserved_directories)
    assert rtl_source.exists()
    assert (project_root / PROJECT_MARKER).exists()
    assert (project_root / "flow.yaml").exists()


def test_clean_reports_when_nothing_exists(tmp_path, monkeypatch):
    runner = CliRunner()

    (tmp_path / PROJECT_MARKER).write_text("version: 0.1.0\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["clean"], catch_exceptions=False)

    assert result.exit_code == 0
    assert result.stdout == "Nothing to clean.\n"


def test_clean_dry_run_does_not_remove_artifacts(tmp_path, monkeypatch):
    (tmp_path / PROJECT_MARKER).write_text("version: 0.1.0\n", encoding="utf-8")
    artifact = tmp_path / "obj_dir" / "artifact.txt"
    artifact.parent.mkdir()
    artifact.write_text("generated\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["clean", "--dry-run"])

    assert result.exit_code == 0
    assert result.stdout == "Would remove obj_dir\n"
    assert artifact.exists()


def test_clean_refuses_to_follow_parent_symlink(tmp_path, monkeypatch):
    project_root = tmp_path / "project"
    external_root = tmp_path / "external"
    project_root.mkdir()
    external_root.mkdir()
    (project_root / PROJECT_MARKER).write_text("version: 0.1.0\n", encoding="utf-8")
    external_artifact = external_root / "obj_dir" / "artifact.txt"
    external_artifact.parent.mkdir()
    external_artifact.write_text("keep\n", encoding="utf-8")
    (project_root / "sim").symlink_to(external_root, target_is_directory=True)

    monkeypatch.chdir(project_root)
    result = CliRunner().invoke(app, ["clean"])

    assert result.exit_code == 1
    assert "Failed to clean sim/obj_dir" in result.output
    assert external_artifact.exists()


def test_clean_unlinks_dangling_generated_symlink(tmp_path, monkeypatch):
    (tmp_path / PROJECT_MARKER).write_text("version: 0.1.0\n", encoding="utf-8")
    generated_symlink = tmp_path / "obj_dir"
    generated_symlink.symlink_to(tmp_path / "missing", target_is_directory=True)

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["clean"])

    assert result.exit_code == 0
    assert result.stdout == "Removed obj_dir\n"
    assert not generated_symlink.is_symlink()


def test_clean_continues_after_removal_failure(tmp_path, monkeypatch):
    (tmp_path / PROJECT_MARKER).write_text("version: 0.1.0\n", encoding="utf-8")
    (tmp_path / "obj_dir").mkdir()
    simulation_object_directory = tmp_path / "sim" / "obj_dir"
    simulation_object_directory.mkdir(parents=True)
    real_remove_path = clean_module.remove_path

    def fail_for_root_object_directory(path, allowed_root):
        if path == tmp_path / "obj_dir":
            raise PermissionError("denied")
        return real_remove_path(path, allowed_root)

    monkeypatch.setattr(clean_module, "remove_path", fail_for_root_object_directory)
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["clean"])

    assert result.exit_code == 1
    assert "Failed to clean obj_dir: denied" in result.output
    assert (tmp_path / "obj_dir").exists()
    assert not simulation_object_directory.exists()


def test_lint_appends_cli_tool_options(tmp_path, monkeypatch):
    (tmp_path / PROJECT_MARKER).write_text("version: 0.1.0\n", encoding="utf-8")
    (tmp_path / "flow.yaml").write_text(
        "lint:\n    tool: verilator\n",
        encoding="utf-8",
    )
    captured_options: list[str] = []

    def fake_run_lint(project_root, flow_config):
        captured_options.extend(
            get_flow_options(flow_config, "lint", ["--lint-only"])
        )
        return FlowRunResult(
            tool_name="verilator",
            steps=[
                FlowStepResult(
                    name="Verilator lint",
                    command=["verilator", *captured_options],
                    returncode=0,
                )
            ],
        )

    monkeypatch.setattr(lint_module, "run_lint", fake_run_lint)
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(
        app,
        ["lint", "--", "-Wall", "--Wno-fatal"],
    )

    assert result.exit_code == 0
    assert captured_options == ["--lint-only", "-Wall", "--Wno-fatal"]



def test_placeholder_commands_explain_they_are_not_implemented():
    runner = CliRunner()

    status_result = runner.invoke(app, ["status"])

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
