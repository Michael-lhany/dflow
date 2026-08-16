from dflow.backends import executor


def test_streaming_command_prints_and_captures_output(
    monkeypatch,
    tmp_path,
    capsys,
):
    class FakeProcess:
        stdout = iter(["first line\n", "second line\n"])

        def wait(self):
            return 3

    monkeypatch.setattr(
        executor.subprocess,
        "Popen",
        lambda *args, **kwargs: FakeProcess(),
    )

    result = executor.run_flow_command(
        ["tool"],
        tmp_path,
        "Streaming tool",
        stream_output=True,
    )

    assert result.returncode == 3
    assert result.stdout == "first line\nsecond line\n"
    assert result.output_streamed
    assert capsys.readouterr().out == result.stdout
