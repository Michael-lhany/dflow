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

Compile, lint, and simulation have Verilator backends, synthesis has a Yosys
backend with optional Liberty cell mapping, and the ASIC stage drives OpenLane
2 directly or through a Nix flake. Formal verification drives SymbiYosys with
timestamped proof work directories. Clean removes generated artifacts, while
status summarizes project sources, flows, reports, and generated artifacts.

## 2. Repository Layout

```text
.
├── AGENTS.md                         contributor instructions
├── README.md                         empty user-documentation placeholder
├── pyproject.toml                    package metadata and console entry point
├── docs/
│   ├── DEVELOPER_GUIDE.md            implementation reference
│   ├── GUI_GUIDE.md                  complete graphical-interface guide
│   ├── OPENLANE_GUIDE.md             OpenLane user guide
│   ├── SYMBIYOSYS_GUIDE.md           formal verification user guide
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
│       ├── synthesis/                Yosys synthesis dispatcher/backend
│       └── asic/                     OpenLane RTL-to-GDS dispatcher/backend
└── tests/                            isolated pytest coverage
```

The top-level, command, and core `__init__.py` files are empty package markers;
the flow backend package initializers implement their dispatchers. `.gitignore`
excludes Python caches, virtual environments, editor state, pytest/build output,
`obj_dir/`, logs, reports, and OS metadata.

## 3. Packaging and Entry Point

`pyproject.toml` is the single dependency source. It uses
`setuptools.build_meta` with `setuptools>=61`; package discovery includes only
`dflow*`. Runtime dependencies are `typer`, `pyyaml`, and `click` (also used
by the standalone SymbiYosys launcher), while the optional
`dev` extra installs pytest. The installed console script is:

```toml
[project.scripts]
dflow = "dflow.cli:app"
```

`dflow/cli.py` is the only command-registration point. It registers, in order,
`init`, `compile`, `synth`, `lint`, `sim`, `status`, `doctor`, `clean`, `gui`,
and `asic`.
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
| `asic` | `tool`, `config`, `executable`, `openlane_root`, `options` | OpenLane design config and direct/Nix execution |

`synthesis.liberty` accepts an absolute path, a path relative to the project
root, `~`, and environment variables such as `${PDK_ROOT}`. The expanded path
must identify an existing file before synthesis starts.

OpenLane-specific optional `asic` keys are `flow`, `pdk`, `scl`, `pdk_root`,
and `run_tag`. They map to the corresponding OpenLane 2 CLI flags. `executable`
can select an already realized Nix-store wrapper without evaluating the flake.
Paths accept
absolute values, project-relative values, `~`, and environment variables. A
typical Nix-backed setup is:

```yaml
asic:
    tool: openlane
    openlane_root: ~/openlane/openlane2
    config: openlane/config.json
```

The design config remains a native OpenLane JSON, YAML, or Tcl file. The
Classic flow normally needs at least `DESIGN_NAME`, `VERILOG_FILES`,
`CLOCK_PORT`, and `CLOCK_PERIOD`.

## 6. Command Reference

### `dflow gui`

Opens the tabbed Tkinter interface. A shared project selector sits above pages
for Project, Compile, Lint, Simulation, Synthesis, Formal, ASIC, Status,
Doctor, and Clean. Each executing flow keeps an independent argument field so options do
not leak between tools. The Simulation page can open a new waveform after a run
or open the newest existing VCD without simulating. The ASIC page provides
condensed output, parallel-job, start-step, end-step, extra-option, lint-only,
KLayout, and OpenROAD controls.
The Formal page selects a job and tasks and builds validated parallel,
sequential, live-status, and extra SBY options.

Commands run through `python -m dflow.cli`, so the GUI uses the same
configuration, backends, reports, and exit codes as the terminal. Output is
streamed into a shared console without blocking the window. Tkinter and a
graphical display are required.

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

### `dflow sim [--wave | --wave-only] [-- TOOL_OPTION...]`

Finds the project, loads configuration, and calls the simulation dispatcher. It
writes a timestamped `reports/sim/<tool>_<timestamp>.log`, forwards each
completed step's output with
headings, prints success only for return code 0, and exits with the final step's
code. A missing or unsupported backend/precondition exits with code 1.
Arguments after `--` are appended to the configured/default simulation options:

```bash
dflow sim -- --threads 4
```

