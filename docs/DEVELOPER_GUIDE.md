# DFlow Developer Guide

**Project:** DFlow (Digital Design Flow Manager)

**Version:** 0.1.0

**Author:** Michael Hany

This guide documents the repository as currently implemented. Features described
as placeholders do not perform a real flow yet.

## 1. Purpose and Architecture

DFlow is an installable Python CLI that gives digital-design projects one
interface for EDA tasks. The current architecture is:

```text
User -> Typer command or Tkinter GUI -> project/config helpers -> backend dispatcher
     -> tool-specific backend -> external EDA process -> report
```

- `dflow/commands/` owns CLI orchestration, console output, exit codes, and
  report requests.
- `dflow/gui.py` provides a graphical launcher for the existing CLI commands.
- `dflow/core/` owns project creation, discovery, source discovery, and report
  persistence.
- `dflow/backends/` selects and runs tool implementations.
- `dflow/config.py` normalizes `flow.yaml` data.
- `dflow/utils.py` checks executable availability on `PATH`.

Compile, lint, and simulation have Verilator backends, and synthesis has a
Yosys backend with optional Liberty cell mapping. Clean removes generated
artifacts, while status summarizes project sources, flows, reports, and
generated artifacts.

## 2. Repository Layout

```text
.
├── AGENTS.md                         contributor instructions
├── README.md                         empty user-documentation placeholder
├── pyproject.toml                    package metadata and console entry point
├── docs/
│   ├── DEVELOPER_GUIDE.md            implementation reference
│   ├── VERILATOR_ARGUMENTS.md        categorized Verilator option reference
│   └── YOSYS_ARGUMENTS.md            Yosys and mapping option reference
├── tests/                            pytest suite
├── dflow/
│   ├── cli.py                        Typer application and registration
│   ├── gui.py                        Tkinter command launcher
│   ├── config.py                     flow.yaml accessors
│   ├── utils.py                      PATH checks
│   ├── logger.py                     empty placeholder
│   ├── version.py                    empty placeholder
│   ├── commands/                     commands and shared CLI lifecycle
│   ├── core/                         filesystem and project helpers
│   └── backends/
│       ├── executor.py               shared subprocess wrapper
│       ├── result.py                 flow and step result models
│       ├── verilator.py              shared RTL-stage runner
│       ├── compile/                  Verilator compile dispatcher/backend
│       ├── lint/                     Verilator lint dispatcher/backend
│       ├── simulation/               Verilator simulation dispatcher/backend
│       └── synthesis/                Yosys synthesis dispatcher/backend
└── Dflow_project_examples/counter/
    ├── .dflow
    ├── flow.yaml
    ├── rtl/counter.v
    ├── tb/counter_tb.sv
    └── sim/waves/counter.vcd
```

The top-level, command, and core `__init__.py` files are empty package markers;
the flow backend package initializers implement their dispatchers. `.gitignore`
excludes Python caches, virtual environments, editor state, pytest/build output,
`obj_dir/`, logs, reports, and OS metadata.

## 3. Packaging and Entry Point

`pyproject.toml` is the single dependency source. It uses
`setuptools.build_meta` with `setuptools>=61`; package discovery includes only
`dflow*`. Runtime dependencies are `typer` and `pyyaml`, while the optional
`dev` extra installs pytest. The installed console script is:

```toml
[project.scripts]
dflow = "dflow.cli:app"
```

`dflow/cli.py` is the only command-registration point. It registers, in order,
`init`, `compile`, `synth`, `lint`, `sim`, `status`, `doctor`, `clean`, and
`gui`.
It can also run directly through `python -m dflow.cli`. Install a development
checkout with `python -m pip install -e '.[dev]'`.
From the repository root, `source ./activate.sh` activates the existing `.venv`
and reports how to create it when it is missing.

## 4. Project Model

### Initialization

`dflow init <project_name>` calls `create_project()`. It creates the target and
the following directories with `parents=True, exist_ok=True`:

```text
rtl/  tb/  scripts/  constraints/  docs/  reports/
formal/  openlane/  sim/  sim/waves/
```

It writes `.dflow` containing `version: 0.1.0` and creates this default
configuration:

```yaml
project:
    name: <project_name>

compile:
    tool: verilator
    options: [--cc]

lint:
    tool: verilator
    options: [--lint-only, -Wall]

simulation:
    tool: verilator

synthesis:
    tool: yosys
```

The low-level `create_text_file()` helper writes UTF-8 text and overwrites an
existing file. Consequently, running `init` against an existing target can
replace its `.dflow` and `flow.yaml`; the command does not guard against that.

### Project and source discovery

`find_project_root()` resolves the starting path (the current working directory
by default) and walks through it and its parents until it finds `.dflow`. It
raises `FileNotFoundError` if no marker exists.

Source discovery is recursive and returns sorted paths:

- `find_rtl_sources()` accepts `.v`, `.sv`, and `.svh` under `rtl/`.
- `find_tb_sources()` accepts `.v`, `.sv`, `.svh`, `.cpp`, `.cc`, and `.cxx`
  under `tb/`.
- A missing source directory produces an empty list.

## 5. Configuration Semantics

`load_flow_config()` reads `<project-root>/flow.yaml` with `yaml.safe_load()`.
A missing or empty file becomes `{}`. Malformed YAML is not caught and propagates
the PyYAML exception.

The accessors behave as follows:

- `get_flow_section()` returns a section only when it is a mapping; otherwise
  it returns `{}`.
- `get_flow_tool()` returns a non-empty string or `None`.
- `get_flow_options()` accepts only a list and removes non-string or empty
  entries. Missing/non-list values use the backend default. An explicit empty
  list disables all default options. Tool arguments supplied on the CLI are
  appended after the configured or default options.

Recognized fields are:

| Section | Fields used | Current behavior |
| --- | --- | --- |
| `project` | `name` | Generated metadata; not otherwise consumed |
| `compile` | `tool`, `options` | Backend selection and Verilator arguments |
| `lint` | `tool`, `options` | Backend selection and Verilator arguments |
| `simulation` | `tool`, `options`, `top` | Backend, arguments, and top module |
| `synthesis` | `tool`, `options`, `top`, `liberty` | Yosys arguments, top, and optional cell library |

`synthesis.liberty` accepts an absolute path, a path relative to the project
root, `~`, and environment variables such as `${PDK_ROOT}`. The expanded path
must identify an existing file before synthesis starts.

## 6. Command Reference

### `dflow gui`

Opens the Tkinter interface. Select a project directory, optionally enter
temporary backend arguments, and run init, compile, lint, simulation,
synthesis, doctor, status, or clean from buttons. Commands run through
`python -m dflow.cli`, so the GUI uses the same configuration, backends,
reports, and exit codes as the terminal. Output is streamed into the GUI without
blocking the window. Tkinter and a graphical display are required.

### `dflow init <project_name>`

Creates the project marker, default configuration, and standard directory tree,
then prints a success message. It does not need an existing DFlow project.

### `dflow compile [-- TOOL_OPTION...]`

Finds the project, loads configuration, and calls the compile dispatcher. A
missing/unsupported backend or backend precondition failure exits with code 1.
Otherwise it saves `reports/compile/<tool>.log`, forwards captured stdout and
stderr, prints a success message for return code 0, and exits with the tool's
return code.

Arguments after `--` are appended to `compile.options` or the backend defaults:

```bash
dflow compile -- --Wall
```

### `dflow lint [-- TOOL_OPTION...]`

Matches the compile command flow but dispatches lint and writes
`reports/lint/<tool>.log`. Extra arguments use the same pass-through syntax:

```bash
dflow lint -- -Wall --Wno-fatal
```

### `dflow sim [-- TOOL_OPTION...]`

Finds the project, loads configuration, and calls the simulation dispatcher. It
writes `reports/sim/<tool>.log`, forwards each completed step's output with
headings, prints success only for return code 0, and exits with the final step's
code. A missing or unsupported backend/precondition exits with code 1.
Arguments after `--` are appended to the configured/default simulation options:

```bash
dflow sim -- --threads 4
```

### `dflow synth [-- TOOL_OPTION...]`

