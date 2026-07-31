from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from dflow.backends.executor import run_flow_command
from dflow.backends.result import FlowRunResult
from dflow.config import get_flow_options, get_flow_section
from dflow.core.filesystem import create_directory
from dflow.core.project import find_rtl_sources, find_tb_sources
from dflow.utils import is_tool_available

DEFAULT_SIM_OPTIONS = [
	"--cc",
	"--exe",
	"--main",
	"--trace",
	"--timing",
]


def _build_simulation_output(prefix: str, output: str) -> str:
	if not output:
		return ""

	return f"{prefix}\n{output.rstrip()}\n"


def run_verilator_simulation(project_root: Path, flow_config: dict) -> FlowRunResult | None:
	"""Run Verilator simulation against the project's RTL and testbench sources."""
	simulation_tool = "verilator"

	if not is_tool_available(simulation_tool):
		print(f"{simulation_tool} is required for simulation but was not found on PATH.")
		return None

	rtl_sources = find_rtl_sources(project_root)
	tb_sources = find_tb_sources(project_root)

	if not rtl_sources:
		print(f"No RTL sources were found under {project_root / 'rtl'}.")
		return None

	if not tb_sources:
		print(f"No testbench sources were found under {project_root / 'tb'}.")
		return None

	simulation_section = get_flow_section(flow_config, "simulation")
	top_module = simulation_section.get("top") if isinstance(simulation_section.get("top"), str) else None

	if not top_module:
		if len(tb_sources) == 1:
			top_module = tb_sources[0].stem
		else:
			print(f"No simulation top module is configured in {project_root / 'flow.yaml'}.")
			return None

	simulation_options = get_flow_options(flow_config, "simulation", DEFAULT_SIM_OPTIONS)
	sim_obj_dir = project_root / "sim" / "obj_dir"
	if sim_obj_dir.exists():
		shutil.rmtree(sim_obj_dir)
	create_directory(sim_obj_dir)
	build_command = [
		simulation_tool,
		*simulation_options,
		"--Mdir",
		str(sim_obj_dir),
		"--top-module",
		top_module,
		*[str(source_path) for source_path in rtl_sources],
		*[str(source_path) for source_path in tb_sources],
	]
	build_result = run_flow_command(build_command, project_root, simulation_tool)

	if build_result.returncode != 0:
		return build_result

	simulation_binary = sim_obj_dir / f"V{top_module}"
	build_make_command = [
		"make",
		"-C",
		str(sim_obj_dir),
		"-f",
		f"V{top_module}.mk",
		"CXX=clang++",
		"LINK=clang++",
		"CXXFLAGS=-std=c++20 -stdlib=libc++ -I/usr/lib/llvm-18/include/c++/v1",
		"LDFLAGS=-stdlib=libc++ -L/usr/lib/llvm-18/lib",
	]
	make_result = run_flow_command(build_make_command, project_root, "make")

	if make_result.returncode != 0:
		combined_stdout = "".join(
			[
				_build_simulation_output("=== Verilator Build Output ===", build_result.stdout),
				_build_simulation_output("=== Make Output ===", make_result.stdout),
			]
		)
		combined_stderr = "".join(
			[
				_build_simulation_output("=== Verilator Build Errors ===", build_result.stderr),
				_build_simulation_output("=== Make Errors ===", make_result.stderr),
			]
		)
		return FlowRunResult(
			tool_name=simulation_tool,
			command=build_command,
			returncode=make_result.returncode,
			stdout=combined_stdout,
			stderr=combined_stderr,
		)

	if not simulation_binary.exists():
		print(f"Expected simulation binary was not found at {simulation_binary}.")
		return FlowRunResult(
			tool_name=simulation_tool,
			command=build_command,
			returncode=1,
			stdout="".join(
				[
					_build_simulation_output("=== Verilator Build Output ===", build_result.stdout),
					_build_simulation_output("=== Make Output ===", make_result.stdout),
				]
			),
			stderr="".join(
				[
					_build_simulation_output("=== Verilator Build Errors ===", build_result.stderr),
					_build_simulation_output("=== Make Errors ===", make_result.stderr),
				]
			),
		)

	run_result = subprocess.run(
		[str(simulation_binary)],
		cwd=project_root,
		text=True,
		capture_output=True,
	)

	stdout = "".join(
		[
			_build_simulation_output("=== Verilator Build Output ===", build_result.stdout),
			_build_simulation_output("=== Make Output ===", make_result.stdout),
			_build_simulation_output("=== Simulation Output ===", run_result.stdout),
		]
	)
	stderr = "".join(
		[
			_build_simulation_output("=== Verilator Build Errors ===", build_result.stderr),
			_build_simulation_output("=== Make Errors ===", make_result.stderr),
			_build_simulation_output("=== Simulation Errors ===", run_result.stderr),
		]
	)

	return FlowRunResult(
		tool_name=simulation_tool,
		command=build_command,
		returncode=run_result.returncode,
		stdout=stdout,
		stderr=stderr,
	)