Pass `--wave` (or `-w`) to open the newest VCD under `sim/waves/` in
GTKWave after a successful simulation. GTKWave is launched as a detached
process, so DFlow exits while the viewer remains open:

```bash
dflow sim --wave
```

Use `--wave-only` to open the newest existing VCD without running simulation:

```bash
dflow sim --wave-only
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

### `dflow asic [-- OPENLANE_OPTION...]`

Runs an OpenLane 2 RTL-to-GDS flow using the `asic` section of `flow.yaml`.
DFlow invokes `openlane` directly when it is on `PATH`. Otherwise,
`asic.openlane_root` must point to an OpenLane 2 checkout containing
`flake.nix`; DFlow invokes it through `nix develop` automatically.

The default design configuration path is `openlane/config.json`. OpenLane's
Classic flow is used unless `asic.flow` or the design config selects another
flow. Extra CLI flags are forwarded after `--`:

```bash
dflow asic -- --condensed --show-progress-bar
```

OpenLane creates timestamped run directories beneath the design configuration
directory's `runs/` folder. DFlow also preserves a timestamped wrapper report
under `reports/asic/openlane_<timestamp>.log`.

### `dflow formal [--task TASK] [--config FILE] [-- SBY_OPTION...]`

Runs the configured SymbiYosys job. `--task/-t` is repeatable and temporarily
replaces `formal.tasks`; `--config/-c` temporarily replaces `formal.config`.
Raw SBY options follow `--`.

The backend supplies a timestamped `--prefix` below `formal/runs/` (or the
configured `formal.output_directory`), streams SBY output, and preserves a
timestamped report under `reports/formal/sby_<timestamp>.log`.

### `dflow doctor`

Collects unique, non-empty tool names from compile, lint, simulation,
synthesis, ASIC, and formal in that order. Each executable is checked once. OpenLane is
considered available when it is on `PATH`, or when Nix and the configured
OpenLane flake are present. SymbiYosys accepts `sby` from `PATH` or an explicit
`formal.executable`. It prints
`<tool>: found|missing`, exits 1 if any are missing, and otherwise prints a
success message. It does not validate backend support or simulation's additional
`make`/Clang requirements.

### `dflow clean [--dry-run] [--only CATEGORY] [--exclude CATEGORY]`

Finds the project root and removes generated artifacts. With no category
options, it removes `build/`, Verilator output at `sim/compile_obj_dir/` and
`sim/obj_dir/`, the legacy root `obj_dir/`, obsolete `sim/logs/`, and
`openlane/runs/` and `formal/runs/`. It clears `reports/` and `sim/waves/` while
preserving those two scaffold directories.

Cleanup targets are grouped as follows:

| Category | Generated paths |
| --- | --- |
| `build` | `build/` |
| `compile` | `obj_dir/`, `sim/compile_obj_dir/` |
| `simulation` | `sim/obj_dir/`, `sim/logs/` |
| `waveforms` | Contents of `sim/waves/` |
| `reports` | Contents of `reports/` |
| `asic` | `openlane/runs/` |
| `formal` | `formal/runs/` |

`--only/-o` is repeatable and limits cleanup to named categories.
`--exclude/-x` is also repeatable and preserves named categories; exclusions
win when combined with `--only`. Examples:

```bash
dflow clean --only simulation
dflow clean -o reports -o waveforms --dry-run
dflow clean --exclude asic --exclude reports
```

The GUI Clean page exposes the same categories as independent checkboxes, with
Select All, Select None, preview, and confirmed cleanup actions.
Every target is validated against the resolved project root; unsafe paths and
parent-directory symlink escapes are refused. Failures are reported per path,
remaining targets are still processed, and any failure produces exit code 1.
`--dry-run` previews non-empty/existing targets without changing them.

### `dflow status`

Prints the project name and root, RTL and testbench source counts, each
configured flow tool, and the latest result recorded for compile, lint,
simulation, synthesis, ASIC, and formal. It also reports whether reports, waveforms, and
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
simulation, synthesis, ASIC, and formal: project/config loading, backend invocation, report
persistence, step-output forwarding, success output, and exit-code propagation.

### Dispatchers

Flow dispatchers may load configuration themselves when none is supplied. Each
reads its section's `tool` and prints an error and returns `None` for missing or
unsupported tools. Compile, lint, and simulation support Verilator; synthesis
supports Yosys; and ASIC supports OpenLane.
Formal supports `sby` and the `symbiyosys` alias.

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
--cc --exe --main --trace --timing --timescale 1ns/1ps
```