Finds RTL sources and dispatches the configured synthesis backend. The Yosys
backend writes netlists to `build/synthesis/netlist.v` and
`build/synthesis/netlist.json`, then saves `reports/synthesis/yosys.log`.
`synthesis.top` selects the top module; Yosys auto-detects it when omitted.
When `synthesis.liberty` is configured, the netlists are mapped to cells from
that library instead of Yosys's generic gates. For example:

```yaml
synthesis:
    tool: yosys
    top: counter
    liberty: ${PDK_ROOT}/sky130A/libs.ref/sky130_fd_sc_hd/lib/<corner>.lib
```

Arguments after `--` are appended to `synthesis.options`:

```bash
dflow synth -- -Q
```

### `dflow doctor`

Collects unique, non-empty tool names from compile, lint, simulation, and
synthesis in that order. Each executable is checked once. It prints
`<tool>: found|missing`, exits 1 if any are missing, and otherwise prints a
success message. It does not validate backend support or simulation's additional
`make`/Clang requirements.

### `dflow clean [--dry-run]`

Finds the project root and removes `build/`, Verilator output at
`sim/compile_obj_dir/` and `sim/obj_dir/`, the legacy root `obj_dir/`, and the
obsolete `sim/logs/` directory. It clears the contents of `reports/` and
`sim/waves/` while preserving those scaffold directories.
Every target is validated against the resolved project root; unsafe paths and
parent-directory symlink escapes are refused. Failures are reported per path,
remaining targets are still processed, and any failure produces exit code 1.
`--dry-run` previews non-empty/existing targets without changing them.

### `dflow status`

Prints the project name and root, RTL and testbench source counts, each
configured flow tool, and the latest result recorded for compile, lint,
simulation, and synthesis. It also reports whether reports, waveforms, and
build files are present. Status is read-only and does not check tool
availability; use `dflow doctor` for that.

## 7. Backend Contracts

### Result and execution

`FlowStepResult` is a dataclass containing a step name, command, return
code, stdout, and stderr. `FlowRunResult` contains the configured tool name and
the ordered list of completed steps; its return code is the last step's code, or
1 when the list is empty.

`run_flow_command()` copies the current environment, optionally merges an
environment override, runs a list-form command from the project root, captures
text stdout/stderr, and returns `FlowStepResult`. It does not use a shell or
catch process-launch errors.

`commands/common.py` provides the shared lifecycle for compile, lint,
simulation, and synthesis: project/config loading, backend invocation, report
persistence, step-output forwarding, success output, and exit-code propagation.

### Dispatchers

Flow dispatchers may load configuration themselves when none is supplied. Each
reads its section's `tool` and prints an error and returns `None` for missing or
unsupported tools. Compile, lint, and simulation support Verilator; synthesis
supports Yosys.

### Verilator compile

The compile backend uses the shared RTL-stage helper. It requires `verilator`
on `PATH` and at least one RTL source, reads `compile.options` with a `--cc`
default. It recreates `sim/compile_obj_dir/` and executes:

```text
verilator <options> --Mdir <project>/sim/compile_obj_dir <sorted RTL sources>
```

The compile output is separate from `sim/obj_dir/`, preventing compile checks
from overwriting simulation executables. The root `obj_dir/` is no longer
generated by DFlow.

### Verilator lint

The lint backend uses the same helper and preconditions. It reads `lint.options`,
defaulting to `--lint-only -Wall`, then executes:

```text
verilator <options> <sorted RTL sources>
```

### Verilator simulation

The simulation backend requires Verilator plus at least one RTL and testbench
source. `simulation.top` selects the top module. If omitted and exactly one
testbench source exists, its filename stem is inferred; with multiple sources,
`top` is required.

Simulation options default to:

```text
--cc --exe --main --trace --timing
```

Every run recursively removes an existing `sim/obj_dir`, recreates it, and runs:

```text
verilator <options> --Mdir <project>/sim/obj_dir \
  --top-module <top> <RTL sources> <testbench sources>
```

If Verilator succeeds, the backend invokes `make` on `V<top>.mk`. The current
implementation is environment-specific: it forces `clang++`, C++20, libc++, and
LLVM 18 include/library paths (`/usr/lib/llvm-18/...`). It therefore also relies
on `make`, Clang, and libc++ even though only Verilator is checked up front.

