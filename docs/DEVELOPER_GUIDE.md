# DFlow Developer Guide

**Project:** DFlow (Digital Design Flow Manager)
**Author:** Michael Hany

This document describes the current repository as it exists today, including the
package layout, the role of each directory and file, and the implemented flow
for commands, configuration, backends, and report generation.

---

# 1. Project Vision

DFlow is a Python command-line framework for digital IC design flows. The goal
is to expose one consistent interface for common EDA tasks instead of forcing
users to remember separate commands for Verilator, Yosys, OpenLane, VCS,
Questa, SpyGlass, Design Compiler, ICC2, and other tools.

The high-level idea is:

- the user types `dflow <command>`
- the command layer decides what the user wants to do
- the core layer resolves project structure and shared project behavior
- the backend layer chooses the concrete tool implementation
- the selected EDA tool performs the actual work

The current implementation already follows that shape for lint and compile,
with Verilator as the first implemented backend, and with project-aware tool
checks for simulation and synthesis.

---

# 2. Repository Layout

Current repository contents:

```text
dflow/
├── dflow/
│   ├── __init__.py
│   ├── cli.py
│   ├── config.py
│   ├── logger.py
│   ├── utils.py
│   ├── version.py
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── clean.py
│   │   ├── compile.py
│   │   ├── doctor.py
│   │   ├── init.py
│   │   ├── lint.py
│   │   ├── sim.py
│   │   ├── status.py
│   │   └── synth.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── filesystem.py
│   │   └── project.py
│   └── backends/
│       ├── __init__.py
│       ├── executor.py
│       ├── result.py
│       ├── compile/
│       │   ├── __init__.py
│       │   └── verilator.py
│       └── lint/
│           ├── __init__.py
│           └── verilator.py
├── docs/
│   └── DEVELOPER_GUIDE.md
├── tests/
├── pyproject.toml
├── README.md
└── requirements.txt
```

The `tests/` directory is currently empty. `README.md` is currently empty. The
project does not yet ship automated tests or user-facing documentation beyond
this guide.

---

# 3. Directory Overview

## `dflow/`

This is the Python package itself. It contains the CLI entry point, the user
commands, shared core utilities, and backend implementations.

### `dflow/__init__.py`

This file is currently empty. It exists so Python treats `dflow` as a package.

### `dflow/cli.py`

This is the Typer entry point for the application.

What it does:

- creates the Typer app
- imports every command function
- registers each command with the CLI
- provides the `dflow` executable entry point

Registered commands today:

- `init`
- `compile`
- `synth`
- `lint`
- `sim`
- `status`
- `doctor`
- `clean`

### `dflow/config.py`

This module loads and interprets each project’s `flow.yaml` file.

What it does:

- reads the project’s configuration file
- returns the whole config as a dictionary
- extracts a named flow section
- extracts the configured tool for a section
- extracts the configured options for a section

This file is the configuration access layer used by commands and backends.

### `dflow/logger.py`

This file is currently empty.

It is reserved for future logging behavior, but the current project does not use
it yet. Report saving is handled through the project core layer instead of a
logger abstraction.

### `dflow/utils.py`

This module provides generic environment helpers.

Current behavior:

- checks whether a tool is present on `PATH`
- returns a list of missing tools from a set of tool names

This module is intentionally small and generic.

### `dflow/version.py`

This file is currently empty.

It exists as a placeholder for future version metadata.

---

## `dflow/commands/`

Each file in this directory represents one user-facing command. The commands are
kept thin and are meant to delegate most work to core logic and backend logic.

### `dflow/commands/__init__.py`

This file is currently empty. It marks the command directory as a package.

### `dflow/commands/init.py`

Implements `dflow init <project_name>`.

Current behavior:

- calls `create_project(project_name)` in the core layer
- creates the new project directory structure
- generates `.dflow`
- generates `flow.yaml`
- prints a success message

This is the only command that creates a new project from scratch.

### `dflow/commands/compile.py`

Implements `dflow compile`.

Current behavior:

- finds the active DFlow project root by searching upward for `.dflow`
- loads `flow.yaml`
- delegates to the compile backend dispatcher
- receives a `FlowRunResult` from the backend
- saves the compile report in `reports/compile/`
- prints captured stdout and stderr
- prints a success message when the command succeeds
- exits with the tool’s return code

The command layer owns report persistence for compile.

### `dflow/commands/lint.py`

Implements `dflow lint`.

Current behavior:

- finds the active DFlow project root by searching upward for `.dflow`
- loads `flow.yaml`
- delegates to the lint backend dispatcher
- receives a `FlowRunResult` from the backend
- saves the lint report in `reports/lint/`
- prints captured stdout and stderr
- prints a success message when the command succeeds
- exits with the tool’s return code

The command layer owns report persistence for lint.

### `dflow/commands/sim.py`

Implements `dflow sim`.

Current behavior:

- finds the active DFlow project root
- loads `flow.yaml`
- reads the configured simulation tool from the `simulation` section
- checks whether that tool exists on `PATH`
- prints a success message if the tool is available

This command is still a tool availability check rather than a full simulation
execution flow.

### `dflow/commands/synth.py`

Implements `dflow synth`.

Current behavior:

- finds the active DFlow project root
- loads `flow.yaml`
- reads the configured synthesis tool from the `synthesis` section
- checks whether that tool exists on `PATH`
- prints a success message if the tool is available

This command is still a tool availability check rather than a full synthesis
execution flow.

### `dflow/commands/doctor.py`

Implements `dflow doctor`.

Current behavior:

- finds the active DFlow project root
- loads `flow.yaml`
- reads the configured tools for compile, lint, simulation, and synthesis
- checks whether each configured tool exists on `PATH`
- prints the status for each configured tool
- fails if any configured tool is missing

This command is used as an environment check for the configured toolchain.

### `dflow/commands/clean.py`

Implements `dflow clean`.

Current behavior:

- prints a placeholder message

It is not implemented yet.

### `dflow/commands/status.py`

Implements `dflow status`.

Current behavior:

- prints a placeholder message

It is not implemented yet.

---

## `dflow/core/`

This directory contains reusable project and filesystem behavior that is not tied
to one specific user command.

### `dflow/core/__init__.py`

This file is currently empty. It exists to mark the directory as a package.

### `dflow/core/filesystem.py`

This module contains low-level filesystem helpers.

Current behavior:

- creates directories recursively
- creates text files and any missing parent directories

These helpers are used by project creation and report writing.

### `dflow/core/project.py`

This is the main project-management module.

It owns:

- the standard DFlow project directory list
- the `.dflow` project marker
- default `flow.yaml` content for new projects
- project creation
- project root discovery
- RTL source discovery
- flow report persistence helpers

Current behavior in detail:

- `create_project(project_name)` creates a new project directory
- it creates the `.dflow` marker file
- it creates a default `flow.yaml`
- it creates the standard directory tree
- `find_project_root()` walks upward from the current directory until `.dflow`
  is found
- `find_rtl_sources()` returns `.v`, `.sv`, and `.svh` files under `rtl/`
- `save_flow_report()` writes a tool log under `reports/<stage>/`
- `save_lint_report()` saves lint reports under `reports/lint/`
- `save_compile_report()` saves compile reports under `reports/compile/`

This module is currently the central place for project structure and report
artifact handling.

---

## `dflow/backends/`

This directory contains tool-specific backend implementations. The backend layer
decides which tool implementation to run based on project configuration.

### `dflow/backends/__init__.py`

This file contains a package docstring only.

### `dflow/backends/result.py`

Defines the `FlowRunResult` data class.

Purpose:

- carry the tool name
- carry the exact command that was executed
- carry the return code
- carry captured stdout
- carry captured stderr

This object lets the backend return execution results to the command layer so
the command layer can print output and write reports.

### `dflow/backends/executor.py`

This module provides a shared subprocess runner for flow backends.

Current behavior:

- runs the command in the project root
- captures stdout and stderr
- returns a `FlowRunResult`