The default timescale supplies a value for RTL modules that omit a local
directive while allowing testbenches to retain an explicit matching timescale.
This avoids `TIMESCALEMOD` failures without adding simulation
directives to synthesizable RTL used by OpenLane.

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

### OpenLane ASIC flow

The ASIC backend validates the configured design file and accepts OpenLane JSON,
YAML, YML, and Tcl formats. It first uses `asic.executable` when configured,
then an `openlane` executable on `PATH`. When neither is available, it validates
`asic.openlane_root/flake.nix` and constructs:

```text
nix develop <openlane-root>#default --command openlane \
  <configured options and flags> <design config>
```

OpenLane owns the detailed flow, PDK resolution, step outputs, and physical
artifacts. DFlow streams its output live to the terminal or GUI while retaining
the same output and return code in one report step. A Nix-backed first run may
need network access to realize missing flake inputs and may download a PDK
through Volare.

### SymbiYosys formal verification

`dflow/backends/formal/__init__.py` dispatches both `sby` and the
`symbiyosys` alias. The backend resolves an optional explicit executable,
validates the `.sby` job and task list, creates the configured run root, and
gives SBY a unique timestamped prefix. SBY options precede the job path while
task names follow it. Proof output is streamed and captured in one result step.

## 8. Reports and Generated Artifacts

`save_flow_report()` normally creates `reports/<stage>/<tool>.log` and
overwrites the same tool/stage log on later runs. Simulation, ASIC, and formal instead
create new timestamped reports for every run, preserving their histories. For
every completed step, the report records its name, command, return code, and
non-empty `STDOUT`/`STDERR` sections.

Compile, lint, simulation, synthesis, ASIC, and formal commands save reports for
successful and nonzero tool results. They do not create a report when dispatch
returns `None`. Yosys writes netlists under `build/synthesis/`. Verilator
compile output uses `sim/compile_obj_dir/`, while simulation builds under
`sim/obj_dir/`; a testbench may write files such as `sim/waves/*.vcd`.
OpenLane writes its run directories below `openlane/runs/`; SymbiYosys writes
proof work directories and traces below `formal/runs/`. Use
`dflow clean --dry-run` to preview these generated artifacts and `dflow clean`
to remove or clear them.

## 9. Local Integration Projects

Local HDL projects and examples are intentionally ignored by Git. Create one
with `dflow init <project-name>` and use it for manual Verilator, Yosys,
SymbiYosys, and OpenLane integration checks. Keep reusable behavior covered by
isolated tests under `tests/`, where external EDA processes are mocked.
- `sim/waves/counter.vcd` is a locally generated, currently untracked waveform.

Unlike newly generated projects, the example omits compile/lint option lists, so
backend defaults apply. Local runs have also produced ignored logs under
`reports/{compile,lint,sim,asic,formal}/`, Verilator/Make output under `sim/obj_dir/`,
OpenLane physical-design runs under `openlane/runs/`, and SBY work directories
under `formal/runs/`;
these are generated artifacts rather than maintained source files.

## 10. Current Limitations

- Standalone Yosys supports Liberty mapping but does not apply the full physical
  constraints used by OpenLane; use `dflow asic` for RTL-to-GDS implementation.
- Simulation's Make command is tied to Clang/libc++ and LLVM 18 filesystem paths.
- `doctor` recognizes a configured OpenLane Nix flake but does not realize it,
  validate its PDK, or check source/config semantics. It also does not validate
  backend support, `make`, Clang, or libc++.
- Config validation and friendly handling for malformed YAML or missing project
  markers are not implemented.
- `logger.py`, `version.py`, and most package `__init__.py` files are empty.
- `README.md` is empty, and no formatter or linter is configured.
- The pytest suite covers shared results/reports, clean safety and failure
  handling, project status, doctor tool deduplication, and simulation
  sequencing; broader command/config coverage is still needed.
- Compile, lint, and synthesis reports still overwrite the previous log for the
  same stage/tool; simulation, ASIC, and formal reports are timestamped.

## 11. Extension Rules

Keep commands thin, put shared project behavior in `core`, and isolate external
tool behavior under a stage-specific backend package. New executing backends
should return `FlowRunResult` containing ordered `FlowStepResult` entries, use
the shared executor where practical, preserve external return codes, and leave
report persistence to the shared command/core layers. When behavior changes,
update this guide and add tests under `tests/`.