After a successful build, the expected binary is `sim/obj_dir/V<top>`. Missing
binary output becomes a synthetic failed step. Otherwise the binary runs from
the project root so relative waveform paths resolve there. The backend returns
the completed Verilator, Make, validation, and simulation steps in order and
stops immediately after a failed step.

### Yosys synthesis

The synthesis backend requires `yosys` on `PATH` and at least one RTL source.
It validates an optional Liberty path, removes stale files under
`build/synthesis/`, recreates that directory, and runs one Yosys process. The
generated script reads RTL as SystemVerilog and selects the configured or
automatically detected top module.

Without a Liberty file, the backend runs generic `synth`. With one, it runs
`synth -noabc`, `dfflibmap -liberty`, `abc -liberty`, `clean`, and
`stat -liberty` before writing Verilog and JSON netlists. This maps sequential
and combinational logic to cells from the selected library and reports cell
area data. `synthesis.options` and CLI arguments remain Yosys process options.

The generated `constraints/` directory remains reserved for future timing and
pin constraints. Liberty mapping uses real cells, but DFlow does not yet pass
an ABC delay target, ABC driving-cell/load constraints, SDC timing constraints,
or physical placement information.

## 8. Reports and Generated Artifacts

`save_flow_report()` creates `reports/<stage>/<tool>.log` and overwrites the same
tool/stage log on later runs. For every completed step, the report records its
name, command, return code, and non-empty `STDOUT`/`STDERR` sections.

Compile, lint, simulation, and synthesis commands save reports for successful
and nonzero tool results. They do not create a report when dispatch returns
`None`. Yosys writes netlists under `build/synthesis/`. Verilator compile output
uses `sim/compile_obj_dir/`, while simulation builds under `sim/obj_dir/`; a
testbench may write files such as `sim/waves/*.vcd`. Simulation ensures
`sim/waves/` exists before building. Use
`dflow clean --dry-run` to preview these generated artifacts and `dflow clean`
to remove or clear them.

## 9. Counter Example

`Dflow_project_examples/counter/` demonstrates the Verilator and Yosys flows:

- `rtl/counter.v` is a four-bit active-low-reset counter.
- `tb/counter_tb.sv` supplies a timed SystemVerilog testbench, enables VCD
  tracing, checks that eight clock edges produce count 8, and exits fatally on
  failure.
- `flow.yaml` selects Verilator for compile, lint, and simulation, declares
  `simulation.top: counter_tb`, selects Yosys, and declares
  `synthesis.top: counter`.
- `.dflow` marks the example as a runnable DFlow project.
- `sim/waves/counter.vcd` is a locally generated, currently untracked waveform.

Unlike newly generated projects, the example omits compile/lint option lists, so
backend defaults apply. Local runs have also produced ignored logs under
`reports/{compile,lint,sim}/` and Verilator/Make output under `sim/obj_dir/`;
these are generated artifacts rather than maintained source files.

## 10. Current Limitations

- Yosys supports Liberty cell mapping, but FPGA-family flows, ABC delay/load
  constraints, SDC timing constraints, and physical design are not implemented.
- Simulation's Make command is tied to Clang/libc++ and LLVM 18 filesystem paths.
- `doctor` checks configured tool names only; it does not validate backend
  support, source files, YAML shape, `make`, Clang, or libc++.
- Config validation and friendly handling for malformed YAML or missing project
  markers are not implemented.
- `logger.py`, `version.py`, and most package `__init__.py` files are empty.
- `README.md` is empty, and no formatter or linter is configured.
- The pytest suite covers shared results/reports, clean safety and failure
  handling, project status, doctor tool deduplication, and simulation
  sequencing; broader command/config coverage is still needed.
- Reports overwrite previous logs for the same stage/tool.

## 11. Extension Rules

Keep commands thin, put shared project behavior in `core`, and isolate external
tool behavior under a stage-specific backend package. New executing backends
should return `FlowRunResult` containing ordered `FlowStepResult` entries, use
the shared executor where practical, preserve external return codes, and leave
report persistence to the shared command/core layers. When behavior changes,
update this guide and add tests under `tests/`.
