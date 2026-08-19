# DFlow Dependencies

## Libraries

| Library | Needed for | Get it from |
| --- | --- | --- |
| Python 3.10+ | DFlow runtime | [python.org](https://www.python.org/downloads/) |
| Setuptools 61+ | Package installation | [PyPI](https://pypi.org/project/setuptools/) |
| Typer | CLI | [PyPI](https://pypi.org/project/typer/) |
| PyYAML | `flow.yaml` parsing | [PyPI](https://pypi.org/project/PyYAML/) |
| Click | CLI and standalone SBY | [PyPI](https://pypi.org/project/click/) |
| Tkinter | GUI | Linux distribution package `python3-tk` |
| pytest | Development tests only | [PyPI](https://pypi.org/project/pytest/) |
| libc++ 18 | Simulation build | [LLVM packages](https://apt.llvm.org/) |
| libc++abi 18 | Simulation build | [LLVM packages](https://apt.llvm.org/) |

Install the Python libraries:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

## External Tools

| Tool | Needed for | Get it from |
| --- | --- | --- |
| Git | Downloading and maintaining DFlow | [git-scm.com](https://git-scm.com/downloads) |
| Verilator | Compile, lint, and simulation | [Verilator installation guide](https://verilator.org/guide/latest/install.html) |
| GNU Make | Simulation build | [GNU Make](https://www.gnu.org/software/make/) |
| Clang/LLVM 18 | Simulation C++ build | [LLVM packages](https://apt.llvm.org/) |
| GTKWave | Waveform viewing | [GTKWave](https://gtkwave.sourceforge.net/) |
| Yosys and ABC | Synthesis and formal verification | [Yosys GitHub](https://github.com/YosysHQ/yosys) |
| SymbiYosys (`sby`) | Formal verification | [SBY GitHub](https://github.com/YosysHQ/sby) |
| `yosys-smtbmc` | Formal SMT engine | Installed with Yosys |
| Z3 | Formal solver | [Z3 GitHub](https://github.com/Z3Prover/z3) |
| OpenLane 2 | RTL-to-GDS ASIC flow | [OpenLane installation guide](https://openlane2.readthedocs.io/en/latest/getting_started/installation.html) |
| OpenROAD, Magic, KLayout, and Netgen | OpenLane internal stages | Included with the OpenLane environment |
| SKY130/Open_PDKs | ASIC process design kit | Installed through OpenLane's PDK setup |
| Nix | Optional OpenLane Nix launcher | [Nix download](https://nixos.org/download/) |
| ccache | Optional faster simulation rebuilds | [ccache](https://ccache.dev/download.html) |
