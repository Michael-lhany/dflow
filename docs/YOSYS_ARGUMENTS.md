# Yosys Argument Reference

This reference covers **Yosys 0.33 (git sha1 2584903a060)**, the version used
to test DFlow. Yosys has many internal passes; this document lists every Yosys
executable argument plus the options for the synthesis, Liberty, mapping,
output, and statistics commands used by DFlow.

## Passing Arguments Through DFlow

DFlow appends arguments after `--` to `synthesis.options` from `flow.yaml`:

```bash
dflow synth -- -Q -q
```

```yaml
synthesis:
    tool: yosys
    top: counter
    options: [-Q]
    liberty: ${PDK_ROOT}/sky130A/libs.ref/sky130_fd_sc_hd/lib/<corner>.lib
```

Arguments passed this way are **Yosys executable options**, such as `-Q`, `-q`,
`-v`, and `-l`. Options for internal commands such as `synth -flatten` or
`abc -D` are not currently exposed as DFlow configuration fields. Although
Yosys accepts injected commands through `-p`, using that to modify DFlow's
generated flow is unsupported because DFlow supplies its own final `-p` script.

DFlow always discovers RTL under `rtl/`, selects `synthesis.top` or auto-detects
the top, and writes `build/synthesis/netlist.v` and `netlist.json`. When
`synthesis.liberty` is present, it performs Liberty cell mapping.

## Console Output and Logging

These options are safe to pass through `dflow synth --`.

| Argument | Purpose |
| --- | --- |
| `-Q` | Suppress the Yosys banner |
| `-T` | Suppress the footer, version, hash, and timing summary |
| `-q` | Print only warnings and errors; repeat as `-q -q` to hide warnings |
| `-v <level>` | Print log headers through a selected verbosity level |
| `-t` | Add timestamps to log messages |
| `-d` | Print detailed timing statistics at exit |
| `-l <file>` | Write messages to a log file |
| `-L <file>` | Write a line-buffered log file |

Example:

```bash
dflow synth -- -Q -t -l build/synthesis/yosys-extra.log
```

DFlow also captures Yosys output in `reports/synthesis/yosys.log`, so `-l` is
normally unnecessary.

## Input, Output, and Script Control

These are executable options, but DFlow already controls most of them.

| Argument | Purpose |
| --- | --- |
| `<infile>...` | Read input files after processing options |
| `-o <file>` | Write the final design to a file |
| `-b <backend>` | Choose the backend used by `-o` |
| `-f <frontend>` | Choose the frontend for command-line input files |
| `-S` | Run the default `synth` script |
| `-s <script.ys>` | Execute a Yosys script file |
| `-c <script.tcl>` | Execute a Tcl script file |
| `-C` | Enter the interactive Tcl shell |
| `-p <commands>` | Execute semicolon-separated Yosys commands |
| `-r <module>` | Elaborate command-line inputs using this top module |
| `-D <macro>[=<value>]` | Define a Verilog preprocessor macro |
| `-E <depsfile>` | Write Makefile-style input/output dependencies |

Avoid passing `-o`, `-b`, `-f`, `-S`, `-s`, `-c`, `-C`, `-p`, or positional
inputs through DFlow unless intentionally overriding its managed flow.

## Help, Plugins, Warnings, and Debugging

| Argument | Purpose |
| --- | --- |
| `-H` | Print the available Yosys command list |
| `-h <command>` | Print help for one internal command |
| `-V` | Print the Yosys version and exit |
| `-m <module>` | Load a Yosys plugin |
| `-W <regex>` | Print matching log messages as warnings |
| `-w <regex>` | Demote matching warnings to ordinary messages |
| `-e <regex>` | Promote matching warnings to errors and fail |
| `-x <feature>` | Suppress warnings for an experimental feature |
| `-g` | Enable global debug messages |
| `-X` | Trace internal design-data changes |
| `-M` | Randomize allocated pointer addresses slightly for debugging |
| `-A` | Call `abort()` at the end of execution |
| `-P <header>[:<file>]` | Dump the design at a log header; use `ALL` for every header |

Useful strict-check example:

```bash
dflow synth -- -e 'Warning:.*'
```

## `synth` Pass Options

DFlow generates either `synth -top <module>` or `synth -auto-top`. With a
Liberty file it adds `-noabc` and runs library-specific mapping afterward.
These options are documented for future configuration support.

