# Using OpenLane with DFlow

This guide explains how to run an OpenLane 2 RTL-to-GDS ASIC flow through
DFlow. It covers both the command line and the graphical interface.

## 1. Prerequisites

You need:

- A DFlow project containing `.dflow` and `flow.yaml`.
- Synthesizable Verilog or SystemVerilog under the project's `rtl/` directory.
- OpenLane 2 and a supported PDK, normally Sky130 for an initial test.
- Either an `openlane` executable on `PATH`, an executable supplied by Nix, or
  an OpenLane 2 checkout containing `flake.nix`.

From the project directory, check the configured tools:

```bash
dflow doctor
```

A working OpenLane setup is reported as:

```text
openlane: found
```

This check confirms that DFlow can locate an OpenLane runtime. It does not run
the flow or validate the PDK and design configuration.

## 2. Configure `flow.yaml`

Add an `asic` section to the project's `flow.yaml`.

### OpenLane already on `PATH`

```yaml
asic:
    tool: openlane
    config: openlane/config.json
```

### OpenLane from a Nix checkout

When `openlane` is not on `PATH`, point DFlow to the OpenLane 2 source checkout:

```yaml
asic:
    tool: openlane
    openlane_root: ~/openlane/openlane2
    config: openlane/config.json
```

DFlow runs it as:

```text
nix develop <openlane_root>#default --command openlane ...
```

The first invocation can take time while Nix realizes the environment.

### Explicit executable

If Nix has already realized OpenLane but the command is not on `PATH`, an
explicit executable can be selected:

```yaml
asic:
    tool: openlane
    executable: /nix/store/<package>/bin/openlane
    openlane_root: ~/openlane/openlane2
    config: openlane/config.json
```

An explicit Nix-store path is machine-specific and can change after an upgrade
or garbage collection. If that happens, update or remove `asic.executable` so
DFlow can use the configured `openlane_root` fallback.

## 3. Create the OpenLane design configuration

DFlow uses OpenLane's native JSON, YAML, YML, or Tcl configuration format. The
default path is:

```text
openlane/config.json
```

A minimal JSON configuration is:

```json
{
  "DESIGN_NAME": "counter",
  "VERILOG_FILES": ["dir::../rtl/counter.v"],
  "CLOCK_PORT": "clk",
  "CLOCK_PERIOD": 10
}
```

The important fields are:

| Field             | Meaning                                    |
| ----------------- | ------------------------------------------ |
| `DESIGN_NAME`   | Name of the synthesizable top-level module |
| `VERILOG_FILES` | RTL files supplied to OpenLane             |
| `CLOCK_PORT`    | Top-level clock input                      |
| `CLOCK_PERIOD`  | Target clock period in nanoseconds         |

`dir::` is relative to the directory containing the OpenLane configuration.
Because this example stores the configuration under `openlane/`, the RTL source
is reached through `../rtl/counter.v`.

For multiple RTL files, list each source explicitly:

```json
{
  "DESIGN_NAME": "chip_top",
  "VERILOG_FILES": [
    "dir::../rtl/chip_top.sv",
    "dir::../rtl/control.sv",
    "dir::../rtl/datapath.sv"
  ],
  "CLOCK_PORT": "clk",
  "CLOCK_PERIOD": 10
}
```

OpenLane settings can be added directly to this file. For example:

```json
{
  "DESIGN_NAME": "counter",
  "VERILOG_FILES": ["dir::../rtl/counter.v"],
  "CLOCK_PORT": "clk",
  "CLOCK_PERIOD": 10,
  "pdk::sky130*": {
    "FP_CORE_UTIL": 40
  }
}
```

