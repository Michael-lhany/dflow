import shlex
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
from tkinter.scrolledtext import ScrolledText


FLOW_COMMANDS = (
    ("Compile", "compile"),
    ("Lint", "lint"),
    ("Simulate", "sim"),
    ("Synthesize", "synth"),
)
PROJECT_COMMANDS = (
    ("Doctor", "doctor"),
    ("Status", "status"),
)
OPTION_COMMANDS = {"compile", "lint", "sim", "synth"}


def build_cli_command(command: str, tool_options: str = "") -> list[str]:
    """Build the DFlow subprocess command used by the GUI."""
    cli_command = [sys.executable, "-m", "dflow.cli", command]
    if command in OPTION_COMMANDS and tool_options.strip():
        cli_command.extend(["--", *shlex.split(tool_options)])
    return cli_command


class DFlowGui:
    """Small Tkinter front end for DFlow commands."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.project_path = tk.StringVar(value=str(Path.cwd()))
        self.tool_options = tk.StringVar()
        self.status_text = tk.StringVar(value="Ready")
        self.command_buttons: list[ttk.Button] = []
        self.running = False

        self._configure_window()
        self._build_layout()

    def _configure_window(self) -> None:
        self.root.title("DFlow")
        self.root.geometry("900x620")
        self.root.minsize(720, 500)

        style = ttk.Style(self.root)
        style.configure("Title.TLabel", font=("TkDefaultFont", 20, "bold"))
        style.configure("Subtitle.TLabel", foreground="#555555")
        style.configure("Command.TButton", padding=(14, 9))

    def _build_layout(self) -> None:
        container = ttk.Frame(self.root, padding=20)
        container.grid(row=0, column=0, sticky="nsew")
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(5, weight=1)

        ttk.Label(container, text="DFlow", style="Title.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            container,
            text="Run your digital design flow from one place.",
            style="Subtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(0, 18))

        project_frame = ttk.LabelFrame(
            container, text="Project", padding=12
        )
        project_frame.grid(row=2, column=0, sticky="ew")
        project_frame.columnconfigure(0, weight=1)
        ttk.Entry(project_frame, textvariable=self.project_path).grid(
            row=0, column=0, sticky="ew", padx=(0, 8)
        )
        ttk.Button(project_frame, text="Browse", command=self._browse).grid(
            row=0, column=1
        )
        self._add_button(
            project_frame, "New Project", self._initialize_project, row=0, column=2
        )

        options_frame = ttk.Frame(container)
        options_frame.grid(row=3, column=0, sticky="ew", pady=(14, 10))
        options_frame.columnconfigure(1, weight=1)
        ttk.Label(options_frame, text="Tool arguments").grid(
            row=0, column=0, sticky="w", padx=(0, 10)
        )
        ttk.Entry(options_frame, textvariable=self.tool_options).grid(
            row=0, column=1, sticky="ew"
        )
        ttk.Label(
            options_frame,
            text="Applied to compile, lint, sim, and synth",
            style="Subtitle.TLabel",
        ).grid(row=1, column=1, sticky="w", pady=(3, 0))

        commands_frame = ttk.Frame(container)
        commands_frame.grid(row=4, column=0, sticky="ew", pady=(0, 14))
        for column in range(4):
            commands_frame.columnconfigure(column, weight=1)

        for column, (label, command) in enumerate(FLOW_COMMANDS):
            self._add_button(
                commands_frame,
                label,
                lambda selected=command: self._run_command(selected),
                row=0,
                column=column,
            )

        for column, (label, command) in enumerate(PROJECT_COMMANDS):
            self._add_button(
                commands_frame,
                label,
                lambda selected=command: self._run_command(selected),
                row=1,
                column=column,
            )
        self._add_button(
            commands_frame, "Clean", self._clean_project, row=1, column=2
        )
        self._add_button(
            commands_frame,
            "Preview Clean",
            lambda: self._run_command("clean", ["--dry-run"]),
            row=1,
            column=3,
        )

        output_frame = ttk.LabelFrame(container, text="Output", padding=10)
        output_frame.grid(row=5, column=0, sticky="nsew")
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)
        self.output = ScrolledText(
            output_frame,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=("TkFixedFont", 10),
        )
        self.output.grid(row=0, column=0, columnspan=2, sticky="nsew")
        ttk.Label(output_frame, textvariable=self.status_text).grid(
            row=1, column=0, sticky="w", pady=(8, 0)
        )
        ttk.Button(
            output_frame, text="Clear Output", command=self._clear_output
        ).grid(row=1, column=1, sticky="e", pady=(8, 0))

    def _add_button(
        self,
        parent: ttk.Frame,
        label: str,
        callback,
        row: int,
        column: int,
    ) -> None:
        button = ttk.Button(
            parent, text=label, command=callback, style="Command.TButton"
        )
        button.grid(row=row, column=column, sticky="ew", padx=4, pady=4)
        self.command_buttons.append(button)

    def _browse(self) -> None:
        selected = filedialog.askdirectory(
            title="Select a DFlow project",
            initialdir=self.project_path.get(),
        )
        if selected:
            self.project_path.set(selected)

    def _initialize_project(self) -> None:
        project_name = simpledialog.askstring(
            "New DFlow Project", "Project name:", parent=self.root
        )
        if project_name and project_name.strip():
            self._run_command("init", [project_name.strip()])

    def _clean_project(self) -> None:
        if messagebox.askyesno(
            "Clean Project",
            "Remove generated logs, reports, and build artifacts?",
            parent=self.root,
        ):
            self._run_command("clean")

    def _run_command(
        self, command: str, extra_arguments: list[str] | None = None
    ) -> None:
        if self.running:
            return

        working_directory = Path(self.project_path.get()).expanduser()
        if not working_directory.is_dir():
            messagebox.showerror(
                "Invalid Project Directory",
                "Select an existing directory before running a command.",
                parent=self.root,
            )
            return

        try:
            cli_command = build_cli_command(command, self.tool_options.get())
        except ValueError as error:
            messagebox.showerror(
                "Invalid Tool Arguments", str(error), parent=self.root
            )
            return

        if extra_arguments:
            cli_command.extend(extra_arguments)

        self.running = True
        self._set_buttons_enabled(False)
        self.status_text.set(f"Running dflow {command}...")
        self._append_output(
            f"\n$ cd {shlex.quote(str(working_directory))}\n"
            f"$ {shlex.join(cli_command)}\n\n"
        )

        thread = threading.Thread(
            target=self._execute,
            args=(cli_command, working_directory, command),
            daemon=True,
        )
        thread.start()

    def _execute(
        self, cli_command: list[str], working_directory: Path, command: str
    ) -> None:
        try:
            process = subprocess.Popen(
                cli_command,
                cwd=working_directory,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            if process.stdout:
                for line in process.stdout:
                    self.root.after(0, self._append_output, line)
            return_code = process.wait()
            self.root.after(0, self._finish_command, command, return_code)
        except OSError as error:
            self.root.after(0, self._append_output, f"{error}\n")
            self.root.after(0, self._finish_command, command, 1)

    def _finish_command(self, command: str, return_code: int) -> None:
        self.running = False
        self._set_buttons_enabled(True)
        if return_code == 0:
            self.status_text.set(f"dflow {command} completed")
        else:
            self.status_text.set(
                f"dflow {command} failed with exit code {return_code}"
            )
        self._append_output(f"\n[exit code {return_code}]\n")

    def _set_buttons_enabled(self, enabled: bool) -> None:
        state = tk.NORMAL if enabled else tk.DISABLED
        for button in self.command_buttons:
            button.configure(state=state)

    def _append_output(self, text: str) -> None:
        self.output.configure(state=tk.NORMAL)
        self.output.insert(tk.END, text)
        self.output.see(tk.END)
        self.output.configure(state=tk.DISABLED)

    def _clear_output(self) -> None:
        self.output.configure(state=tk.NORMAL)
        self.output.delete("1.0", tk.END)
        self.output.configure(state=tk.DISABLED)


def launch_gui() -> None:
    """Create and run the DFlow GUI."""
    try:
        root = tk.Tk()
    except tk.TclError as error:
        raise RuntimeError(
            "Unable to open the DFlow GUI. A graphical display is required."
        ) from error

    DFlowGui(root)
    root.mainloop()
