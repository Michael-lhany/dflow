# DFlow GUI Guide

This guide documents the complete DFlow graphical interface, including every
page, option, action, and the command each control runs.

## 1. Starting the GUI

Activate the DFlow development environment and launch the interface:

```bash
cd /path/to/dflow
source ./activate.sh
dflow gui
```

The GUI requires Python Tkinter and a graphical desktop session. If Tkinter is
missing, install the Python Tk package supplied by the operating system. If no
display is available, DFlow reports that a graphical display is required.

The window contains three main areas:

1. The active project selector.
2. Command-specific tabs.
3. A shared command-output console.

## 2. Active project selector

The **Active project** field appears above every command tab. It determines the
working directory used for all commands.

| Control | Behavior |
| --- | --- |
| Project path | Accepts an existing directory path |
| **Browse** | Opens a directory-selection dialog |

For most commands, the selected directory must be inside a DFlow project. DFlow
searches it and its parents for the `.dflow` marker. This means a nested source
directory can be selected and DFlow will still find the project root.

The Project tab is different: its selected directory is the parent directory
under which a new project will be created.

## 3. Command execution model

The GUI does not implement separate versions of the flows. It starts the same
Python CLI used in a terminal:

```text
<active Python> -m dflow.cli <command> [command options] [-- tool options]
```

For example, entering `-Wall --Wno-fatal` on the Lint tab produces:

```bash
python -m dflow.cli lint -- -Wall --Wno-fatal
```

Every executing flow has an independent option field. Compile, lint,
simulation, synthesis, and ASIC options do not leak into one another.

While a command is running:

- Command buttons are disabled to prevent overlapping flows.
- Output is streamed into the shared console.
- The status line shows the active command.
- The GUI remains responsive because execution occurs on a worker thread.
- Buttons are restored when the subprocess exits.

## 4. Project tab

The Project tab creates a new DFlow project.

| Control | Description |
| --- | --- |
| **Project name** | Name of the new directory and DFlow project |
| **Create Project** | Runs `dflow init <project-name>` |

The new project is created below the directory in **Active project**. For
example:

```text
Active project: /path/to/designs
Project name: uart
```

runs:

```bash
cd /path/to/designs
python -m dflow.cli init uart
```

Initialization creates `.dflow`, `flow.yaml`, RTL and testbench directories,
reports, simulation folders, constraints, and OpenLane folders. A blank project
name is rejected before a command is started.

## 5. Compile tab

The Compile tab performs the configured RTL compilation check.

| Control | Description |
| --- | --- |
| **Verilator arguments** | Temporary arguments appended to the configured compile options |
| **Run Compile** | Runs `dflow compile` |

Example field value:

```text
--top-module counter -Wall
```

Generated command:

```bash
dflow compile -- --top-module counter -Wall
```

The arguments are passed to Verilator after the configured `compile.options`
from `flow.yaml`. Quoted values are parsed using shell-style quoting, but the
command itself is executed without a shell.

Compile reports are written to:

```text
reports/compile/<tool>.log
```

Verilator compile output is generated under:

```text
sim/compile_obj_dir/
```

## 6. Lint tab

The Lint tab runs the configured RTL linter.

| Control | Description |
| --- | --- |
| **Verilator arguments** | Temporary lint options |
| **Run Lint** | Runs `dflow lint` |

Example field value:

```text
-Wall --Wno-fatal --Wno-TIMESCALEMOD
```

Generated command:

```bash
dflow lint -- -Wall --Wno-fatal --Wno-TIMESCALEMOD
```

The GUI does not automatically suppress warnings. Add warning controls only
after reviewing the diagnostic and deciding that it is intentional.

Lint reports are written to:

```text
reports/lint/<tool>.log
```

## 7. Simulation tab

The Simulation tab builds and runs the configured testbench.

