# Writing `flow.yaml`

Every DFlow project has one `flow.yaml` file in its root, beside `.dflow`.
The file selects a backend for each flow and supplies backend-specific values.

## YAML structure

Each flow is a top-level mapping. Indent nested values with spaces, not tabs:

```yaml
project:
    name: counter

compile:
    tool: verilator
```

Tool arguments must be a YAML list of strings:

```yaml
lint:
    tool: verilator
    options:
        - --lint-only
        - -Wall
```

Quote a value when YAML could interpret it as another data type or when it
contains special YAML characters:

```yaml
simulation:
    tool: vcs
    runtime_options:
        - "+UVM_TESTNAME=counter_smoke"
        - "+ntb_random_seed=1"
```

Unknown top-level sections and unknown fields are currently ignored. A flow
section must be a mapping, and `tool` must be a non-empty string.

## Complete open-source example

```yaml
project:
    name: counter

compile:
    tool: verilator
    options:
        - --cc

lint:
    tool: verilator
    options:
        - --lint-only
        - -Wall

simulation:
    tool: verilator
    top: counter_tb

waveform:
    tool: gtkwave

synthesis:
    tool: yosys
    top: counter

formal:
    tool: sby
    config: formal/counter.sby

asic:
    tool: openlane
    config: openlane/config.json
```

Remove sections for flows that the project does not use.

## Complete Synopsys example

```yaml
project:
    name: counter

compile:
    tool: vcs
    top: counter

lint:
    tool: spyglass
    top: counter

simulation:
    tool: vcs
    top: counter_tb
    runtime_options:
        - "+UVM_TESTNAME=counter_smoke"
        - "+ntb_random_seed=1"

waveform:
    tool: verdi

synthesis:
    tool: dc
    top: counter
    setup: scripts/dc_setup.tcl
    constraints: constraints/counter.sdc
```

VCS simulation compile options and runtime options are separate. The testbench
must write its FSDB file beneath `sim/waves/` for the Verdi backend to find it.

## `project`

```yaml
project:
    name: counter
```

`name` is project metadata displayed by DFlow. It does not rename the project
directory or HDL top module.

## `compile`

### Verilator

```yaml
compile:
    tool: verilator
    options:
        - --cc
```

The default Verilator compile options are `--cc`. `top` is not used by this
backend; pass a Verilator top option in `options` when needed.

### VCS

```yaml
compile:
    tool: vcs
    top: counter
    options:
        - -full64
        - -sverilog
        - "+define+RTL"
```

Supported fields:

| Field | Meaning |
| --- | --- |
| `tool` | Must be `vcs` |
| `top` | Optional elaboration top passed through `-top` |
| `options` | VCS compile and elaboration arguments |

When `options` is omitted, VCS defaults to `-full64 -sverilog`.

## `lint`

```yaml
lint:
    tool: verilator
    options:
        - --lint-only
        - -Wall
        - --Wno-fatal
```

The Verilator backend defaults to `--lint-only` and `-Wall`.

### SpyGlass

```yaml
lint:
    tool: spyglass
    top: counter
    goal: lint/lint_rtl
    options:
        - -64bit
```

DFlow generates `build/lint/spyglass/dflow.prj` from the RTL sources and runs
SpyGlass in batch mode. `top` is optional and `goal` defaults to
`lint/lint_rtl`. To use a maintained project instead, configure its path:

```yaml
lint:
    tool: spyglass
    project: scripts/counter.prj
    goal: lint/lint_rtl
```

`project` may be absolute, project-relative, use `~`, or contain environment
variables. When present, it replaces DFlow's generated project; `top` is then
owned by that file. `options` contains SpyGlass process arguments.

## `simulation`

### Verilator

```yaml
simulation:
    tool: verilator
    top: counter_tb
    options:
        - --cc
        - --exe
        - --main
        - --trace
        - --timing
        - --timescale
        - 1ns/1ps
```

`top` names the testbench top module. If it is omitted, DFlow uses the filename
stem when `tb/` contains exactly one source. Configure `top` explicitly when
there are multiple testbench sources.

When `options` is omitted, the complete list shown above is used.

### VCS

```yaml
simulation:
    tool: vcs
    top: counter_tb
    options:
        - -full64
        - -sverilog
        - -timescale=1ns/1ps
        - -debug_access+all
        - -kdb
        - "+define+RTL_SIM"
    runtime_options:
        - "+UVM_TESTNAME=counter_smoke"
        - "+ntb_random_seed=1"
```

Supported fields:

| Field | Meaning |
| --- | --- |
| `tool` | Must be `vcs` |
| `top` | Testbench top passed through `-top` |
| `options` | Arguments used while building `simv` |
| `runtime_options` | Arguments passed to the generated `simv` executable |

When `options` is omitted, VCS uses `-full64`, `-sverilog`,
`-timescale=1ns/1ps`, `-debug_access+all`, and `-kdb`.
`runtime_options` defaults to an empty list.

