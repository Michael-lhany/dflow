# Verilator Argument Reference

This reference covers the arguments reported by the installed **Verilator
5.050 (2026-07-01)**. Check the
[official Verilator executable reference](https://verilator.org/guide/latest/exe_verilator.html)
when using another version because options can be added, renamed, or removed.

## Passing Arguments Through DFlow

DFlow appends arguments after `--` to the options from `flow.yaml`, or to the
backend defaults when that section has no `options` list:

```bash
dflow lint -- -Wno-fatal
dflow compile -- --output-split 20000
dflow sim -- --threads 4 --trace-fst
```

The current defaults are:

| Flow | Verilator defaults |
| --- | --- |
| Lint | `--lint-only -Wall` |
| Compile | `--cc` |
| Simulation build | `--cc --exe --main --trace --timing` |

The simulation arguments above configure the **Verilator build**. Runtime
`+verilator+...` arguments belong to the generated simulation executable and
are listed separately below. DFlow does not currently provide a CLI channel for
runtime plusargs.

## Input Files

| Argument | Purpose |
| --- | --- |
| `<file.v>`, `<file.sv>` | Verilog or SystemVerilog design source |
| `<file.c>`, `<file.cc>`, `<file.cpp>` | C/C++ source linked into a model |
| `<file.a>`, `<file.o>`, `<file.so>` | Prebuilt object, archive, or shared library |

## Lint and Diagnostics

These options are primarily useful with `dflow lint`, although warning flags
also apply during compile and simulation builds.

| Argument | Purpose |
| --- | --- |
| `--lint-only` | Parse, elaborate, and lint without generating a model |
| `-Wall` | Enable the main style-warning set |
| `-Wpedantic` | Enable strict language-compliance warnings |
| `-Werror-<message>` | Promote one warning category to an error |
| `-Wwarn-<message>` | Enable one warning category |
| `-Wno-<message>` | Disable one warning category |
| `-Wfuture-<message>` | Accept an unknown warning name for forward compatibility |
| `-Wwarn-lint`, `-Wno-lint` | Enable or disable lint-warning categories |
| `-Wwarn-style`, `-Wno-style` | Enable or disable style-warning categories |
| `-Wno-fatal` | Do not exit merely because warnings occurred |
| `-Wno-context` | Omit source context from diagnostics |
| `--error-limit <count>` | Stop after a selected number of errors |
| `--if-depth <depth>` | Set the threshold for deep-if warnings |
| `--unused-regexp <regexp>` | Define names treated as intentionally unused |
| `--report-unoptflat` | Add details for UNOPTFLAT diagnostics |
| `--diagnostics-sarif` | Emit diagnostics in SARIF form |
| `--diagnostics-sarif-output <file>` | Select the SARIF output file |
| `--waiver-output <file>` | Generate warning-waiver configuration |
| `--waiver-multiline` | Generate multiline waiver matches |
| `--no-std-waiver` | Do not load the standard waiver file |

Example:

```bash
dflow lint -- -Wpedantic -Werror-WIDTH -Wno-UNUSEDSIGNAL
```

## Compilation and Model Generation

### Output Mode and Build

| Argument | Purpose |
| --- | --- |
| `--cc` | Generate a C++ model |
| `--sc` | Generate a SystemC model |
| `--binary` | Generate and build an executable model |
| `--build` | Build after model generation |
| `--exe` | Link supplied C/C++ sources into an executable |
| `--main` | Generate a basic C++ `main()` |
| `--main-top-name` | Pass the top name to the generated main program |
| `--make <tool>` | Select the generated build-system format |
| `--build-jobs <jobs>` | Set build parallelism |
| `--verilate-jobs <jobs>` | Set Verilation-stage parallelism |
| `-j <jobs>` | Set build and Verilation parallelism together |
| `--build-dep-bin <file>` | Override the Verilator dependency recorded for builds |
| `--no-verilate` | Build previously generated output without regenerating it |
| `--Mdir <directory>` | Select the generated object directory |
| `-o <file>` | Select the final executable name |
| `-CFLAGS <flags>` | Add C++ compiler flags to the generated build |
| `-LDFLAGS <flags>` | Add linker flags before linked objects |
| `-MAKEFLAGS <flags>` | Pass flags to Make during `--build` |
| `--compiler <name>` | Tune generated C++ for a compiler family |
| `--compiler-include` | Add compiler support to the precompiled header |
| `--MMD` | Generate dependency files |
| `--MP` | Add phony dependency targets |
| `--no-skip-identical` | Regenerate output even when unchanged |
| `--quiet-build` | Suppress build progress |

### Generated Model Interface

| Argument | Purpose |
| --- | --- |
| `--prefix <name>` | Set the generated top-class prefix |
| `--mod-prefix <name>` | Set the prefix for generated lower-level classes |
| `--l2-name <name>` | Set the Verilog scope name of the top model |
| `--emit-accessors` | Generate top-model getter and setter methods |
| `--dpi-hdr-only` | Generate only the DPI header |
| `--lib-create <name>` | Build a DPI library |
| `--protect-lib <name>` | Build a protected DPI library |
| `--vpi` | Include VPI support in the model |
| `--savable` | Generate model save/restore support |
| `--pins-bv <bits>` | Use SystemC bit-vector ports above a width |
| `--pins-inout-enables` | Split inouts into output and enable signals |
| `--pins-sc-biguint` | Use `sc_biguint` ports |
| `--pins-sc-uint` | Use `sc_uint` ports |
| `--pins-sc-uint-bool` | Use `sc_uint` and Boolean ports |
| `--pins-uint8` | Use smallest-width integer port types |
| `--no-pins64` | Avoid 64-bit types for ports between 33 and 64 bits |
| `--public` | Make selected model objects publicly accessible |
| `--public-depth <depth>` | Apply public visibility to a module depth |
| `--public-flat-rw` | Make flattened variables publicly read/write |
| `--public-ignore` | Ignore public metacomments |
| `--public-params` | Expose parameters publicly |
| `--private` | Enable the internal private/debug visibility mode |

### Output Size and Layout

| Argument | Purpose |
| --- | --- |
| `--output-groups <count>` | Group generated C++ into a chosen number of files |
| `--output-split <statements>` | Split large generated C++ files |
| `--output-split-cfuncs <statements>` | Split large generated functions |
| `--output-split-ctrace <statements>` | Split large generated tracing functions |
| `--decorations <level>` | Control generated comments and whitespace |
| `--no-decoration` | Minimize generated comments and spacing |

## Simulation Build Options

### Timing, Assertions, and Values

| Argument | Purpose |
| --- | --- |
| `--timing`, `--no-timing` | Enable or disable timing-control support |
| `--timescale <unit/precision>` | Supply a default timescale |
| `--timescale-override <unit/precision>` | Replace every source timescale |
| `--sched-zero-delay` | Enable supported `#0` scheduling |
| `--converge-limit <loops>` | Set the settle-loop convergence limit |
| `--no-assert` | Disable all assertions |
| `--no-assert-case` | Disable unique/priority-case assertions |
| `--assert-unroll-limit <iterations>` | Limit repeated SVA assertion expansion |
| `--no-stop-fail` | Prevent `$stop` from failing the simulation |
| `--autoflush` | Flush output streams after displays |
| `--fourstate`, `--no-fourstate` | Enable or disable four-state model support |
| `--x-assign <mode>` | Select handling of non-initial X assignments |
| `--x-initial <mode>` | Select initialization of X values |
| `--x-initial-edge` | Trigger initial X-to-known edge behavior |
| `--runtime-debug` | Add runtime model debugging support |

### Threads and DPI

| Argument | Purpose |
| --- | --- |
| `--threads <count>` | Generate a multithreaded model |
| `--threads-dpi <mode>` | Configure DPI behavior with threads |
| `--threads-max-mtasks <count>` | Limit model task partitions |
| `--instr-count-dpi <count>` | Estimate DPI-import execution cost |

### Tracing

| Argument | Purpose |
| --- | --- |
| `--trace`, `--trace-vcd` | Compile VCD tracing support |
| `--trace-fst` | Compile FST tracing support |
| `--trace-saif` | Compile SAIF activity tracing support |
| `--trace-depth <levels>` | Limit traced hierarchy depth |
| `--trace-max-array <depth>` | Limit traced array depth |
| `--trace-max-width <width>` | Limit traced signal width |
| `--trace-params` | Trace parameter values |
| `--trace-structs` | Preserve structure names in traces |
| `--trace-underscore` | Trace identifiers beginning with underscore |
| `--no-trace-top` | Exclude top-module signals from generated tracing |
| `--trace-coverage` | Trace coverage information |

### Coverage

| Argument | Purpose |
| --- | --- |
| `--coverage` | Enable all standard coverage types |
| `--coverage-line` | Enable line coverage |
| `--coverage-toggle` | Enable signal-toggle coverage |
| `--coverage-fsm` | Enable FSM coverage |
| `--coverage-expr` | Enable expression coverage |
| `--coverage-user` | Enable user-defined SystemVerilog coverage |
| `--coverage-expr-max <count>` | Limit expression-coverage permutations |
| `--coverage-max-width <width>` | Limit coverage array depth/width |
| `--coverage-per-instance` | Keep counters per design instance |
| `--coverage-underscore` | Include underscore-prefixed signals |

### Profiling

| Argument | Purpose |
| --- | --- |
| `--prof-c` | Compile generated C++ with profiling enabled |
| `--prof-cfuncs` | Give generated functions profiler-friendly names |
| `--prof-exec` | Generate runtime execution-profile data |
| `--prof-pgo` | Generate profile-guided optimization data |

## Simulation Runtime Plusargs

These arguments are passed to the **generated simulation executable**, not to
the `verilator` build command.

| Runtime argument | Purpose |
| --- | --- |
| `+verilator+coverage+file+<filename>` | Select the coverage-data output file |
| `+verilator+debug` | Enable runtime debug output |
| `+verilator+debugi+<value>` | Select the runtime debug level |
| `+verilator+error+limit+<value>` | Set the runtime error limit |
| `+verilator+help` | Display runtime argument help |
| `+verilator+log+file+<filename>` | Redirect runtime stdout/stderr to a file |
| `+verilator+noassert` | Disable runtime assertion checks |
| `+verilator+prof+exec+file+<filename>` | Select execution-profile output |
| `+verilator+prof+exec+start+<value>` | Select execution-profile start time |
| `+verilator+prof+exec+window+<value>` | Select execution-profile duration |
| `+verilator+prof+vlt+file+<filename>` | Select PGO profile input/output |
| `+verilator+quiet` | Reduce runtime informational output |
| `+verilator+rand+reset+<value>` | Select randomized reset initialization |
| `+verilator+seed+<value>` | Set the random seed |
| `+verilator+solver+file+<filename>` | Select random-constraint solver logging |
| `+verilator+V` | Display verbose runtime version/configuration |
| `+verilator+version` | Display runtime version |
| `+verilator+vpi+<library>[:<bootstrap>]` | Load a VPI shared library |
| `+verilator+wno+unsatconstr+<value>` | Suppress unsatisfied-constraint warnings |

## Shared Source and Language Options

### Language Selection and File Extensions

| Argument | Purpose |
| --- | --- |
| `--language <standard>` | Select the language standard |
| `--default-language <standard>` | Select the fallback language standard |
| `-sv` | Parse inputs as SystemVerilog |
| `+1364-1995ext+<ext>` | Treat an extension as Verilog 1995 |
| `+1364-2001ext+<ext>` | Treat an extension as Verilog 2001 |
| `+1364-2005ext+<ext>` | Treat an extension as Verilog 2005 |
| `+1800-2005ext+<ext>` | Treat an extension as SystemVerilog 2005 |
| `+1800-2009ext+<ext>` | Treat an extension as SystemVerilog 2009 |
| `+1800-2012ext+<ext>` | Treat an extension as SystemVerilog 2012 |
| `+1800-2017ext+<ext>` | Treat an extension as SystemVerilog 2017 |
| `+1800-2023ext+<ext>` | Treat an extension as SystemVerilog 2023 |
| `+systemverilogext+<ext>` | Alias for the current SystemVerilog extension mapping |
| `+verilog1995ext+<ext>` | Alias for Verilog 1995 extension mapping |
| `+verilog2001ext+<ext>` | Alias for Verilog 2001 extension mapping |
| `--no-std` | Do not load any Verilator standard files |
| `--no-std-package` | Do not load the standard package |

### Preprocessor

| Argument | Purpose |
| --- | --- |
| `-D<var>[=<value>]`, `+define+<var>=<value>` | Define a preprocessor symbol |
| `-U<var>` | Undefine a preprocessor symbol |
| `-I<dir>`, `+incdir+<dir>` | Add an include search directory |
| `-FI <file>` | Force inclusion of a source file |
| `-E` | Preprocess without generating a model |
| `-P` | Suppress line markers and blank lines with `-E` |
| `--preproc-comments` | Keep comments in preprocessor output |
| `--preproc-defines` | Include macro definitions in preprocessor output |
| `--preproc-resolve` | Include resolved modules in preprocessor output |
| `--preproc-token-limit <count>` | Limit tokens on one preprocessor line |
| `--dump-defines` | Print macro definitions with `-E` |
| `--relative-includes` | Resolve includes relative to the including file |
| `--pipe-filter <command>` | Filter source input through an external command |

### File Lists, Libraries, Top, and Parameters

| Argument | Purpose |
| --- | --- |
| `-f <file>` | Read arguments from a file |
| `-F <file>` | Read arguments with paths relative to that file |
| `-v <file>` | Add a Verilog library file |
| `-y <directory>` | Add a Verilog library directory |
| `+libext+<ext>+[ext]...` | Select extensions used for library lookup |
| `-libmap <file>` | Supply a library-mapping file |
| `-work <library>` | Select the configuration library for following files |
| `--top <name>`, `--top-module <name>` | Select the top module |
| `-G<name>=<value>`, `-pvalue+<name>=<value>` | Override a top parameter |

### Hierarchical Compilation

| Argument | Purpose |
| --- | --- |
| `--hierarchical` | Enable hierarchical Verilation |
| `--hierarchical-threads <count>` | Set hierarchy scheduling threads |
| `--hierarchical-block <block>` | Internal hierarchical block selection |
| `--hierarchical-child <block>` | Internal hierarchical child selection |
| `--hierarchical-params-file <file>` | Internal hierarchy parameter file |

## Optimization and Elaboration Tuning

Most projects should keep the defaults and use these only for measured problems.

| Argument | Purpose |
| --- | --- |
| `-O0`, `-O1`, `-O2`, `-O3` | Select increasing Verilator optimization levels |
| `-O<optimization-letter>` | Enable a specific internal optimization |
| `-fno-<optimization>` | Disable a specific internal optimization |
| `--expand-limit <value>` | Tune expression expansion |
| `--gate-stmts <value>` | Tune gate optimization |
| `--inline-cfuncs <value>` | Limit generated C++ function inlining |
| `--inline-cfuncs-product <value>` | Tune inlining by size multiplied by calls |
| `--inline-mult <value>` | Tune module inlining |
| `--localize-max-size <value>` | Limit variable localization size |
| `--reloop-limit <value>` | Tune generated-loop formation |
| `--unroll-count <loops>` | Tune loop unrolling count |
| `--unroll-limit <loops>` | Set the loop-iteration safety limit |
| `--unroll-stmts <statements>` | Limit loop-body size for unrolling |
| `--flatten` | Inline all hierarchy, tasks, and functions |
| `--bbox-sys` | Black-box unsupported system calls |
| `--bbox-unsup` | Black-box unsupported language constructs |
| `--constraint-array-limit <size>` | Limit array size in constraint reductions |
| `--func-recursion-depth <depth>` | Limit recursive constant-function evaluation |
| `--max-num-width <bits>` | Limit numeric literal width |
| `--replication-limit <count>` | Limit replication concatenation size |

## Debugging, JSON, Statistics, and Protection

### Verilator Debugging

| Argument | Purpose |
| --- | --- |
| `--debug` | Enable internal debug mode |
| `--debug-check` | Enable additional internal consistency checks |
| `--no-debug-leak` | Disable intentional memory retention in debug mode |
| `--debugi <level>` | Set the global debug level |
| `--debugi-<srcfile> <level>` | Set debugging for one Verilator source file |
| `--gdb` | Run Verilator interactively under GDB |
| `--gdbbt` | Run under GDB and obtain a backtrace |
| `--rr` | Record Verilator execution with rr |
| `--valgrind` | Run Verilator under Valgrind |
| `--dump-<srcfile>` | Enable all dumps for one Verilator source file |
| `--dumpi-<srcfile> <level>` | Set dump level for one source file |
| `--dump-ast-patterns` | Report AST pattern statistics |
| `--dump-dfg`, `--dumpi-dfg <level>` | Dump data-flow graphs |
| `--dump-dfg-patterns` | Report data-flow pattern statistics |
| `--dump-graph`, `--dumpi-graph <level>` | Dump internal graphs |
| `--dump-inputs` | Save preprocessed inputs |
| `--dump-tree`, `--dumpi-tree <level>` | Dump AST tree files |
| `--dump-tree-addrids` | Use short tree identifiers |
| `--dump-tree-dot` | Dump AST trees in DOT form |
| `--dump-tree-json`, `--dumpi-tree-json <level>` | Dump AST trees as JSON |

### JSON and Statistics

| Argument | Purpose |
| --- | --- |
| `--json-only` | Generate parser JSON instead of a model |
| `--json-only-output <file>` | Select parser-tree JSON output |
| `--json-only-meta-output <file>` | Select parser metadata output |
| `--no-json-edit-nums` | Omit edit numbers from tree JSON |
| `--no-json-ids` | Omit short JSON identifiers |
| `--stats` | Generate Verilator statistics |
| `--stats-vars` | Include variable statistics |
| `--quiet-stats` | Suppress printed statistics |

### Identifier Protection

| Argument | Purpose |
| --- | --- |
| `--protect-ids` | Obscure generated identifiers |
| `--protect-key <key>` | Supply the identifier-protection key |
| `--generate-key` | Generate a random protection key |

## General and Compatibility Options

| Argument | Purpose |
| --- | --- |
| `--help` | Display Verilator help |
| `--version` | Display the short version |
| `-V` | Display verbose version and configuration |
| `--get-supported <feature>` | Report whether a feature is supported |
| `--getenv <name>` | Display a Verilator environment/configuration value |
| `--quiet` | Reduce informational output |
| `--quiet-exit` | Do not repeat the command after failure |
| `--no-aslr` | Disable address-space layout randomization |
| `--no-unlimited-stack` | Keep the normal process stack limit |
| `--future0 <option>` | Ignore one future compatibility option |
| `--future1 <option> <value>` | Ignore a future option and its argument |
| `+librescan` | Accepted and ignored for compatibility |
| `+notimingchecks` | Accepted and ignored for compatibility |

## Choosing the Right Section

- Use **Lint and Diagnostics** for warning policy and static checks.
- Use **Compilation and Model Generation** for C++/SystemC output and build
  layout.
- Use **Simulation Build Options** for timing, threads, tracing, coverage, and
  assertions compiled into the model.
- Use **Simulation Runtime Plusargs** only when invoking the built executable.
- Use **Shared Source and Language Options** for includes, defines, libraries,
  standards, top modules, and parameters.
- Avoid optimization/debug/internal flags until a concrete problem requires
  them.
