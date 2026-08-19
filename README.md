# DFlow

DFlow is a Python command-line and graphical front end for an open-source
digital ASIC workflow. It provides one project configuration and a consistent
interface for RTL compilation, linting, simulation, waveform viewing,
synthesis, formal verification, and RTL-to-GDS implementation.

## Features

- Verilator compilation, linting, and simulation
- GTKWave waveform viewing, including opening an existing VCD without rerunning
  simulation
- Yosys synthesis
- SymbiYosys formal verification with task selection and counterexample traces
- OpenLane RTL-to-GDS flow integration
- Timestamped simulation, formal, and ASIC reports that preserve previous runs
- Selective cleanup and read-only project/tool status commands
- Tkinter GUI exposing the same commands and options as the CLI

## Requirements

DFlow requires Python 3.10 or newer. Install the external EDA tools needed by
the flows you intend to run:

- Verilator and Make for compile, lint, and simulation
- GTKWave for waveform viewing
- Yosys for synthesis
- SymbiYosys, Yosys, and a supported solver such as Z3 for formal verification
- OpenLane and its PDK dependencies for physical ASIC implementation

Use `dflow doctor` inside a project to check the configured tools.

## Installation

Clone the repository and create the development environment:

```bash
git clone https://github.com/Michael-lhany/dflow.git
cd dflow
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

For later sessions, `source ./activate.sh` activates the repository's virtual
environment.

## Quick start

Create and enter a project:

```bash
dflow init my_design
cd my_design
dflow status
dflow doctor
```

Add synthesizable sources under `rtl/`, testbench sources under `tb/`, and edit
`flow.yaml` for the design and installed tools. Typical commands are:

```bash
dflow compile
dflow lint
dflow sim
dflow sim --wave
dflow sim --wave-only
dflow synth
dflow formal
dflow asic
dflow gui
```

Pass temporary backend arguments after `--`, for example:

```bash
dflow lint -- -Wall --Wno-fatal
dflow formal --task prove -- --live jsonl
dflow asic -- --to Verilator.Lint --condensed
```

Generated reports and tool work directories are ignored by Git. Use
`dflow clean --dry-run` to preview cleanup or select categories with `--only`
and `--exclude`.

## Documentation

- [GUI guide](docs/GUI_GUIDE.md)
- [OpenLane guide](docs/OPENLANE_GUIDE.md)
- [SymbiYosys guide](docs/SYMBIYOSYS_GUIDE.md)
- [Verilator arguments](docs/VERILATOR_ARGUMENTS.md)
- [Yosys arguments](docs/YOSYS_ARGUMENTS.md)
- [Developer guide](docs/DEVELOPER_GUIDE.md)

## Development

Run the automated test suite from the repository root:

```bash
pytest
```

Keep generated reports, waveforms, proof runs, OpenLane runs, virtual
environments, and local design examples out of commits. See `AGENTS.md` for the
repository's contributor conventions.

## License

No open-source license has been selected yet. Public visibility allows others
to view and fork the repository, but it does not grant permission to reuse or
redistribute the code. Add a suitable `LICENSE` file before external reuse if
your company or mentor requires one.
