import sys

from typer.testing import CliRunner

from dflow import gui as gui_module
from dflow.cli import app


def test_build_cli_command_adds_tool_arguments_after_separator():
    command = gui_module.build_cli_command(
        "lint", '-Wall --Wno-fatal --top-module "counter tb"'
    )

    assert command == [
        sys.executable,
        "-m",
        "dflow.cli",
        "lint",
        "--",
        "-Wall",
        "--Wno-fatal",
        "--top-module",
        "counter tb",
    ]


def test_build_cli_command_ignores_tool_arguments_for_other_commands():
    assert gui_module.build_cli_command("doctor", "--unused") == [
        sys.executable,
        "-m",
        "dflow.cli",
        "doctor",
    ]


def test_build_cli_command_adds_synthesis_arguments():
    assert gui_module.build_cli_command("synth", "-Q -q")[-3:] == [
        "--",
        "-Q",
        "-q",
    ]


def test_build_cli_command_places_command_arguments_before_tool_separator():
    assert gui_module.build_cli_command(
        "sim",
        "--threads 4",
        ["--wave"],
    ) == [
        sys.executable,
        "-m",
        "dflow.cli",
        "sim",
        "--wave",
        "--",
        "--threads",
        "4",
    ]


def test_build_cli_command_can_open_wave_without_tool_arguments():
    assert gui_module.build_cli_command(
        "sim",
        "",
        ["--wave-only"],
    ) == [
        sys.executable,
        "-m",
        "dflow.cli",
        "sim",
        "--wave-only",
    ]


def test_gui_command_launches_interface(monkeypatch):
    launched = False

    def fake_launch_gui():
        nonlocal launched
        launched = True

    monkeypatch.setattr(gui_module, "launch_gui", fake_launch_gui)
    result = CliRunner().invoke(app, ["gui"])

    assert result.exit_code == 0
    assert launched


def test_gui_command_reports_when_display_cannot_open(monkeypatch):
    def fail_to_launch():
        raise RuntimeError("No graphical display.")

    monkeypatch.setattr(gui_module, "launch_gui", fail_to_launch)
    result = CliRunner().invoke(app, ["gui"])

    assert result.exit_code == 1
    assert result.stdout == "No graphical display.\n"
