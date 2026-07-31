import typer

app = typer.Typer()


@app.command()
def status():
    """Show project status."""
    print("Status command")
