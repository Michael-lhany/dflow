# Synopsys Tools Guide

DFlow can use Synopsys VCS for `compile` and `sim`, then open FSDB waveforms
with Verdi. It can also lint RTL with SpyGlass and synthesize with Design
Compiler. These commercial tools are not bundled with DFlow.

## Configuration

Configure the stages independently in `flow.yaml`:

```yaml
compile:
    tool: vcs
    top: counter

simulation:
    tool: vcs
    top: counter_tb

waveform:
    tool: verdi

lint:
    tool: spyglass
    top: counter

synthesis:
    tool: dc
    top: counter
    setup: scripts/dc_setup.tcl
    constraints: constraints/counter.sdc
```

`compile.top` is optional. `simulation.top` is inferred only when `tb/`
contains exactly one source file; configuring it explicitly is recommended.

The default compile options are:

```text
-full64 -sverilog
```

The simulation build defaults add:

```text
-timescale=1ns/1ps -debug_access+all -kdb
```

Replace these defaults with `options`. Temporary arguments supplied after `--`
are appended to them:

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
        - +define+RTL_SIM
```

```bash
dflow sim -- +incdir+rtl/include
```

## Runtime and waveforms

By default, DFlow runs the generated `simv` without additional runtime
arguments. Set `simulation.runtime_options` for UVM test names and normal
simulation plusargs:

```yaml
simulation:
    tool: vcs
    top: counter_tb
    runtime_options:
        - +UVM_TESTNAME=counter_smoke
        - +ntb_random_seed=1
```

The testbench is responsible for waveform dumping. Call `$fsdbDumpfile` and
`$fsdbDumpvars`, writing the FSDB beneath `sim/waves/` so
`dflow sim --wave` can find it. For example:

```systemverilog
initial begin
    $fsdbDumpfile("sim/waves/counter_tb.fsdb");
    $fsdbDumpvars(0, counter_tb);
end
```

Recent VCS/Verdi releases support native FSDB integration with the default
`-kdb` debug build. Older site installations may also require their documented
FSDB PLI options in `simulation.options`. Verdi selects the newest `.fsdb` or
`.vcd` recursively under `sim/waves/` and launches it with `verdi -ssf`.

## Commands and outputs

```bash
dflow doctor
dflow compile
dflow lint
dflow sim
dflow sim --wave
dflow sim --wave-only
dflow synth
```

VCS compile output is isolated under `sim/vcs_compile/`. Simulation output is
under `sim/vcs/`, waveforms remain under `sim/waves/`, and reports are written
under `reports/compile/` and `reports/sim/`.

## Manual validation

On a licensed Synopsys host, first source the site setup that adds the selected
Synopsys tools to `PATH` and configures the license environment. Then verify:

1. `dflow doctor` reports both `vcs` and `verdi` as found.
2. `dflow compile` creates `sim/vcs_compile/simv` and a passing report.
3. `dflow sim` creates `sim/vcs/simv`, runs the testbench, and creates the
   testbench-managed FSDB under `sim/waves/`.
4. `dflow sim --wave-only` launches the newest waveform in Verdi.
5. A deliberate RTL error returns VCS's nonzero status and does not run the
   simulation binary.
6. `dflow lint` creates a SpyGlass work directory and lint report.
7. `dflow synth` creates the expected DC netlist and QoR reports.

If VCS rejects a default option in the installed release, copy the desired
defaults into `simulation.options` and adjust them there. DFlow passes the list
directly to VCS without shell interpretation.

## SpyGlass lint

With `lint.tool: spyglass`, DFlow discovers RTL under `rtl/`, creates
`build/lint/spyglass/dflow.prj`, and runs the default `lint/lint_rtl` goal in
batch mode. Set `lint.goal` for another installed GuideWare goal, or point
`lint.project` at a maintained SpyGlass `.prj` file when the design requires
waivers, include paths, macros, or methodology-specific settings.

```yaml
lint:
    tool: spyglass
    project: scripts/counter.prj
    goal: lint/lint_rtl
    options:
        - -64bit
```

Command-line options are appended to `lint.options`:

```bash
dflow lint -- -64bit
```

## Design Compiler synthesis

The Design Compiler backend invokes `dc_shell` and requires
`synthesis.top`. A minimal generic run is:

```yaml
synthesis:
    tool: dc
    top: counter
```

Production mapped synthesis normally adds site/library setup and constraints:

```yaml
synthesis:
    tool: dc
    top: counter
    setup: scripts/dc_setup.tcl
    constraints: constraints/counter.sdc
    target_libraries: [slow.db]
    link_libraries: ["*", slow.db]
    compile_ultra: true
```

The generated `build/synthesis/dc/run.tcl` analyzes SystemVerilog, elaborates
and links the configured top, sources constraints, compiles, and writes
`netlist.v`, `design.ddc`, `constraints.sdc`, plus QoR, area, and timing
reports. `compile_ultra` is opt-in because it needs the corresponding license.
Set `synthesis.executable` when `dc_shell` is not exposed under its standard
name.

Before running either backend, source the site's Synopsys environment so the
executables and license variables are available. `dflow doctor` checks
`spyglass` and the configured Design Compiler executable; only a real lint or
synthesis run can validate licenses and technology-library setup.