| Control | Description |
| --- | --- |
| **Verilator arguments** | Temporary Verilator simulation-build options |
| **Open a newly generated waveform** | Adds `--wave` to the DFlow simulation command |
| **Run Simulation** | Builds and runs the simulation |
| **Open Existing Wave** | Opens the newest existing VCD without simulating |

### Run without opening a waveform

With the waveform checkbox cleared:

```bash
dflow sim
```

### Run and open the generated waveform

With the checkbox selected:

```bash
dflow sim --wave
```

DFlow opens only a VCD created or updated during that successful simulation.
This prevents an old waveform from being mistaken for current output.

### Open an existing waveform

The **Open Existing Wave** action runs:

```bash
dflow sim --wave-only
```

It does not compile or run simulation and intentionally ignores the Simulation
tab's Verilator arguments.

GTKWave must be installed and available on `PATH`. Waveforms are searched
recursively below:

```text
sim/waves/
```

Simulation reports use timestamped names so previous runs are preserved:

```text
reports/sim/verilator_<timestamp>.log
```

## 8. Synthesis tab

The Synthesis tab generates netlists using the configured synthesis backend.

| Control | Description |
| --- | --- |
| **Yosys arguments** | Temporary Yosys process options |
| **Run Synthesis** | Runs `dflow synth` |

Example field value:

```text
-Q -q
```

Generated command:

```bash
dflow synth -- -Q -q
```

The top module and optional Liberty file are persistent project settings under
the `synthesis` section of `flow.yaml`; they are not GUI text fields.

Generated netlists are written under:

```text
build/synthesis/
```

The synthesis report is written to:

```text
reports/synthesis/<tool>.log
```

## 9. Formal tab

The Formal tab runs the SymbiYosys backend configured in `flow.yaml`.

| Control | Generated argument | Description |
| --- | --- | --- |
| **SBY configuration** | `--config <file>` | Temporarily selects another `.sby` job |
| **Tasks** | Repeated `--task <name>` | Selects space-separated tasks such as `prove cover` |
| **Parallel jobs** | `-j <count>` | Sets the maximum SBY process count |
| **Run tasks sequentially** | `--sequential` | Runs tasks one after another |
| **Stream property status** | `--live jsonl` | Streams property updates |
| **Extra SBY arguments** | User-entered options | Adds options such as `--autotune` |

The configuration and task fields may be blank to use `flow.yaml`. A complete
selection can generate:

```bash
dflow formal --config formal/counter.sby \
    --task prove --task cover -- -j 4 --live jsonl
```

DFlow preserves SBY work directories under `formal/runs/` and timestamped
reports under `reports/formal/`. Do not provide `-d` or `--prefix` as an extra
argument because DFlow manages unique run paths.

See [SymbiYosys formal verification with DFlow](SYMBIYOSYS_GUIDE.md) for job
syntax, properties, trace viewing, and troubleshooting.

## 10. ASIC tab

The ASIC tab controls the OpenLane RTL-to-GDS backend.

| Control | Generated OpenLane option | Description |
| --- | --- | --- |
| **Condensed OpenLane output** | `--condensed` | Reduces verbose subprocess output |
| **Parallel jobs** | `-j <count>` | Sets OpenLane's worker count |
| **Start step** | `--from <step>` | Starts the Classic flow at a selected step |
| **End step** | `--to <step>` | Stops after a selected step |
| **Extra arguments** | User-entered options | Adds other OpenLane CLI options |

The parallel-job value must be a positive integer. Blank means that OpenLane
uses its default. Invalid values are rejected in the GUI before execution.

Common step IDs include:

```text
Verilator.Lint
Yosys.Synthesis
OpenROAD.Floorplan
OpenROAD.GeneratePDN
OpenROAD.GlobalPlacement
OpenROAD.DetailedRouting
```

OpenLane validates step IDs. Names are case-sensitive.

### Run ASIC Flow

**Run ASIC Flow** combines all selected ASIC controls and runs:

```bash
dflow asic -- <generated OpenLane options>
```

For example, condensed output, four jobs, and an end step of
`OpenROAD.GeneratePDN` produce:

```bash
dflow asic -- --condensed -j 4 --to OpenROAD.GeneratePDN
```

### Lint Only

**Lint Only** forces the end step to `Verilator.Lint` while preserving the
condensed-output, jobs, start-step, and extra-argument controls:

```bash
dflow asic -- --condensed --to Verilator.Lint
```

This is the recommended quick validation before a design's first full physical
run.

### Open in KLayout

Runs the OpenLane viewer flow against the latest run:

```bash
dflow asic -- --last-run --flow OpenInKLayout
```

### Open in OpenROAD

Runs:

```bash
dflow asic -- --last-run --flow OpenInOpenROAD
```

Viewer actions intentionally ignore other ASIC page controls. They require a
successful existing OpenLane run and a graphical desktop session.

### ASIC output

OpenLane run directories are stored beside the OpenLane design configuration:

```text
openlane/runs/RUN_<timestamp>/
```

DFlow preserves timestamped wrapper reports under:

```text
reports/asic/openlane_<timestamp>.log
```

For full OpenLane configuration and troubleshooting, see
[Using OpenLane with DFlow](OPENLANE_GUIDE.md).

## 11. Status tab

The Status tab is read-only.

| Control | Description |
| --- | --- |
| **Refresh Status** | Runs `dflow status` |

It reports:

- Project name and root.
- RTL and testbench source counts.
- Configured tool for each flow.
- Latest known report result.
- Availability of reports, waveforms, and build artifacts.

Status does not execute EDA tools or validate their installation.

## 12. Doctor tab

The Doctor tab checks configured tool availability.

| Control | Description |
| --- | --- |
| **Run Doctor** | Runs `dflow doctor` |

Doctor checks unique configured executables once. OpenLane is considered
available when DFlow can find one of the following:

- The configured `asic.executable`.
- An `openlane` command on `PATH`.
- Nix and a valid `asic.openlane_root` flake.

Doctor does not validate HDL, PDK completeness, backend options, Make, Clang,
or the complete OpenLane environment. Run the actual stage or OpenLane lint-only
action for deeper validation.

## 13. Clean tab

The Clean tab safely previews or removes selected generated artifacts.

| Checkbox | CLI category | Paths affected |
| --- | --- | --- |
| **Synthesis build** | `build` | `build/` |
| **Compile output** | `compile` | `obj_dir/`, `sim/compile_obj_dir/` |
| **Simulation build** | `simulation` | `sim/obj_dir/`, `sim/logs/` |
| **Waveforms** | `waveforms` | Contents of `sim/waves/` |
| **Reports** | `reports` | Contents of `reports/` |
| **OpenLane runs** | `asic` | `openlane/runs/` |
| **SymbiYosys runs** | `formal` | `formal/runs/` |

### Selection actions

| Button | Behavior |
| --- | --- |
| **Select All** | Enables every cleanup category |
| **Select None** | Clears every category |
| **Preview Cleanup** | Runs selected categories with `--dry-run` |
| **Clean Selected** | Shows a confirmation listing selected categories, then removes them |

When all categories are selected, the GUI runs the default command:

```bash
dflow clean
```

When only reports and waveforms are selected, it runs:

```bash
dflow clean --only waveforms --only reports
```

Preview adds `--dry-run`:

```bash
dflow clean --dry-run --only waveforms --only reports
```

Selecting no categories is rejected without starting a command.

Cleanup never intentionally removes maintained RTL, testbenches, `flow.yaml`,
`.dflow`, or `openlane/config.json`. Every target is validated to remain inside
the project before deletion.

The CLI additionally supports exclusions, for example:

```bash
dflow clean --exclude reports --exclude asic
```

## 14. Shared output console

The bottom panel displays the exact working directory and command before each
run:

```text
$ cd /path/to/project
$ /path/to/python -m dflow.cli lint -- -Wall
```

It then streams combined standard output and standard error. When the command
finishes, the GUI appends its exit code:

