# SymbiYosys formal verification with DFlow

This guide covers installing standalone SymbiYosys, configuring a DFlow
project, writing properties, running formal tasks from the CLI and GUI,
reading results, opening counterexample traces, and cleaning generated runs.

SymbiYosys is invoked as `sby`. It coordinates Yosys, a formal engine, and a
solver to prove assertions, find bounded assertion failures, and reach cover
statements. DFlow manages the command, timestamped work directories, saved
reports, project status, tool checks, GUI controls, and cleanup.

## 1. Installation

The recommended standalone source installation is:

```bash
git clone https://github.com/YosysHQ/sby.git
cd sby
make install PREFIX="$HOME/.local"
```

Ensure `$HOME/.local/bin` is on `PATH`. SymbiYosys also requires Yosys,
`yosys-smtbmc`, and at least one supported solver. The counter example uses
Z3. Verify the complete tool chain:

```bash
command -v sby yosys yosys-smtbmc z3
sby --version
z3 --version
```

The official source and reference documentation are:

- <https://github.com/YosysHQ/sby>
- <https://yosyshq.readthedocs.io/projects/sby/en/stable/>

This workstation currently has standalone SBY v0.68 under `~/.local` and a
standalone Z3 5.0.0 executable on the same user-local `PATH`.

## 2. DFlow project configuration

Add a `formal` section to `flow.yaml`:

```yaml
formal:
    tool: sby
    config: formal/counter.sby
    tasks:
        - prove
        - cover
```

Supported DFlow keys are:

| Key | Meaning |
| --- | --- |
| `tool` | Use `sby` or the alias `symbiyosys` |
| `config` | Path to the maintained `.sby` job file |
| `tasks` | Optional list of SBY tasks; omitted means the job defaults |
| `options` | SBY command options placed before the job file |
| `output_directory` | Generated run root; defaults to `formal/runs` |
| `executable` | Optional explicit path to `sby` when it is not on `PATH` |

Paths are relative to the DFlow project root. Environment variables and `~`
are expanded. Do not put `-d` or `--prefix` in `options`; DFlow supplies a
unique timestamped prefix so previous results remain intact.

Check the configured installation with:

```bash
dflow doctor
dflow status
```

`doctor` reports `sby: found` when the executable is usable. Solver
availability is ultimately checked by SBY when the selected engine starts.

## 3. Anatomy of an `.sby` job

The counter example uses `formal/counter.sby`:

```ini
[tasks]
prove :default
cover :default
fail

[options]
prove: mode prove
prove: depth 20
cover: mode cover
cover: depth 40
fail: mode bmc
fail: depth 10
multiclock on

[engines]
smtbmc z3

[script]
prove: read -formal -sv counter.v counter_formal.sv
cover: read -formal -sv counter.v counter_formal.sv
fail: read -formal -D INTENTIONAL_FAILURE -sv counter.v counter_formal.sv
prep -top counter_formal

[files]
counter.v rtl/counter.v
counter_formal.sv formal/counter_formal.sv
```

The sections have distinct jobs:

- `[tasks]` names independently selectable runs.
- `[options]` selects `prove`, `bmc`, `cover`, or `live` mode and its depth.
- `[engines]` chooses an engine and solver. Here `smtbmc z3` uses Z3.
- `[script]` reads the copied sources and prepares the formal top module.
- `[files]` lists every input copied into each isolated SBY work directory.

The `name source-path` form in `[files]` gives a stable basename to the copied
file. DFlow launches SBY from the project root, so the source paths on the
right are project-relative. Direct SBY runs resolve them from the shell's
current working directory as well.

## 4. Assertions, assumptions, and covers

The formal harness lives in `formal/counter_formal.sv` and instantiates the
maintained RTL. It contains three kinds of formal property:

- `assert(expression)` describes behavior that must always hold.
- `assume(expression)` constrains unconstrained inputs or the environment.
- `cover(expression)` asks the solver to find a reachable execution.

The counter proof asserts that reset clears the count and that each enabled
clock advances the count by one. Its cover statement searches for a trace that
reaches `4'hf`.

Guard `$past(...)` with a valid-history register. The first formal timestep has
no previous value. Keep environmental assumptions realistic: an assertion
proved only because of an over-restrictive assumption is not useful evidence.

The open-source Yosys frontend supports immediate assertions and formal helper
functions such as `$past`, `$stable`, `$rose`, and `$fell`. Full commercial SVA
support is a separate capability, so prefer the supported immediate-property
style for portable open-source jobs.

## 5. Running from the CLI

From an initialized project with a configured `.sby` file:

```bash
cd /path/to/your-project
dflow formal
```

Run only one task:

```bash
dflow formal --task prove
dflow formal -t cover
```

Repeat `--task` to select multiple tasks:

```bash
dflow formal -t prove -t cover
```

Temporarily use another job file:

```bash
dflow formal --config formal/experiment.sby
```

