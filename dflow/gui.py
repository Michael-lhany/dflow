import shlex
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from dflow.core.project import CLEAN_CATEGORIES


OPTION_COMMANDS = {"compile", "lint", "sim", "synth", "asic"}
CLEAN_CATEGORY_LABELS = {
    "build": "Synthesis build",
    "compile": "Compile output",
    "simulation": "Simulation build",
    "waveforms": "Waveforms",
    "reports": "Reports",
    "asic": "OpenLane runs",
}


def build_cli_command(
    command: str,
    tool_options: str = "",
    command_arguments: list[str] | None = None,
) -> list[str]:
    """Build the DFlow subprocess command used by the GUI."""
    cli_command = [sys.executable, "-m", "dflow.cli", command]
    if command_arguments:
        cli_command.extend(command_arguments)
    if command in OPTION_COMMANDS and tool_options.strip():
        cli_command.extend(["--", *shlex.split(tool_options)])
    return cli_command


def build_asic_tool_options(
    *,
    condensed: bool,
    jobs: str = "",
    start_step: str = "",
    end_step: str = "",
    extra_options: str = "",
) -> str:
    """Build validated OpenLane options from the ASIC page controls."""
    options: list[str] = []
    if condensed:
        options.append("--condensed")

    normalized_jobs = jobs.strip()
    if normalized_jobs:
        try:
            job_count = int(normalized_jobs)
        except ValueError as error:
            raise ValueError("OpenLane jobs must be a positive integer.") from error
        if job_count < 1:
            raise ValueError("OpenLane jobs must be a positive integer.")
        options.extend(["-j", str(job_count)])

    if start_step.strip():
        options.extend(["--from", start_step.strip()])
    if end_step.strip():
        options.extend(["--to", end_step.strip()])
    if extra_options.strip():
        options.extend(shlex.split(extra_options))
    return shlex.join(options)


def build_clean_arguments(
    selected_categories: list[str],
    *,
    dry_run: bool = False,
) -> list[str]:
    """Build clean command arguments from selected GUI categories."""
    selected = set(selected_categories)
    unknown = selected - set(CLEAN_CATEGORIES)
    if unknown:
        raise ValueError(
            "Unknown cleanup categories: " + ", ".join(sorted(unknown))
        )
    if not selected:
        raise ValueError("Select at least one cleanup category.")

    arguments = ["--dry-run"] if dry_run else []
    if selected != set(CLEAN_CATEGORIES):
        for category in CLEAN_CATEGORIES:
            if category in selected:
                arguments.extend(["--only", category])
    return arguments