| Option | Purpose |
| --- | --- |
| `-top <module>` | Select the top module |
| `-auto-top` | Automatically determine the top hierarchy |
| `-flatten` | Flatten hierarchy during synthesis |
| `-encfile <file>` | Supply an FSM recoding file |
| `-lut <k>` | Target a generic `k`-input LUT architecture |
| `-nofsm` | Disable FSM optimization |
| `-noabc` | Skip ABC mapping inside `synth` |
| `-noalumacc` | Keep arithmetic operations instead of using `alumacc` |
| `-nordff` | Prevent merging flip-flops into memory read ports |
| `-noshare` | Disable SAT-based resource sharing |
| `-run <from>[:<to>]` | Execute only part of the standard synthesis script |
| `-abc9` | Use the experimental ABC9 flow |
| `-flowmap` | Use FlowMap LUT technology mapping |
| `-no-rw-check` | Treat memory read/write collisions as don't-care |

## `read_verilog` Options

DFlow currently uses `read_verilog -sv <RTL sources>`.

### Language and Preprocessor

| Option | Purpose |
| --- | --- |
| `-sv` | Enable Yosys's supported SystemVerilog subset |
| `-formal` | Enable assertions/extensions and define `FORMAL` instead of `SYNTHESIS` |
| `-nosynthesis` | Do not define the `SYNTHESIS` macro automatically |
| `-Dname[=value]` | Define a preprocessor symbol |
| `-Idir` | Add an include search directory |
| `-ppdump` | Dump preprocessed Verilog |
| `-nopp` | Disable preprocessing |
| `-nodpi` | Disable DPI-C support |
| `-specify` | Parse and import `specify` blocks |

### Assertions and Elaboration

| Option | Purpose |
| --- | --- |
| `-noassert` | Ignore `assert` statements |
| `-noassume` | Ignore `assume` statements |
| `-norestrict` | Ignore `restrict` statements |
| `-assume-asserts` | Treat assertions as assumptions |
| `-assert-assumes` | Treat assumptions as assertions |
| `-nolatches` | Replace inferred latch hold behavior with `x` |
| `-nomem2reg` | Disable automatic early memory-to-register conversion |
| `-mem2reg` | Always convert memories to registers |
| `-nomeminit` | Convert initialized memories to registers instead of `$meminit` |
| `-noopt` | Disable basic frontend optimization |
| `-defer` | Defer AST compilation until a later `hierarchy` command |
| `-noautowire` | Treat implicit wires as disabled by default |
| `-pwires` | Create a wire for each module parameter |
| `-icells` | Interpret `$`-prefixed cells as internal cell types |

### Libraries, Attributes, and Diagnostics

| Option | Purpose |
| --- | --- |
| `-lib` | Import modules as black boxes and define `BLACKBOX` |
| `-noblackbox` | Do not mark empty modules automatically as black boxes |
| `-nowb` | Remove white-box attributes |
| `-nooverwrite` | Ignore conflicting module redefinitions |
| `-overwrite` | Replace existing modules with the same name |
| `-setattr <name>` | Add an attribute with value `1` to loaded modules |
| `-debug` | Enable all main AST/parser dumps and parser debugging |
| `-dump_ast1`, `-dump_ast2` | Dump AST before or after simplification |
| `-dump_vlog1`, `-dump_vlog2` | Dump Verilog before or after simplification |
| `-dump_rtlil` | Dump generated RTLIL |
| `-no_dump_ptr` | Exclude pointer addresses from dumps |
| `-yydebug` | Enable parser debugging |

## Liberty Loading and Flip-Flop Mapping

### `read_liberty`

DFlow uses `read_liberty -lib <file>` when `synthesis.liberty` is configured.

| Option | Purpose |
| --- | --- |
| `-lib` | Create empty black-box modules for library cells |
| `-wb` | Import library cells as white boxes |
| `-nooverwrite` | Ignore conflicting module definitions |
| `-overwrite` | Replace existing modules with matching names |
| `-ignore_miss_func` | Ignore cells whose outputs lack Boolean functions |
| `-ignore_miss_dir` | Ignore pins with missing or invalid directions |
| `-ignore_miss_data_latch` | Ignore latches missing data or enable pins |
| `-setattr <name>` | Add an attribute to every imported module |

### `dfflibmap`

DFlow runs `dfflibmap -liberty <file>` before combinational mapping.

| Option | Purpose |
| --- | --- |
| `-liberty <file>` | Select the target Liberty library; required |
| `-prepare` | Convert internal FFs to supported forms without mapping them |
| `-map-only` | Map only FF forms already matching available cells |
| `-info` | Print compatible target FFs without changing the design |
| `[selection]` | Restrict mapping to a Yosys design selection |

## ABC Technology-Mapping Options

DFlow currently runs `abc -liberty <file>`. These options are pass-level and
cannot yet be selected with dedicated `flow.yaml` fields.

### Target and Timing