This is the shared execution helper used by compile and lint backends.

### `dflow/backends/compile/`

This package holds compile backend implementations.

#### `dflow/backends/compile/__init__.py`

This is the compile backend dispatcher.

Current behavior:

- loads the configuration if needed
- reads the configured compile tool from `flow.yaml`
- dispatches to the matching backend implementation
- currently supports Verilator only
- returns `None` for missing or unsupported configuration

#### `dflow/backends/compile/verilator.py`

This is the Verilator compile backend.

Current behavior:

- checks that Verilator is available on `PATH`
- finds RTL sources under `rtl/`
- reads compile options from `flow.yaml`
- builds a Verilator compile command
- executes the command through the shared backend executor
- returns a `FlowRunResult`

This backend does not save reports itself. That responsibility lives in the
command layer and the core project helper layer.

### `dflow/backends/lint/`

This package holds lint backend implementations.

#### `dflow/backends/lint/__init__.py`

This is the lint backend dispatcher.

Current behavior:

- loads the configuration if needed
- reads the configured lint tool from `flow.yaml`
- dispatches to the matching backend implementation
- currently supports Verilator only
- returns `None` for missing or unsupported configuration

#### `dflow/backends/lint/verilator.py`

This is the Verilator lint backend.

Current behavior:

- checks that Verilator is available on `PATH`
- finds RTL sources under `rtl/`
- reads lint options from `flow.yaml`
- builds a Verilator lint command
- executes the command through the shared backend executor
- returns a `FlowRunResult`

This backend does not save reports itself. That responsibility lives in the
command layer and the core project helper layer.

---

## `docs/`

This directory contains human-readable project documentation.

### `docs/DEVELOPER_GUIDE.md`

This file.

It documents the current repository layout, the implementation strategy, and
the way the command/core/backend layers fit together.

---

## `tests/`

This directory is currently empty.

It exists as the place for automated tests when they are added later.

---

## Root-level files

### `pyproject.toml`

This file defines the build system and project metadata.

Current behavior:

- uses setuptools as the build backend
- defines the project name as `dflow`
- defines version `0.1.0`
- lists dependencies
- exposes the `dflow` console script entry point

The current dependency list includes:

- `typer`
- `rich`
- `pyyaml`

### `requirements.txt`

This file lists the pinned environment dependencies currently present in the
workspace.

It includes the runtime packages and the dependency chain used by the current
environment.

### `README.md`

This file is currently empty.

It is intended for user-facing project documentation.

---

# 4. Current Architecture

The current layering is:

```text
User
 │
 ▼
dflow command
 │
 ▼
commands/
 │
 ▼
core/
 │
 ▼
backends/
 │
 ▼
EDA Tool
```

What each layer is responsible for:

- **commands**: decide what action the user requested
- **core**: handle project structure, config loading, source discovery, and report persistence
- **backends**: decide which tool implementation to use and run it
- **tool**: do the actual lint or compile work

This is the separation of concerns that the current code follows.

---

# 5. How Project Initialization Works

`dflow init <project_name>` creates a new DFlow project.

The creation flow is:

```text
init command
→ create_project()
→ create root project directory
→ write .dflow
→ write flow.yaml
→ create standard project directories
```

The generated project tree currently contains:

```text
<project>/
├── rtl/
├── tb/
├── scripts/
├── constraints/
├── docs/
├── reports/
├── formal/
├── openlane/
└── sim/
    ├── logs/
    └── waves/
```

The generated configuration file sets these default tool mappings:

- `compile.tool = verilator`
- `compile.options = [--cc]`
- `lint.tool = verilator`
- `lint.options = [--lint-only, -Wall]`
- `simulation.tool = verilator`
- `synthesis.tool = yosys`

The `.dflow` file acts as the project root marker.

---

# 6. Configuration Model

Each project contains a `flow.yaml` file.

The project config is read by `dflow/config.py` and used by commands and
backends.

Current configuration behavior:

- the file is loaded from the project root
- each section is normalized into a dictionary
- each section can define a `tool`
- some sections can define an `options` list

Section usage today:

- `compile` selects the compile backend tool and options
- `lint` selects the lint backend tool and options
- `simulation` selects the simulation tool check
- `synthesis` selects the synthesis tool check

Current implementation expects tool names to be strings and options to be lists
of strings.

---

# 7. Command Behavior Today

## `init`

Creates a new project and the default directory tree.

## `lint`

- locates the project root
- loads config
- dispatches to the lint backend
- saves the lint report to `reports/lint/`
- prints captured tool output

## `compile`

- locates the project root
- loads config
- dispatches to the compile backend
- saves the compile report to `reports/compile/`
- prints captured tool output

## `sim`

- locates the project root
- loads config
- checks whether the configured simulation tool is available

## `synth`

- locates the project root
- loads config
- checks whether the configured synthesis tool is available

## `doctor`

- locates the project root
- loads config
- checks the configured compile, lint, simulation, and synthesis tools
- prints their availability

## `clean`

Placeholder only.

## `status`

Placeholder only.

---

# 8. Backend Behavior Today

## Backend dispatchers

`dflow/backends/compile/__init__.py` and `dflow/backends/lint/__init__.py`
resolve which backend implementation to use from `flow.yaml`.

They currently support Verilator only.

If a different tool is configured, they print an unsupported-tool message and
return `None`.

## Verilator compile backend

The Verilator compile backend:

- checks Verilator availability
- checks that RTL sources exist
- builds the Verilator command
- runs it through the shared executor
- returns the captured result

## Verilator lint backend

The Verilator lint backend:

- checks Verilator availability
- checks that RTL sources exist
- builds the Verilator lint command
- runs it through the shared executor
- returns the captured result

## Shared executor

`dflow/backends/executor.py` runs the actual subprocess call and converts it into
the common `FlowRunResult` format.

This avoids duplicating subprocess handling across different tool backends.

## Report saving

Report persistence is handled by the command layer using helpers from
`dflow/core/project.py`:

- compile logs go to `reports/compile/<tool>.log`
- lint logs go to `reports/lint/<tool>.log`

That keeps artifact writing in the project/core layer instead of embedding it in
the tool execution logic.

---

# 9. Current Generated Artifacts

When compile or lint runs successfully, the project receives report files under:

- `reports/compile/`
- `reports/lint/`

The files contain:

- the command that was executed
- the return code
- stdout
- stderr

This makes the tool output reproducible and easy to inspect after a run.

---

# 10. Current Limitations

These parts are still incomplete or placeholder-only:

- `dflow/commands/status.py`
- `dflow/commands/clean.py`
- `dflow/logger.py`
- `dflow/version.py`
- `dflow/__init__.py`
- `dflow/commands/__init__.py`
- `dflow/core/__init__.py`
- `dflow/backends/__init__.py`
- `dflow/backends/compile/__init__.py` and `dflow/backends/lint/__init__.py` only support Verilator today
- `sim` and `synth` are still tool-availability checks rather than full execution flows
- `README.md` is empty
- `tests/` is empty

The architecture is in place, but several commands still need their full tool
execution behavior implemented.

---

# 11. Roadmap

## Already implemented

- installable Python package
- Typer CLI entry point
- modular command layout
- core filesystem helpers
- core project discovery and config loading
- `.dflow` project marker
- default `flow.yaml` generation
- Verilator lint backend
- Verilator compile backend
- command-owned lint and compile report saving
- `doctor` environment checking

## Next likely steps

- implement real simulation execution
- implement real synthesis execution
- implement `status`
- implement `clean`
- add test coverage
- add a real logger if needed
- expand backend support beyond Verilator
- add stronger config validation

---

# 12. Design Principles

The codebase is currently following these principles:

- thin commands
- reusable core logic
- tool-specific backend packages
- configuration-driven behavior
- clear separation of responsibilities
- report persistence in the project/core layer
- shared subprocess handling for backends

These rules are what keep the structure pluggable as more EDA tools are added.