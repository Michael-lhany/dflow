# Repository Guidelines

## Project Structure & Module Organization

`dflow/` contains the Python CLI package. Add user-facing Typer commands in `dflow/commands/`, shared project and filesystem behavior in `dflow/core/`, and tool-specific integrations in `dflow/backends/<flow>/` (for example, `backends/lint/verilator.py`). `dflow/cli.py` registers commands, while `dflow/config.py` reads project `flow.yaml` files. `Dflow_project_examples/counter/` is the working HDL example, with RTL in `rtl/`, testbench sources in `tb/`, and generated simulation output under `sim/`. Developer documentation lives in `docs/`; Python tests belong in `tests/`.

## Build, Test, and Development Commands

- `python -m venv .venv && source .venv/bin/activate` creates an isolated environment.
- `python -m pip install -e .` installs DFlow and exposes the `dflow` command for local development.
- `dflow --help` verifies the CLI entry point and lists registered commands.
- `dflow doctor` checks tools configured by the nearest DFlow project's `flow.yaml`.
- `dflow lint`, `dflow compile`, and `dflow sim` exercise flows from inside an example project; Verilator must be installed when configured.
- `pytest` runs the test suite once test dependencies are installed. The suite is currently empty, so add tests with behavioral changes.

## Coding Style & Naming Conventions

Follow PEP 8 with four-space indentation, type hints for public interfaces, and short docstrings for non-obvious behavior. Use `snake_case` for modules, functions, and variables; `PascalCase` for classes; and uppercase names for constants. Keep command modules thin: resolve configuration in the command layer, place reusable behavior in `core`, and return `FlowRunResult` from executing backends. No formatter or linter is configured, so keep imports grouped as standard library, third-party, then local modules.

## Testing Guidelines

Use pytest-style tests under `tests/`, named `test_<feature>.py`, with functions named `test_<behavior>`. Prefer temporary directories for project discovery, report generation, and `flow.yaml` cases. Mock external EDA executables; reserve manual example runs for integration checks. Cover successful execution, missing configuration/tools, and nonzero backend return codes.

## Commit & Pull Request Guidelines

Recent history uses concise Conventional Commit subjects such as `feat: Add initial counter example`. Continue with imperative prefixes like `feat:`, `fix:`, `test:`, or `docs:` and keep each commit focused. Pull requests should explain the behavior change, list verification commands, link relevant issues, and include terminal output or generated-report examples when CLI behavior changes. Do not commit virtual environments, caches, generated waveforms, or local build artifacts.
