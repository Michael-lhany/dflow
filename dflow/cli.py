import typer

from dflow.commands.asic import asic
from dflow.commands.init import init
from dflow.commands.compile import compile
from dflow.commands.synth import synth
from dflow.commands.lint import lint
from dflow.commands.sim import sim
from dflow.commands.status import status
from dflow.commands.doctor import doctor
from dflow.commands.clean import clean
from dflow.commands.gui import gui

app = typer.Typer(
    help="Digital Flow Manager (DFLOW)"
)

app.command()(init)
app.command()(compile)
app.command()(synth)
app.command()(lint)
app.command()(sim)
app.command()(status)
app.command()(doctor)
app.command()(clean)
app.command()(gui)
app.command()(asic)

if __name__ == "__main__":
    app()
