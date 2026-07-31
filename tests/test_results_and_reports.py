from dflow.backends.result import FlowRunResult, FlowStepResult
from dflow.core.project import save_flow_report


def test_flow_result_uses_final_step_return_code():
    result = FlowRunResult(
        tool_name="verilator",
        steps=[
            FlowStepResult("build", ["verilator"], 0),
            FlowStepResult("run", ["Vtop"], 7),
        ],
    )

    assert result.returncode == 7


def test_empty_flow_result_is_a_failure():
    assert FlowRunResult(tool_name="verilator", steps=[]).returncode == 1


def test_report_records_every_step(tmp_path):
    steps = [
        FlowStepResult(
            name="Verilator build",
            command=["verilator", "--cc", "rtl/top.v"],
            returncode=0,
            stdout="build output\n",
        ),
        FlowStepResult(
            name="Simulation",
            command=["sim/obj_dir/Vtop"],
            returncode=1,
            stderr="simulation failed\n",
        ),
    ]

    report_path = save_flow_report(
        tmp_path,
        "sim",
        "verilator",
        steps,
    )
    report = report_path.read_text(encoding="utf-8")

    assert "Step 1: Verilator build" in report
    assert "Command: verilator --cc rtl/top.v" in report
    assert "Step 2: Simulation" in report
    assert "Return code: 1" in report
    assert "simulation failed" in report