Pass raw SBY options after `--`:

```bash
dflow formal --task prove -- -j 4 --live jsonl
dflow formal -- --sequential
dflow formal -- --setup
```

The general form is:

```text
dflow formal [--config FILE] [--task NAME ...] [-- SBY_OPTIONS...]
```

Task names are positional arguments to SBY and therefore belong in DFlow's
`--task` option, not after the `--` separator.

## 6. Running from the GUI

Launch the GUI from a terminal that has `~/.local/bin` on `PATH`:

```bash
dflow gui
```

Open the **Formal** page. Its controls are:

| Control | Effect |
| --- | --- |
| **SBY configuration** | Optional `--config` override |
| **Tasks** | Space-separated repeated `--task` selections |
| **Parallel jobs** | Passes `-j N` to SBY |
| **Run tasks sequentially** | Passes `--sequential` |
| **Stream property status** | Passes `--live jsonl` |
| **Extra SBY arguments** | Additional arguments such as `--autotune` |
| **Run Formal Verification** | Starts the command and streams its output |

Leave configuration and tasks blank to use `flow.yaml`. For the counter
example, enter `prove` to run only the unbounded safety proof or `cover` to
generate the reachability trace.

## 7. Results and traces

Every invocation gets a unique run prefix below:

```text
formal/runs/<job>_<timestamp>_<task>/
```

An SBY task directory normally contains `logfile.txt`, a copied `src/` tree,
generated models, engine logs, status data, and traces. A passing proof ends in
`PASS`. A failing assertion ends in `FAIL` and normally creates a VCD trace in
an engine directory. A cover task passes when all requested cover statements
are reached.

DFlow separately preserves the complete wrapper output:

```text
reports/formal/sby_<timestamp>.log
```

Open a VCD counterexample or cover trace with:

```bash
gtkwave formal/runs/<run>/<engine>/trace.vcd
```

Use `find formal/runs -name '*.vcd'` if the engine created a nested trace with
a different name.

## 8. Understanding outcomes

- `PASS` in `prove` means the configured engines established every assertion
  under the stated assumptions.
- `FAIL` in `prove` or `bmc` means a counterexample was found; inspect the
  assertion location and trace.
- `PASS` in `cover` means every cover statement was reached within the depth.
- `FAIL` in `cover` commonly means the requested state was not reached within
  the configured depth, not necessarily that it is unreachable forever.
- `UNKNOWN` means the selected engine could not complete the requested proof.
  Try a deeper bound, another engine, or a stronger inductive invariant.

The DFlow command returns SBY's exit code, records it in the formal report, and
shows the latest result in `dflow status`.

## 9. Intentional failure demonstration

The counter job also contains an opt-in `fail` task. It defines
`INTENTIONAL_FAILURE`, enabling a deliberately false assertion that says the
enabled counter must remain zero. The task is not listed in `flow.yaml`, so a
normal `dflow formal` still runs only the passing `prove` and `cover` tasks.

Run the demonstration explicitly:

```bash
dflow formal --task fail
```

An exit code of 2 and `DONE (FAIL)` are expected. The counterexample is written
to a path like:

```text
formal/runs/counter_<timestamp>_fail/engine_0/trace.vcd
```

Open it with GTKWave, expand `counter_formal`, and add `clk`, `rst_n`, and
`count`. The trace shows reset release and the count changing from zero to one,
which contradicts the demonstration assertion.

## 10. Cleanup and Git

Formal runs and reports are generated data. They are ignored by the repository
through `**/formal/runs/` and `reports/` rules.

Preview formal cleanup:

```bash
dflow clean --dry-run --only formal
```

Remove only formal work directories:

```bash
dflow clean --only formal
```

This preserves maintained `.sby` files and formal harness sources. Cleaning
reports is separate:

```bash
dflow clean --only reports
```

The GUI exposes the same operation as **SymbiYosys runs** on the Clean page.

## 11. Troubleshooting

### `sby` is missing

Confirm `~/.local/bin` is exported before starting DFlow or its GUI:

```bash
export PATH="$HOME/.local/bin:$PATH"
command -v sby
```

### Solver is missing

If an engine reports that `z3` cannot be found, install it and check
`command -v z3`. Alternatively change `[engines]` to a solver that is already
installed and supported by the chosen engine.

### Existing work directory

DFlow normally prevents this with timestamped prefixes. Avoid passing `-d` or
`--prefix` yourself. Direct `sby` runs can use `-f` to replace an existing work
directory, but that discards its previous contents.

### Source cannot be opened

List the source in `[files]`, then read its copied basename in `[script]`.
When using DFlow, maintained source paths are interpreted relative to the
DFlow project root.

### Proof passes too easily

Check for vacuous properties: verify the clock toggles, reset is eventually
released, assumptions permit realistic traffic, and cover statements reach
meaningful states. Running a complementary cover task is a useful sanity check.
