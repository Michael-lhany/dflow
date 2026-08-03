import typer


def gui() -> None:
    """Open the graphical DFlow interface."""
    try:
        from dflow.gui import launch_gui
    except ImportError:
        print(
            "The DFlow GUI requires Tkinter. Install your system's Python "
            "Tk package and try again."
        )
        raise typer.Exit(code=1)

    try:
        launch_gui()
    except RuntimeError as error:
        print(error)
        raise typer.Exit(code=1)