```text
[exit code 0]
```

The status line reports completion or failure. **Clear Output** removes text
from the GUI console only; it does not delete saved reports or flow artifacts.

## 15. Argument quoting

Option fields support shell-style quoting. For example:

```text
--top-module "counter top"
```

is passed as two arguments:

```text
--top-module
counter top
```

Unmatched quotation marks are rejected as invalid tool arguments. DFlow passes
parsed arguments directly to subprocesses and does not execute them through a
shell.

Do not enter the DFlow command itself in an option field. Enter only backend
arguments. For example, the ASIC **Extra arguments** field should contain:

```text
--run-tag floorplan_test
```

not:

```text
dflow asic -- --run-tag floorplan_test
```

## 16. Typical workflows

### RTL development loop

1. Select the project.
2. Run **Lint**.
3. Run **Compile**.
4. Run **Simulation** with waveform opening enabled.
5. Inspect the VCD in GTKWave.

### Synthesis check

1. Configure `synthesis.top` and optional `synthesis.liberty` in `flow.yaml`.
2. Run **Synthesis**.
3. Use **Status** to confirm the report result.
4. Inspect generated netlists under `build/synthesis/`.

### Formal verification loop

1. Add assertions and cover statements in a formal harness.
2. Configure its `.sby` job and the `flow.yaml` formal section.
3. Open **Formal**, select `prove`, and run the safety proof.
4. Select `cover` to confirm the intended state is reachable and inspect its
   VCD trace in GTKWave.

### First OpenLane run

1. Configure `asic` in `flow.yaml` and create `openlane/config.json`.
2. Run **Doctor**.
3. On the ASIC tab, click **Lint Only**.
4. Correct all meaningful lint diagnostics.
5. Use start/end controls for focused floorplan or PDN experiments.
6. Run the complete ASIC flow.
7. Open the final layout in KLayout or OpenROAD.

### Selective cleanup

1. Open **Clean**.
2. Select only the generated categories that should be removed.
3. Click **Preview Cleanup**.
4. Review the listed paths in the console.
5. Click **Clean Selected** and confirm.

## 17. Troubleshooting

### A command does nothing

Check whether another command is already running. Command buttons remain
disabled until it exits. Also verify that **Active project** points to an
existing directory.

### A command exits immediately

Read the exact command and error in the output console. Then use the Status and
Doctor tabs to distinguish a project configuration issue from a missing tool.

### Invalid tool arguments

Check for unmatched quotes. On the ASIC tab, also verify that **Parallel jobs**
is blank or a positive integer.

### GTKWave does not open

Confirm that `gtkwave` is installed, a VCD exists under `sim/waves/`, and the
GUI was started from a graphical desktop session.

### KLayout or OpenROAD does not open

Viewer actions require a previous OpenLane run with the necessary physical
views. Review the latest ASIC report and confirm that the underlying Classic
flow completed far enough to generate a layout.

### OpenLane appears slow

The initial Nix environment and PDK setup can take time. OpenLane output should
continue streaming into the console. Use a positive parallel job count when the
machine has sufficient CPU and memory.

### Cleanup selected the wrong artifacts

Use **Preview Cleanup** before confirming. The preview uses the exact same
category selection without deleting anything.

### SymbiYosys or its solver is missing

Run **Doctor** and confirm `sby: found`. Start the GUI from a terminal whose
`PATH` includes `~/.local/bin`. If SBY starts but its engine fails, verify the
solver from the `.sby` `[engines]` section, such as `command -v z3`.

## 18. Related documentation

- [Using OpenLane with DFlow](OPENLANE_GUIDE.md)
- [SymbiYosys formal verification with DFlow](SYMBIYOSYS_GUIDE.md)
- [Verilator Arguments](VERILATOR_ARGUMENTS.md)
- [Yosys Arguments](YOSYS_ARGUMENTS.md)
- [DFlow Developer Guide](DEVELOPER_GUIDE.md)