class DFlowGui:
    """Tabbed Tkinter front end for DFlow commands."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.project_path = tk.StringVar(master=root, value=str(Path.cwd()))
        self.status_text = tk.StringVar(master=root, value="Ready")
        self.new_project_name = tk.StringVar(master=root)
        self.command_options = {
            command: tk.StringVar(master=root)
            for command in ("compile", "lint", "sim", "synth")
        }
        self.sim_open_wave = tk.BooleanVar(master=root, value=False)
        self.asic_condensed = tk.BooleanVar(master=root, value=True)
        self.asic_jobs = tk.StringVar(master=root)
        self.asic_start_step = tk.StringVar(master=root)
        self.asic_end_step = tk.StringVar(master=root)
        self.asic_extra_options = tk.StringVar(master=root)
        self.clean_categories = {
            category: tk.BooleanVar(master=root, value=True)
            for category in CLEAN_CATEGORIES
        }
        self.command_buttons: list[ttk.Button] = []
        self.running = False

        self._configure_window()
        self._build_layout()

    def _configure_window(self) -> None:
        self.root.title("DFlow")
        self.root.geometry("1100x760")
        self.root.minsize(860, 640)

        style = ttk.Style(self.root)
        style.configure("Title.TLabel", font=("TkDefaultFont", 20, "bold"))
        style.configure("PageTitle.TLabel", font=("TkDefaultFont", 14, "bold"))
        style.configure("Subtitle.TLabel", foreground="#555555")
        style.configure("Hint.TLabel", foreground="#666666")
        style.configure("Command.TButton", padding=(14, 9))
        style.configure("TNotebook.Tab", padding=(10, 6))

    def _build_layout(self) -> None:
        container = ttk.Frame(self.root, padding=18)
        container.grid(row=0, column=0, sticky="nsew")
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(4, weight=1)

        ttk.Label(container, text="DFlow", style="Title.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            container,
            text="Digital design flows with focused controls for every stage.",
            style="Subtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(0, 12))

        self._build_project_selector(container)

        notebook = ttk.Notebook(container)
        notebook.grid(row=3, column=0, sticky="ew", pady=(12, 12))
        self._build_project_page(notebook)
        self._build_compile_page(notebook)
        self._build_lint_page(notebook)
        self._build_simulation_page(notebook)
        self._build_synthesis_page(notebook)
        self._build_asic_page(notebook)
        self._build_status_page(notebook)
        self._build_doctor_page(notebook)
        self._build_clean_page(notebook)

        self._build_output_panel(container)

    def _build_project_selector(self, parent: ttk.Frame) -> None:
        project_frame = ttk.LabelFrame(parent, text="Active project", padding=10)
        project_frame.grid(row=2, column=0, sticky="ew")
        project_frame.columnconfigure(0, weight=1)
        ttk.Entry(project_frame, textvariable=self.project_path).grid(
            row=0, column=0, sticky="ew", padx=(0, 8)
        )
        ttk.Button(project_frame, text="Browse", command=self._browse).grid(
            row=0, column=1
        )

    def _new_page(
        self,
        notebook: ttk.Notebook,
        tab_label: str,
        title: str,
        description: str,
    ) -> ttk.Frame:
        page = ttk.Frame(notebook, padding=16)
        page.columnconfigure(1, weight=1)
        notebook.add(page, text=tab_label)
        ttk.Label(page, text=title, style="PageTitle.TLabel").grid(
            row=0, column=0, columnspan=3, sticky="w"
        )
        ttk.Label(
            page,
            text=description,
            style="Subtitle.TLabel",
            wraplength=920,
            justify=tk.LEFT,
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(2, 12))
        return page

    def _add_options_entry(
        self,
        page: ttk.Frame,
        row: int,
        label: str,
        variable: tk.StringVar,
        hint: str,
    ) -> None:
        ttk.Label(page, text=label).grid(
            row=row, column=0, sticky="w", padx=(0, 10)
        )
        ttk.Entry(page, textvariable=variable).grid(
            row=row, column=1, columnspan=2, sticky="ew"
        )
        ttk.Label(page, text=hint, style="Hint.TLabel").grid(
            row=row + 1,
            column=1,
            columnspan=2,
            sticky="w",
            pady=(3, 8),
        )

    def _build_project_page(self, notebook: ttk.Notebook) -> None:
        page = self._new_page(
            notebook,
            "Project",
            "Initialize a DFlow project",
            "Create a new project below the directory selected above.",
        )
        ttk.Label(page, text="Project name").grid(
            row=2, column=0, sticky="w", padx=(0, 10)
        )
        entry = ttk.Entry(page, textvariable=self.new_project_name)
        entry.grid(row=2, column=1, sticky="ew")
        self._add_button(
            page,
            "Create Project",
            self._initialize_project,
            row=2,
            column=2,
        )
        ttk.Label(
            page,
            text="Creates .dflow, flow.yaml, RTL/testbench folders, reports, and flow output directories.",
            style="Hint.TLabel",
            wraplength=900,
        ).grid(row=3, column=1, columnspan=2, sticky="w", pady=(4, 0))

    def _build_compile_page(self, notebook: ttk.Notebook) -> None:
        page = self._new_page(
            notebook,
            "Compile",
            "Compile RTL",
            "Run the configured compiler as a structural RTL build check.",
        )
        self._add_options_entry(
            page,
            2,
            "Verilator arguments",
            self.command_options["compile"],
            "Examples: --top-module counter or -Wall. These are appended after --.",
        )
        self._add_button(
            page,
            "Run Compile",
            lambda: self._run_command("compile"),
            row=4,
            column=2,
        )

    def _build_lint_page(self, notebook: ttk.Notebook) -> None:
        page = self._new_page(
            notebook,
            "Lint",
            "Lint RTL",
            "Check RTL style, widths, unused signals, and other Verilator diagnostics.",
        )
        self._add_options_entry(
            page,
            2,
            "Verilator arguments",
            self.command_options["lint"],
            "Examples: -Wall --Wno-fatal or --Wno-TIMESCALEMOD.",
        )
        self._add_button(
            page,
            "Run Lint",
            lambda: self._run_command("lint"),
            row=4,
            column=2,
        )

    def _build_simulation_page(self, notebook: ttk.Notebook) -> None:
        page = self._new_page(
            notebook,
            "Simulation",
            "Build and run simulation",
            "Run the configured testbench, optionally opening a newly generated VCD in GTKWave.",
        )
        self._add_options_entry(
            page,
            2,
            "Verilator arguments",
            self.command_options["sim"],
            "Examples: --threads 4. Runtime-independent build options are appended after --.",
        )
        ttk.Checkbutton(
            page,
            text="Open a newly generated waveform after a successful simulation",
            variable=self.sim_open_wave,
        ).grid(row=4, column=1, columnspan=2, sticky="w", pady=(2, 8))
        self._add_button(
            page,
            "Run Simulation",
            self._run_simulation,
            row=5,
            column=1,
        )
        self._add_button(
            page,
            "Open Existing Wave",
            lambda: self._run_command(
                "sim",
                ["--wave-only"],
                tool_options="",
            ),
            row=5,
            column=2,
        )

    def _build_synthesis_page(self, notebook: ttk.Notebook) -> None:
        page = self._new_page(
            notebook,
            "Synthesis",
            "Synthesize RTL",
            "Generate mapped or generic netlists with the synthesis tool configured in flow.yaml.",
        )
        self._add_options_entry(
            page,
            2,
            "Yosys arguments",
            self.command_options["synth"],
            "Examples: -Q or -q. Top module and Liberty mapping are configured in flow.yaml.",
        )
        self._add_button(
            page,
            "Run Synthesis",
            lambda: self._run_command("synth"),
            row=4,
            column=2,
        )

    def _build_asic_page(self, notebook: ttk.Notebook) -> None:
        page = self._new_page(
            notebook,
            "ASIC",
            "OpenLane RTL-to-GDS flow",
            "Run the full Classic flow, isolate a range of steps, or inspect the latest completed layout.",
        )
        ttk.Checkbutton(
            page,
            text="Condensed OpenLane output",
            variable=self.asic_condensed,
        ).grid(row=2, column=0, columnspan=2, sticky="w")
        ttk.Label(page, text="Parallel jobs").grid(
            row=2, column=2, sticky="e", padx=(12, 6)
        )
        ttk.Entry(page, textvariable=self.asic_jobs, width=7).grid(
            row=2, column=3, sticky="w"
        )

        ttk.Label(page, text="Start step").grid(
            row=3, column=0, sticky="w", pady=(10, 0)
        )
        ttk.Entry(page, textvariable=self.asic_start_step).grid(
            row=3, column=1, sticky="ew", pady=(10, 0), padx=(0, 12)
        )
        ttk.Label(page, text="End step").grid(
            row=3, column=2, sticky="e", pady=(10, 0), padx=(0, 6)
        )
        ttk.Entry(page, textvariable=self.asic_end_step).grid(
            row=3, column=3, sticky="ew", pady=(10, 0)
        )
        page.columnconfigure(3, weight=1)
        ttk.Label(
            page,
            text="Optional OpenLane step IDs, for example Verilator.Lint or OpenROAD.GeneratePDN.",
            style="Hint.TLabel",
        ).grid(row=4, column=1, columnspan=3, sticky="w", pady=(3, 8))

        ttk.Label(page, text="Extra arguments").grid(
            row=5, column=0, sticky="w", padx=(0, 10)
        )
        ttk.Entry(page, textvariable=self.asic_extra_options).grid(
            row=5, column=1, columnspan=3, sticky="ew"
        )
        ttk.Label(
            page,
            text="Examples: --pdk sky130A or --run-tag experiment_1.",
            style="Hint.TLabel",
        ).grid(row=6, column=1, columnspan=3, sticky="w", pady=(3, 8))

        actions = ttk.Frame(page)
        actions.grid(row=7, column=0, columnspan=4, sticky="ew")
        for column in range(4):
            actions.columnconfigure(column, weight=1)
        self._add_button(
            actions,
            "Run ASIC Flow",
            self._run_asic,
            row=0,
            column=0,
        )
        self._add_button(
            actions,
            "Lint Only",
            self._run_openlane_lint,
            row=0,
            column=1,
        )
        self._add_button(
            actions,
            "Open in KLayout",
            lambda: self._run_openlane_viewer("OpenInKLayout"),
            row=0,
            column=2,
        )
        self._add_button(
            actions,
            "Open in OpenROAD",
            lambda: self._run_openlane_viewer("OpenInOpenROAD"),
            row=0,
            column=3,
        )

    def _build_status_page(self, notebook: ttk.Notebook) -> None:
        page = self._new_page(
            notebook,
            "Status",
            "Project status",
            "Summarize configured flows, latest reports, sources, waveforms, and generated build artifacts.",
        )
        self._add_button(
            page,
            "Refresh Status",
            lambda: self._run_command("status"),
            row=2,
            column=2,
        )

    def _build_doctor_page(self, notebook: ttk.Notebook) -> None:
        page = self._new_page(
            notebook,
            "Doctor",
            "Tool availability",
            "Check the executables required by the selected project's flow.yaml configuration.",
        )
        self._add_button(
            page,
            "Run Doctor",
            lambda: self._run_command("doctor"),
            row=2,
            column=2,
        )

    def _build_clean_page(self, notebook: ttk.Notebook) -> None:
        page = self._new_page(
            notebook,
            "Clean",
            "Generated artifact cleanup",
            "Preview or remove reports, simulation output, synthesis builds, and OpenLane run directories. Maintained source and configuration files are preserved.",
        )
        ttk.Label(page, text="Artifacts to clean").grid(
            row=2, column=0, sticky="nw", padx=(0, 12)
        )
        choices = ttk.Frame(page)
        choices.grid(row=2, column=1, columnspan=2, sticky="ew")
        for column in range(3):
            choices.columnconfigure(column, weight=1)
        for index, category in enumerate(CLEAN_CATEGORIES):
            ttk.Checkbutton(
                choices,
                text=CLEAN_CATEGORY_LABELS[category],
                variable=self.clean_categories[category],
            ).grid(
                row=index // 3,
                column=index % 3,
                sticky="w",
                padx=(0, 14),
                pady=2,
            )

        selection_actions = ttk.Frame(page)
        selection_actions.grid(row=3, column=1, columnspan=2, sticky="w")
        self._add_button(
            selection_actions,
            "Select All",
            lambda: self._set_clean_categories(True),
            row=0,
            column=0,
        )
        self._add_button(
            selection_actions,
            "Select None",
            lambda: self._set_clean_categories(False),
            row=0,
            column=1,
        )

        actions = ttk.Frame(page)
        actions.grid(row=4, column=1, columnspan=2, sticky="ew", pady=(8, 0))
        actions.columnconfigure(0, weight=1)
        actions.columnconfigure(1, weight=1)
        self._add_button(
            actions,
            "Preview Cleanup",
            self._preview_clean,
            row=0,
            column=0,
        )
        self._add_button(
            actions,
            "Clean Selected",
            self._clean_project,
            row=0,
            column=1,
        )

    def _build_output_panel(self, parent: ttk.Frame) -> None:
        output_frame = ttk.LabelFrame(parent, text="Command output", padding=10)
        output_frame.grid(row=4, column=0, sticky="nsew")
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
            output_frame,
            text="Clear Output",
            command=self._clear_output,
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
            parent,
            text=label,
            command=callback,
            style="Command.TButton",
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
        project_name = self.new_project_name.get().strip()
        if not project_name:
            messagebox.showerror(
                "Missing Project Name",
                "Enter a project name before creating a project.",
                parent=self.root,
            )
            return
        self._run_command("init", [project_name])

    def _run_simulation(self) -> None:
        command_arguments = ["--wave"] if self.sim_open_wave.get() else None
        self._run_command("sim", command_arguments)

    def _current_asic_options(self, end_step: str | None = None) -> str:
        return build_asic_tool_options(
            condensed=self.asic_condensed.get(),
            jobs=self.asic_jobs.get(),
            start_step=self.asic_start_step.get(),
            end_step=end_step if end_step is not None else self.asic_end_step.get(),
            extra_options=self.asic_extra_options.get(),
        )

    def _run_asic(self) -> None:
        try:
            options = self._current_asic_options()
        except ValueError as error:
            self._show_option_error(error)
            return
        self._run_command("asic", tool_options=options)

    def _run_openlane_lint(self) -> None:
        try:
            options = self._current_asic_options(end_step="Verilator.Lint")
        except ValueError as error:
            self._show_option_error(error)
            return
        self._run_command("asic", tool_options=options)

    def _run_openlane_viewer(self, flow_name: str) -> None:
        options = shlex.join(["--last-run", "--flow", flow_name])
        self._run_command("asic", tool_options=options)

    def _set_clean_categories(self, selected: bool) -> None:
        for variable in self.clean_categories.values():
            variable.set(selected)

    def _selected_clean_categories(self) -> list[str]:
        return [
            category
            for category in CLEAN_CATEGORIES
            if self.clean_categories[category].get()
        ]

    def _clean_arguments(self, *, dry_run: bool = False) -> list[str] | None:
        try:
            return build_clean_arguments(
                self._selected_clean_categories(),
                dry_run=dry_run,
            )
        except ValueError as error:
            self._show_option_error(error)
            return None

    def _preview_clean(self) -> None:
        arguments = self._clean_arguments(dry_run=True)
        if arguments is not None:
            self._run_command("clean", arguments)

    def _clean_project(self) -> None:
        arguments = self._clean_arguments()
        if arguments is None:
            return
        selected_labels = [
            CLEAN_CATEGORY_LABELS[category]
            for category in self._selected_clean_categories()
        ]
        if messagebox.askyesno(
            "Clean Project",
            "Remove the selected generated artifacts?\n\n"
            + "\n".join(f"• {label}" for label in selected_labels),
            parent=self.root,
        ):
            self._run_command("clean", arguments)

    def _show_option_error(self, error: Exception) -> None:
        messagebox.showerror(
            "Invalid Tool Arguments",
            str(error),
            parent=self.root,
        )

    def _run_command(
        self,
        command: str,
        extra_arguments: list[str] | None = None,
        tool_options: str | None = None,
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

        if tool_options is None:
            variable = self.command_options.get(command)
            tool_options = variable.get() if variable is not None else ""

        try:
            cli_command = build_cli_command(
                command,
                tool_options,
                extra_arguments,
            )
        except ValueError as error:
            self._show_option_error(error)
            return

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
        self,
        cli_command: list[str],
        working_directory: Path,
        command: str,
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
