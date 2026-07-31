import typer

app = typer.Typer()


@app.command()
def clean():
    """Clean generated files."""
    print("Clean command")
