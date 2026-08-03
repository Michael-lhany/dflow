from dflow.backends import verilator as shared_backend
from dflow.backends.compile import verilator as compile_backend
from dflow.backends.result import FlowStepResult


def test_compile_writes_verilator_output_under_sim(monkeypatch, tmp_path):
    rtl_source = tmp_path / "rtl" / "top.v"
    rtl_source.parent.mkdir()
    rtl_source.write_text("module top; endmodule\n", encoding="utf-8")
    captured_command: list[str] = []

    monkeypatch.setattr(
        shared_backend,
        "is_tool_available",
        lambda tool_name: True,
    )

    def fake_run(command, project_root, step_name, env=None):
        captured_command.extend(command)
        return FlowStepResult(step_name, command, 0)

    monkeypatch.setattr(shared_backend, "run_flow_command", fake_run)

    result = compile_backend.run_verilator_compile(
        tmp_path,
        {"compile": {"tool": "verilator"}},
    )

    output_directory = tmp_path / "sim" / "compile_obj_dir"
    assert result is not None
    assert captured_command == [
        "verilator",
        "--cc",
        "--Mdir",
        str(output_directory),
        str(rtl_source),
    ]
    assert output_directory.is_dir()
    assert not (tmp_path / "obj_dir").exists()