## `waveform`

Use GTKWave for VCD files:

```yaml
waveform:
    tool: gtkwave
```

Use Verdi for FSDB files:

```yaml
waveform:
    tool: verdi
```

When the section or `tool` is omitted, the viewer defaults to `gtkwave` for
backward compatibility. Both viewers search recursively under `sim/waves/` and
select the newest supported file.

## `synthesis`

### Yosys

```yaml
synthesis:
    tool: yosys
    top: counter
    liberty: ${PDK_ROOT}/sky130A/libs.ref/sky130_fd_sc_hd/lib/corner.lib
    options:
        - -Q
```

Supported fields:

| Field | Meaning |
| --- | --- |
| `tool` | Must be `yosys` |
| `top` | Optional synthesis top; Yosys auto-detects it when omitted |
| `liberty` | Optional standard-cell Liberty file for technology mapping |
| `options` | Yosys process arguments |

`liberty` may be absolute, relative to the project root, use `~`, or contain
environment variables such as `${PDK_ROOT}`. The file must exist.

### Design Compiler

```yaml
synthesis:
    tool: dc
    top: counter
    setup: scripts/dc_setup.tcl
    constraints: constraints/counter.sdc
    target_libraries:
        - slow.db
    link_libraries:
        - "*"
        - slow.db
    compile_ultra: true
    options:
        - -no_gui
```

Supported fields:

| Field | Meaning |
| --- | --- |
| `tool` | `dc` (recommended), `dc_shell`, or `design_compiler` |
| `top` | Required elaboration top module |
| `setup` | Optional Tcl file sourced before RTL analysis |
| `constraints` | Optional Tcl/SDC file sourced after link |
| `target_libraries` | Optional list assigned to `target_library` |
| `link_libraries` | Optional list assigned to `link_library` |
| `compile_ultra` | Use `compile_ultra` when true; defaults to `compile` |
| `executable` | Optional explicit `dc_shell` executable path |
| `options` | Design Compiler process arguments |

DFlow generates `build/synthesis/dc/run.tcl`, a Verilog netlist, DDC and SDC
outputs, and QoR, area, and timing reports. The optional setup script is the
right place for site-specific search paths and library setup. Path fields may
be absolute, project-relative, use `~`, or contain environment variables; they
must exist before the output directory is cleaned.

## `formal`

```yaml
formal:
    tool: sby
    config: formal/counter.sby
    tasks:
        - prove
        - cover
    output_directory: formal/runs
    options:
        - -j
        - "4"
```

Supported fields:

| Field | Meaning |
| --- | --- |
| `tool` | `sby` or `symbiyosys` |
| `config` | SymbiYosys `.sby` file; defaults to `formal/design.sby` |
| `tasks` | Optional list of task names from the `.sby` file |
| `output_directory` | Run root; defaults to `formal/runs` |
| `executable` | Optional explicit executable path |
| `options` | SymbiYosys command-line arguments |

Path fields may be absolute, project-relative, use `~`, or contain environment
variables. `tasks` must contain only non-empty strings.

## `asic`

For an `openlane` executable already on `PATH`:

```yaml
asic:
    tool: openlane
    config: openlane/config.json
    flow: Classic
    pdk: sky130A
    scl: sky130_fd_sc_hd
    pdk_root: ${PDK_ROOT}
    run_tag: counter_run
    options:
        - --condensed
```

For an OpenLane 2 Nix checkout:

```yaml
asic:
    tool: openlane
    openlane_root: ~/openlane/openlane2
    config: openlane/config.json
```

Supported fields:

| Field | Meaning |
| --- | --- |
| `tool` | Must be `openlane` |
| `config` | OpenLane JSON, YAML, YML, or Tcl design configuration |
| `executable` | Optional explicit OpenLane executable path |
| `openlane_root` | Optional OpenLane 2 checkout containing `flake.nix` |
| `flow` | Value passed to OpenLane's `--flow` |
| `pdk` | Value passed to `--pdk` |
| `scl` | Value passed to `--scl` |
| `pdk_root` | Path passed to `--pdk-root` |
| `run_tag` | Value passed to `--run-tag` |
| `options` | Additional OpenLane arguments |

`config` defaults to `openlane/config.json`. Path fields support absolute and
project-relative paths, `~`, and environment variables. The OpenLane design
configuration is a separate file; its design-specific values do not belong in
DFlow's `flow.yaml`.

## Options and defaults

For `options`, omitting the field uses that backend's defaults:

```yaml
compile:
    tool: vcs
```

Providing a list replaces the defaults completely:

```yaml
compile:
    tool: vcs
    options:
        - -sverilog
```

An explicit empty list disables every default option:

```yaml
compile:
    tool: vcs
    options: []
```

Therefore, include required language, timing, and debug flags whenever
overriding a complete default list. Empty strings and non-string entries in an
`options` list are ignored.