See the official [OpenLane configuration reference](https://openlane2.readthedocs.io/en/latest/reference/configuration.html)
for floorplanning, placement, routing, timing, power-grid, and signoff options.

## 4. Validate the setup quickly

Before starting the complete physical flow, run only OpenLane's lint stage:

```bash
dflow asic -- --to Verilator.Lint --condensed
```

This verifies that DFlow can start OpenLane, load the PDK, read the design
configuration, and locate the RTL. A successful check ends with:

```text
Flow complete.
ASIC flow passed with openlane.
```

The `--` separator is important. Arguments after it are passed to OpenLane.

## 5. Run the complete RTL-to-GDS flow

Run the default OpenLane Classic flow with:

```bash
dflow asic -- --condensed
```

Or simply:

```bash
dflow asic
```

OpenLane output is streamed live while DFlow also records it in a report. A
complete run can take a long time depending on the design, computer, PDK cache,
and selected OpenLane options.

Common temporary OpenLane arguments include:

```bash
dflow asic -- --condensed -j 4
```

Persistent options can be stored in `flow.yaml`:

```yaml
asic:
    tool: openlane
    config: openlane/config.json
    options:
        - --condensed
        - -j
        - "4"
```

## 6. Run from the DFlow GUI

Start the interface from a graphical desktop terminal:

```bash
dflow gui
```

Then:

1. Select the DFlow project directory.
2. Open the **ASIC** tab.
3. Choose condensed output, a parallel job count, or optional start/end step
   IDs.
4. Add any remaining OpenLane flags in **Extra arguments**.
5. Click **Run ASIC Flow**.

The GUI runs the same `dflow asic` command and streams OpenLane output into the
shared output panel. The buttons remain disabled until the process finishes.
The ASIC tab also provides **Lint Only**, **Open in KLayout**, and **Open in
OpenROAD** actions.

Do not enter `dflow asic` itself in **Extra arguments**. That field contains
only arguments forwarded to OpenLane. Other command tabs have independent
option fields, so Verilator and Yosys arguments are not reused by the ASIC flow.

## 7. Find the results

OpenLane creates a timestamped run directory beside the design configuration:

```text
openlane/runs/RUN_<date>_<time>/
```

Important locations inside a completed run commonly include:

```text
openlane/runs/RUN_<timestamp>/final/
openlane/runs/RUN_<timestamp>/resolved.json
openlane/runs/RUN_<timestamp>/<step-number>-<step-name>/
```

The `final/` directory contains the final views produced by the selected flow,
such as GDS, DEF, LEF, netlists, timing data, and reports when those stages
complete successfully.

DFlow separately records the wrapper command, exit code, and streamed output:

```text
reports/asic/openlane_<timestamp>.log
```

Check the latest result with:

```bash
dflow status
```

## 8. Open the layout

After a successful full run, OpenLane can open the most recent layout in
KLayout:

```bash
dflow asic -- --last-run --flow OpenInKLayout
```

To inspect it with the OpenROAD GUI instead:

```bash
dflow asic -- --last-run --flow OpenInOpenROAD
```

Run graphical viewers from a desktop session with a valid display. These
commands reuse the most recent OpenLane run; they do not repeat the Classic
RTL-to-GDS flow.

## 9. Select a PDK or standard-cell library

The PDK can be set in the native OpenLane config or in `flow.yaml`:

```yaml
asic:
    tool: openlane
    config: openlane/config.json
    pdk: sky130A
    scl: sky130_fd_sc_hd
```

An existing manual PDK root can also be forwarded:

```yaml
asic:
    tool: openlane
    config: openlane/config.json
    pdk: sky130A
    pdk_root: ${PDK_ROOT}
```

OpenLane uses Sky130 by default when no other PDK is selected. Refer to the
official [OpenLane PDK guide](https://openlane2.readthedocs.io/en/latest/usage/about_pdks.html)
before selecting another PDK or standard-cell library.

## 10. Preserve or remove results

ASIC reports and OpenLane run directories are preserved between normal runs.
Each run receives a new timestamp.

Preview generated artifacts that DFlow would remove:

```bash
dflow clean --dry-run
```

Preserve OpenLane history while cleaning everything else:

```bash
dflow clean --exclude asic
```

Remove only OpenLane run directories:

```bash
dflow clean --only asic
```

Remove generated OpenLane runs, reports, simulation output, and other build
artifacts:

```bash
dflow clean
```

The maintained `openlane/config.json` file is not removed. Only the generated
`openlane/runs/` directory is removed.

In the GUI, open the **Clean** tab and select or clear **OpenLane runs** along
with the other artifact categories before previewing or confirming cleanup.

## 11. Troubleshooting

### `openlane: missing`

Run:

```bash
dflow doctor
```

Then confirm one of the following:

- `openlane` is available on `PATH`.
- `asic.executable` points to an executable OpenLane wrapper.
- `asic.openlane_root` points to an OpenLane 2 checkout containing `flake.nix`,
  and `nix` is available.

### Nix fetch or lock-file errors

Enter the OpenLane environment once from a normal terminal with network access:

```bash
nix develop ~/openlane/openlane2#default
```

After it finishes, exit the shell and retry `dflow asic`. If an already realized
OpenLane wrapper exists, configure `asic.executable` to bypass flake evaluation.

### OpenLane cannot find RTL

Check that every `VERILOG_FILES` entry is relative to the OpenLane config
directory when using `dir::`. For a config at `openlane/config.json`, project
RTL is normally referenced as `dir::../rtl/<file>`.

### Top module or clock errors

Ensure that `DESIGN_NAME` exactly matches the synthesizable module name and that
`CLOCK_PORT` names a real top-level input. `CLOCK_PERIOD` is specified in
nanoseconds.

### GUI appears idle

OpenLane initialization and PDK loading can take time. Current OpenLane output
should stream into the GUI. Check the newest `reports/asic/openlane_*.log` if
the process exits, and run the quick lint command from a terminal to isolate
configuration problems.

### Invalid ASIC page options

The GUI validates that **Parallel jobs** is a positive integer. Start and end
steps must be valid OpenLane step IDs, such as `Verilator.Lint` or
`OpenROAD.GeneratePDN`. Inspect the output panel for OpenLane's available-step
error if a step ID is misspelled.

## 12. Running your project

From any initialized DFlow project with a valid `openlane/config.json`:

```bash
cd /path/to/your-project
source /path/to/dflow/activate.sh
dflow doctor
dflow asic -- --to Verilator.Lint --condensed
dflow asic -- --condensed
```

The relevant project files are:

```text
your-project/
├── flow.yaml
├── rtl/<design>.v
└── openlane/config.json
```

The quick lint command is recommended before every new design's first complete
physical run.
