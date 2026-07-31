import typer
import sys

from dflow.backends.compile import run_compile
from dflow.config import load_flow_config
from dflow.core.project import find_project_root, save_compile_report

app = typer.Typer()


@app.command()
def compile():
    """Compile RTL."""

    project_root = find_project_root()
    flow_config = load_flow_config(project_root)
    result = run_compile(project_root, flow_config)

    if result is None:
        raise typer.Exit(code=1)

    save_compile_report(
        project_root,
        result.tool_name,
        result.command,
        result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )

    if result.stdout:
        print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")

    if result.stderr:
        print(result.stderr, end="" if result.stderr.endswith("\n") else "\n", file=sys.stderr)

    if result.returncode == 0:
        print(f"RTL compile check passed with {result.tool_name}.")


    raise typer.Exit(code=result.returncode)