| Option | Purpose |
| --- | --- |
| `-liberty <file>` | Map logic using a Liberty cell library |
| `-genlib <file>` | Map logic using a SIS Genlib library |
| `-constr <file>` | Supply ABC driving-cell and output-load constraints |
| `-D <picoseconds>` | Set the mapping delay target |
| `-lut <width>` | Map to one LUT width |
| `-lut <min>:<max>` | Use equal cost through `min`, then increasing LUT cost |
| `-luts <costs>` | Supply explicit costs for multiple LUT sizes |
| `-sop` | Map to sum-of-products and inverter cells |
| `-g <types>` | Select generic gate types such as `cmos`, `gates`, or `aig` |

An ABC constraint file is not SDC. It contains exactly these concepts:

```text
set_driving_cell <library_cell>
set_load <femtofarads>
```

### Mapping Behavior

| Option | Purpose |
| --- | --- |
| `-fast` | Use a faster, lower-quality mapping script |
| `-script <file>` | Use a custom ABC script; `+...` supplies an inline script |
| `-exe <command>` | Select an alternate ABC executable |
| `-I <count>` | Limit SOP inputs |
| `-P <count>` | Limit SOP products |
| `-S <count>` | Limit shared LUT inputs |
| `-dff` | Include supported FF cells in ABC mapping |
| `-clk [!]<clock>[,[!]<enable>]` | Restrict mapping to one clock domain |
| `-keepff` | Preserve flip-flop output wires |
| `-dress` | Attempt experimental name preservation after mapping |
| `-markgroups` | Mark cells with their ABC mapping group |
| `-nocleanup` | Preserve ABC temporary files |
| `-showtmp` | Print ABC temporary-directory names |
| `[selection]` | Restrict mapping to selected design objects |

## Netlist Output Options

### `write_verilog`

DFlow uses `write_verilog -noattr build/synthesis/netlist.v`.

| Option | Purpose |
| --- | --- |
| `-sv` | Emit SystemVerilog constructs where applicable |
| `-norename` | Preserve internal `$` names instead of shortening them |
| `-renameprefix <prefix>` | Prefix auto-generated instance names |
| `-noattr` | Omit Yosys attributes; enabled by DFlow |
| `-attr2comment` | Write attributes as comments |
| `-noexpr` | Keep internal cells instead of converting them to expressions |
| `-noparallelcase` | Avoid `parallel_case` attributes |
| `-siminit` | Emit initialization statements for flip-flops |
| `-nodec` | Avoid decimal formatting of 32-bit constants |
| `-decimal` | Prefer decimal formatting for 32-bit constants |
| `-nohex` | Avoid hexadecimal constant formatting |
| `-nostr` | Emit string parameters and attributes as binary values |
| `-simple-lhs` | Use only simple assignment left-hand sides |
| `-extmem` | Write memory initialization to separate `.mem` files |
| `-defparam` | Use `defparam` instead of parameterized instances |
| `-blackboxes` | Write only black-box modules |
| `-selected` | Write only fully selected modules |
| `-v` | Print renamed wires and cells |

### `write_json`

| Option | Purpose |
| --- | --- |
| `-aig` | Include AIG models for supported cell types |
| `-compat-int` | Store small fully defined parameters as JSON integers |

## Statistics Options

DFlow runs `stat -liberty <file>` for a mapped design.

| Option | Purpose |
| --- | --- |
| `-top <module>` | Report hierarchy using a selected top module |
| `-liberty <file>` | Include cell-area information from a Liberty library |
| `-tech <technology>` | Estimate area using `xilinx` or `cmos` models |
| `-width` | Include internal cell widths in type names |
| `-json` | Print statistics as JSON |
| `[selection]` | Restrict statistics to selected design objects |

## Practical Examples

Quiet synthesis while keeping DFlow's report:

```bash
dflow synth -- -Q -q
```

Treat every Yosys warning as an error:

```bash
dflow synth -- -e 'Warning:.*'
```

Use a project-relative library:

```yaml
synthesis:
    tool: yosys
    top: top
    liberty: constraints/cells.lib
```

Use an external PDK without committing a machine-specific path:

```bash
export PDK_ROOT=/opt/pdks
dflow synth
```

## Choosing the Right Section

- Use **Console Output and Logging** for supported temporary CLI arguments.
- Use `synthesis.top` and `synthesis.liberty` for reproducible project settings.
- Use **`synth` Pass Options** when planning future synthesis controls.
- Use **Liberty Loading** and **ABC Technology Mapping** for ASIC cell mapping.
- Use **Netlist Output** and **Statistics** when extending generated artifacts.
- Do not confuse ABC's two-line constraint format with SDC timing constraints.
