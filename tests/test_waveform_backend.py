import os

from dflow.backends.waveform import gtkwave as waveform_backend
from dflow.backends.waveform import open_latest_waveform
from dflow.backends.waveform import verdi as verdi_backend


def test_open_latest_waveform_launches_gtkwave(monkeypatch, tmp_path, capsys):
    older = tmp_path / "sim" / "waves" / "older.vcd"
    newer = tmp_path / "sim" / "waves" / "nested" / "newer.vcd"
    older.parent.mkdir(parents=True)
    newer.parent.mkdir(parents=True)
    older.write_text("old\n", encoding="utf-8")
    newer.write_text("new\n", encoding="utf-8")
    os.utime(older, ns=(1_000_000, 1_000_000))
    os.utime(newer, ns=(2_000_000, 2_000_000))
    monkeypatch.setattr(
        waveform_backend,
        "is_tool_available",
        lambda tool_name: tool_name == "gtkwave",
    )
    launched = {}

    def fake_popen(command, **kwargs):
        launched["command"] = command
        launched["kwargs"] = kwargs
        return object()

    monkeypatch.setattr(waveform_backend.subprocess, "Popen", fake_popen)

    assert waveform_backend.open_latest_waveform(tmp_path)
    assert launched["command"] == ["gtkwave", str(newer)]
    assert launched["kwargs"]["cwd"] == tmp_path
    assert launched["kwargs"]["start_new_session"] is True
    assert capsys.readouterr().out == (
        "Opening sim/waves/nested/newer.vcd with GTKWave.\n"
    )


def test_open_latest_waveform_reports_missing_vcd(tmp_path, capsys):
    assert not waveform_backend.open_latest_waveform(tmp_path)
    assert "No VCD waveform was found" in capsys.readouterr().out


def test_open_latest_waveform_ignores_stale_vcd(tmp_path, capsys):
    waveform = tmp_path / "sim" / "waves" / "stale.vcd"
    waveform.parent.mkdir(parents=True)
    waveform.write_text("stale\n", encoding="utf-8")
    os.utime(waveform, ns=(1_000_000, 1_000_000))

    assert not waveform_backend.open_latest_waveform(
        tmp_path,
        modified_since_ns=2_000_000,
    )
    assert "No new VCD waveform was generated" in capsys.readouterr().out


def test_open_latest_waveform_reports_missing_gtkwave(
    monkeypatch,
    tmp_path,
    capsys,
):
    waveform = tmp_path / "sim" / "waves" / "top.vcd"
    waveform.parent.mkdir(parents=True)
    waveform.write_text("wave\n", encoding="utf-8")
    monkeypatch.setattr(
        waveform_backend,
        "is_tool_available",
        lambda tool_name: False,
    )

    assert not waveform_backend.open_latest_waveform(tmp_path)
    assert "GTKWave is required for --wave" in capsys.readouterr().out


def test_waveform_dispatcher_launches_verdi_for_newest_supported_file(
    monkeypatch,
    tmp_path,
    capsys,
):
    older_fsdb = tmp_path / "sim" / "waves" / "older.fsdb"
    fsdb = tmp_path / "sim" / "waves" / "newer.fsdb"
    older_fsdb.parent.mkdir(parents=True)
    older_fsdb.write_text("fsdb\n", encoding="utf-8")
    fsdb.write_text("fsdb\n", encoding="utf-8")
    os.utime(older_fsdb, ns=(1_000_000, 1_000_000))
    os.utime(fsdb, ns=(2_000_000, 2_000_000))
    monkeypatch.setattr(verdi_backend, "is_tool_available", lambda tool: True)
    launched = {}

    def fake_popen(command, **kwargs):
        launched["command"] = command
        launched["kwargs"] = kwargs
        return object()

    monkeypatch.setattr(verdi_backend.subprocess, "Popen", fake_popen)
    assert open_latest_waveform(
        tmp_path,
        flow_config={"waveform": {"tool": "verdi"}},
    )
    assert launched["command"] == ["verdi", "-ssf", str(fsdb)]
    assert launched["kwargs"]["cwd"] == tmp_path
    assert launched["kwargs"]["start_new_session"] is True
    assert capsys.readouterr().out == "Opening sim/waves/newer.fsdb with Verdi.\n"


def test_waveform_dispatcher_launches_verdi_for_vcd(
    monkeypatch,
    tmp_path,
    capsys,
):
    older_fsdb = tmp_path / "sim" / "waves" / "older.fsdb"
    vcd = tmp_path / "sim" / "waves" / "newer.vcd"
    older_fsdb.parent.mkdir(parents=True)
    older_fsdb.write_text("fsdb\n", encoding="utf-8")
    vcd.write_text("vcd\n", encoding="utf-8")
    os.utime(older_fsdb, ns=(1_000_000, 1_000_000))
    os.utime(vcd, ns=(2_000_000, 2_000_000))
    monkeypatch.setattr(verdi_backend, "is_tool_available", lambda tool: True)
    launched = {}

    def fake_popen(command, **kwargs):
        launched["command"] = command
        return object()

    monkeypatch.setattr(verdi_backend.subprocess, "Popen", fake_popen)

    assert open_latest_waveform(
        tmp_path,
        flow_config={"waveform": {"tool": "verdi"}},
    )
    assert launched["command"] == ["verdi", "-ssf", str(vcd)]
    assert capsys.readouterr().out == "Opening sim/waves/newer.vcd with Verdi.\n"


def test_waveform_dispatcher_defaults_to_gtkwave(monkeypatch, tmp_path):
    waveform = tmp_path / "sim" / "waves" / "top.vcd"
    waveform.parent.mkdir(parents=True)
    waveform.write_text("wave\n", encoding="utf-8")
    monkeypatch.setattr(waveform_backend, "is_tool_available", lambda tool: True)
    launched = {}

    def fake_popen(command, **kwargs):
        launched["command"] = command
        return object()

    monkeypatch.setattr(waveform_backend.subprocess, "Popen", fake_popen)
    assert open_latest_waveform(tmp_path, flow_config={})
    assert launched["command"] == ["gtkwave", str(waveform)]
