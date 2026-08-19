import sys

import pytest
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


def test_build_cli_command_adds_asic_arguments():
    assert gui_module.build_cli_command("asic", "--condensed")[-2:] == [
        "--",
        "--condensed",
    ]


def test_build_cli_command_adds_formal_arguments():
    assert gui_module.build_cli_command(
        "formal",
        "-j 4 --live jsonl",
        ["--task", "prove"],
    )[-7:] == [
        "--task",
        "prove",
        "--",
        "-j",
        "4",
        "--live",
        "jsonl",
    ]


def test_build_formal_invocation_combines_page_controls():
    arguments, options = gui_module.build_formal_invocation(
        config="formal/counter.sby",
        tasks="prove cover",
        jobs="3",
        sequential=True,
        live_status=True,
        extra_options="--autotune",
    )

    assert arguments == [
        "--config",
        "formal/counter.sby",
        "--task",
        "prove",
        "--task",
        "cover",
    ]
    assert options == "-j 3 --sequential --live jsonl --autotune"


@pytest.mark.parametrize("jobs", ["0", "-2", "many"])
def test_build_formal_invocation_rejects_invalid_jobs(jobs):
    with pytest.raises(ValueError, match="positive integer"):
        gui_module.build_formal_invocation(jobs=jobs)


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


def test_build_asic_tool_options_combines_page_controls():
    assert gui_module.build_asic_tool_options(
        condensed=True,
        jobs="4",
        start_step="Yosys.Synthesis",
        end_step="OpenROAD.GeneratePDN",
        extra_options='--run-tag "floorplan test"',
    ) == (
        "--condensed -j 4 --from Yosys.Synthesis --to "
        "OpenROAD.GeneratePDN --run-tag 'floorplan test'"
    )


@pytest.mark.parametrize("jobs", ["0", "-1", "four"])
def test_build_asic_tool_options_rejects_invalid_jobs(jobs):
    with pytest.raises(ValueError, match="positive integer"):
        gui_module.build_asic_tool_options(
            condensed=False,
            jobs=jobs,
        )


def test_build_clean_arguments_uses_only_for_partial_selection():
    assert gui_module.build_clean_arguments(
        ["simulation", "waveforms"],
        dry_run=True,
    ) == [
        "--dry-run",
        "--only",
        "simulation",
        "--only",
        "waveforms",
    ]


def test_build_clean_arguments_uses_default_for_all_categories():
    assert gui_module.build_clean_arguments(
        list(gui_module.CLEAN_CATEGORIES),
    ) == []


def test_build_clean_arguments_requires_a_selection():
    with pytest.raises(ValueError, match="at least one"):
        gui_module.build_clean_arguments([])


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
